"""Extensive correctness tests for the rich-text diffing in ``src.diff_engine``.

The diff engine maps rich text to a flat character sequence, diffs it, then
projects the result back onto the original blocks (see ``docs/diff-engine.md``).
These tests pin down that projection with a "round-trip" invariant:

* side-by-side: ``as_plain_text(left_result) == as_plain_text(left_input)``
  (and the same for the right side);
* combined: removing the ``added`` segments reproduces the left text, and
  removing the ``removed`` segments reproduces the right text.

A violation is a *silent* corruption — a dropped last piece, a duplicated common
block, spurious whitespace, … — which is exactly the kind of bug these tests
exist to catch. See also GitHub issues #21 (atomic split) and #24 (combined
duplication) and the inline regression tests below.
"""

import itertools
import unittest

from src.diff_engine import diff_functions
from src.diff_engine.common_functions import (
    as_format,
    as_plain_text,
    count_linebreaks,
    detect_format,
    did_change,
    fill_same_number_linebreaks,
    get_segment_payload,
    ErrorCantSplitAtomicPiece,
)
from src.helper_utility.perfmonitor import PerformanceMonitor


def _config():
    # The list-diff path reads config and expects a PerformanceMonitor.
    return {'PerformanceMonitor': PerformanceMonitor}


ADDED = ('added', 'source_added')
REMOVED = ('removed', 'source_removed')


def _text_excluding(value, exclude_roles):
    """Reconstruct the plain text of ``value``, skipping segments whose fine
    role is in ``exclude_roles``.

    This mirrors the rendering in ``as_plain_text`` but honours the per-segment
    ``role`` so we can rebuild the left/right inputs out of a combined diff.
    """
    fmt = detect_format(value)
    if fmt == '(segment)':
        if value.get('role') in exclude_roles:
            return ''
        return _text_excluding(get_segment_payload(value), exclude_roles)
    if fmt == '(list)':
        return ''.join(_text_excluding(item, exclude_roles) for item in value)
    if fmt == '(propertylist)':
        parts = []
        for record in value:
            v = record.get('value')
            role = v.get('role') if isinstance(v, dict) else None
            if role in exclude_roles:
                continue
            parts.append('%s = "%s"' % (
                record['name'],
                _text_excluding(v, exclude_roles).replace('"', '""'),
            ))
        return '[ ' + ', '.join(parts) + ' ]'
    if fmt == '(str)':
        return '%s' % (value,)
    if fmt == '(none)':
        return ''
    return as_plain_text(value)


def _left_text(combined):
    return _text_excluding(combined, ADDED)


def _right_text(combined):
    return _text_excluding(combined, REMOVED)


# ---------------------------------------------------------------------------
# Corpora. FLAT covers the plain rich-text shapes (string / segment / list of
# segments). PROP covers keyed property lists. Each is diffed against itself
# (cross-product) because those pairs are the ones whose rendering is
# preserved; cross-format pairs that change the rendering (e.g. str -> property
# list) and diff-on-diff inputs (role-bearing segments) are covered by the
# dedicated tests further down instead.
# ---------------------------------------------------------------------------

FLAT_CORPUS = [
    '', 'a', 'ab', 'abc', 'Item', 'Item name', 'Item label',
    'hello world', 'hello worlds', '123',
    {'text': 'a'}, {'text': 'ab'},
    {'parts': [{'text': 'a'}, {'text': 'b'}]},
    [{'text': 'a'}],
    [{'text': 'a'}, {'text': 'b'}],
    [{'text': 'a'}, {'text': 'b'}, {'text': 'c'}],
]

PROP_CORPUS = [
    [{'name': 'k', 'value': 'v'}],
    [{'name': 'a', 'value': '1'}, {'name': 'b', 'value': '2'}],
    [{'name': 'a', 'value': '1'}, {'name': 'b', 'value': '2'},
     {'name': 'c', 'value': '3'}],
]


class TestRoundTripSideBySide(unittest.TestCase):
    """The side-by-side result must reproduce each input's plain text exactly."""

    def test_flat_corpus(self):
        for left, right in itertools.product(FLAT_CORPUS, FLAT_CORPUS):
            with self.subTest(left=left, right=right):
                l_res, r_res = diff_functions.finddiff_values_general_formatsidebyside(
                    left, right, _config())
                self.assertEqual(as_plain_text(l_res), as_plain_text(left))
                self.assertEqual(as_plain_text(r_res), as_plain_text(right))

    def test_property_list_corpus(self):
        for left, right in itertools.product(PROP_CORPUS, PROP_CORPUS):
            with self.subTest(left=left, right=right):
                l_res, r_res = diff_functions.finddiff_values_general_formatsidebyside(
                    left, right, _config())
                self.assertEqual(as_plain_text(l_res), as_plain_text(left))
                self.assertEqual(as_plain_text(r_res), as_plain_text(right))


class TestRoundTripCombined(unittest.TestCase):
    """The combined result must reproduce each input after removing the other
    side's segments (catches duplicated common blocks, issue #24)."""

    def test_flat_corpus(self):
        for left, right in itertools.product(FLAT_CORPUS, FLAT_CORPUS):
            with self.subTest(left=left, right=right):
                combined = diff_functions.finddiff_values_general_formatcombined(
                    left, right, _config())
                self.assertEqual(_left_text(combined), as_plain_text(left))
                self.assertEqual(_right_text(combined), as_plain_text(right))

    def test_property_list_corpus(self):
        for left, right in itertools.product(PROP_CORPUS, PROP_CORPUS):
            with self.subTest(left=left, right=right):
                combined = diff_functions.finddiff_values_general_formatcombined(
                    left, right, _config())
                self.assertEqual(_left_text(combined), as_plain_text(left))
                self.assertEqual(_right_text(combined), as_plain_text(right))

class TestStructuralStrings(unittest.TestCase):
    """Exact segmentation of a plain-string diff (the word-level path)."""

    def test_replace(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            'Item name', 'Item label', _config())
        self.assertEqual(left, [
            {'role': 'context', 'text': 'Item '},
            {'role': 'removed', 'text': 'name'},
            {'text': None},
        ])
        self.assertEqual(right, [
            {'role': 'context', 'text': 'Item '},
            {'text': None},
            {'role': 'added', 'text': 'label'},
        ])

    def test_replace_combined(self):
        combined = diff_functions.finddiff_values_general_formatcombined(
            'Item name', 'Item label', _config())
        self.assertEqual(combined, {'parts': [
            {'role': 'context', 'text': 'Item '},
            {'role': 'removed', 'text': 'name'},
            {'role': 'added', 'text': 'label'},
        ]})

    def test_equal_is_context(self):
        combined = diff_functions.finddiff_values_general_formatcombined(
            'same', 'same', _config())
        self.assertEqual(combined, {'role': 'context', 'text': 'same'})
        self.assertFalse(did_change(combined))

    def test_add_only(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            '', 'hello', _config())
        self.assertEqual(left, {'role': 'context', 'text': None})
        self.assertEqual(right, {'role': 'added', 'text': 'hello'})

    def test_remove_only(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            'hello', '', _config())
        self.assertEqual(left, {'role': 'removed', 'text': 'hello'})
        self.assertEqual(right, {'role': 'context', 'text': None})


class TestStructuralLists(unittest.TestCase):
    """The rich-text list path: diff as text, then project back to blocks.

    The "missing last piece" class of bug shows up here as a dropped trailing
    segment; the round-trip tests above already guard it, but the following
    cases make the trailing/leading position explicit.
    """

    def test_change_in_last_element(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            [{'text': 'a'}, {'text': 'b'}], [{'text': 'a'}, {'text': 'c'}], _config())
        self.assertEqual(left, [
            {'role': 'context', 'text': {'text': 'a'}},
            {'role': 'removed', 'text': {'text': 'b'}},
        ])
        self.assertEqual(right, [
            {'role': 'context', 'text': {'text': 'a'}},
            {'role': 'added', 'text': {'text': 'c'}},
        ])

    def test_append_last_element_is_not_dropped(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            [{'text': 'a'}, {'text': 'b'}],
            [{'text': 'a'}, {'text': 'b'}, {'text': 'c'}],
            _config())
        self.assertEqual(as_plain_text(left), 'ab')
        self.assertEqual(as_plain_text(right), 'abc')
        self.assertTrue(did_change(right))

    def test_remove_last_element_is_not_dropped(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            [{'text': 'a'}, {'text': 'b'}, {'text': 'c'}],
            [{'text': 'a'}, {'text': 'b'}],
            _config())
        self.assertEqual(as_plain_text(left), 'abc')
        self.assertEqual(as_plain_text(right), 'ab')
        self.assertTrue(did_change(left))

    def test_change_in_first_element(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            [{'text': 'a'}, {'text': 'b'}], [{'text': 'x'}, {'text': 'b'}], _config())
        self.assertEqual(left, [
            {'role': 'removed', 'text': {'text': 'a'}},
            {'role': 'context', 'text': {'text': 'b'}},
        ])
        self.assertEqual(right, [
            {'role': 'added', 'text': {'text': 'x'}},
            {'role': 'context', 'text': {'text': 'b'}},
        ])

    def test_whole_list_added(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            [], [{'text': 'a'}, {'text': 'b'}], _config())
        self.assertEqual(left, [])
        self.assertEqual(right, [
            {'role': 'added', 'text': {'text': 'a'}},
            {'role': 'added', 'text': {'text': 'b'}},
        ])

    def test_whole_list_removed(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            [{'text': 'a'}, {'text': 'b'}], [], _config())
        self.assertEqual(left, [
            {'role': 'removed', 'text': {'text': 'a'}},
            {'role': 'removed', 'text': {'text': 'b'}},
        ])
        self.assertEqual(right, [])

class TestStructuralPropertyLists(unittest.TestCase):
    """Keyed collections are compared structurally, by ``name`` (not as text)."""

    def test_value_change(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            [{'name': 'a', 'value': '1'}, {'name': 'b', 'value': '2'}],
            [{'name': 'a', 'value': '1'}, {'name': 'b', 'value': '3'}],
            _config())
        # 'a' unchanged -> context; 'b' changed -> removed on left, added on right
        self.assertEqual(left, [
            {'name': 'a', 'value': {'role': 'context', 'text': '1'}},
            {'name': 'b', 'value': [
                {'role': 'context', 'text': ''},
                {'role': 'removed', 'text': '2'},
                {'text': None},
            ]},
        ])
        self.assertEqual(right, [
            {'name': 'a', 'value': {'role': 'context', 'text': '1'}},
            {'name': 'b', 'value': [
                {'role': 'context', 'text': ''},
                {'text': None},
                {'role': 'added', 'text': '3'},
            ]},
        ])

    def test_add_property(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            [{'name': 'a', 'value': '1'}],
            [{'name': 'a', 'value': '1'}, {'name': 'b', 'value': '2'}],
            _config())
        self.assertEqual(left, [{'name': 'a', 'value': {'role': 'context', 'text': '1'}}])
        self.assertEqual(right, [
            {'name': 'a', 'value': {'role': 'context', 'text': '1'}},
            {'name': 'b', 'value': {'role': 'added', 'text': '2'}},
        ])

    def test_remove_property(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            [{'name': 'a', 'value': '1'}, {'name': 'b', 'value': '2'}],
            [{'name': 'a', 'value': '1'}],
            _config())
        self.assertEqual(left, [
            {'name': 'a', 'value': {'role': 'context', 'text': '1'}},
            {'name': 'b', 'value': {'role': 'removed', 'text': '2'}},
        ])
        self.assertEqual(right, [{'name': 'a', 'value': {'role': 'context', 'text': '1'}}])

    def test_did_change(self):
        equal = diff_functions.finddiff_values_general_formatcombined(
            [{'name': 'a', 'value': '1'}], [{'name': 'a', 'value': '1'}], _config())
        self.assertFalse(did_change(equal))
        changed = diff_functions.finddiff_values_general_formatcombined(
            [{'name': 'a', 'value': '1'}], [{'name': 'a', 'value': '2'}], _config())
        self.assertTrue(did_change(changed))


class TestStructuralSegments(unittest.TestCase):
    """A single ``(segment)`` diffing (payload + role handling)."""

    def test_text_segment_payload_diff(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            {'text': 'ab'}, {'text': 'ac'}, _config())
        self.assertEqual(as_plain_text(left), 'ab')
        self.assertEqual(as_plain_text(right), 'ac')
        self.assertTrue(did_change(left))

    def test_parts_segment_payload_diff(self):
        combined = diff_functions.finddiff_values_general_formatcombined(
            {'parts': [{'text': 'a'}, {'text': 'b'}]},
            {'parts': [{'text': 'a'}, {'text': 'c'}]},
            _config())
        self.assertEqual(_left_text(combined), 'ab')
        self.assertEqual(_right_text(combined), 'ac')

    def test_identical_segments_are_context(self):
        combined = diff_functions.finddiff_values_general_formatcombined(
            {'parts': [{'text': 'a'}]}, {'parts': [{'text': 'a'}]}, _config())
        self.assertFalse(did_change(combined))

class TestAtomicSplit(unittest.TestCase):
    """Issue #21: a character diff crossing an atomic (dict/property-list)
    piece cannot be projected back, and raises ``ErrorCantSplitAtomicPiece``
    instead of silently corrupting the result. A change that does *not* cross
    the atomic piece must still diff cleanly."""

    def test_raises_when_change_crosses_dict(self):
        with self.assertRaises(ErrorCantSplitAtomicPiece):
            diff_functions.finddiff_values_general_formatsidebyside(
                [{'text': 'before '}, {'name': 'k', 'value': 'v'}],
                [{'text': 'before '}, {'name': 'k', 'value': 'w'}],
                _config())

    def test_raises_when_change_crosses_bare_dict(self):
        with self.assertRaises(ErrorCantSplitAtomicPiece):
            diff_functions.finddiff_values_general_formatsidebyside(
                [{'text': 'before '}, {'k': 'v'}, {'text': ' after'}],
                [{'text': 'before '}, {'k': 'w'}, {'text': ' after'}],
                _config())

    def test_whole_atomic_add_does_not_raise(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            [{'text': 'a'}], [{'text': 'a'}, {'name': 'k', 'value': 'v'}], _config())
        self.assertEqual(left, [{'role': 'context', 'text': {'text': 'a'}}])
        self.assertEqual(right, [
            {'role': 'context', 'text': {'text': 'a'}},
            {'role': 'added', 'text': {'name': 'k', 'value': 'v'}},
        ])

    def test_whole_atomic_remove_does_not_raise(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            [{'text': 'a'}, {'name': 'k', 'value': 'v'}], [{'text': 'a'}], _config())
        self.assertEqual(left, [
            {'role': 'context', 'text': {'text': 'a'}},
            {'role': 'removed', 'text': {'name': 'k', 'value': 'v'}},
        ])
        self.assertEqual(right, [{'role': 'context', 'text': {'text': 'a'}}])

    def test_unchanged_atomic_does_not_raise(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            [{'text': 'a'}, {'name': 'k', 'value': 'v'}],
            [{'text': 'a'}, {'name': 'k', 'value': 'v'}],
            _config())
        self.assertEqual(left, [
            {'role': 'context', 'text': {'text': 'a'}},
            {'role': 'context', 'text': {'name': 'k', 'value': 'v'}},
        ])
        self.assertEqual(right, [
            {'role': 'context', 'text': {'text': 'a'}},
            {'role': 'context', 'text': {'name': 'k', 'value': 'v'}},
        ])


class TestAsFormatMultiStep(unittest.TestCase):
    """Regression: ``as_format`` used to only convert one step, so a common
    format reachable only via an intermediate step crashed. It now path-finds."""

    def test_dict_to_str(self):
        self.assertEqual(
            as_format({'k': 'v'}, '(dict)', '(str)'),
            "{'k': 'v'}",
        )

    def test_dict_to_list(self):
        self.assertEqual(
            as_format({'k': 'v'}, '(dict)', '(list)'),
            ["{'k': 'v'}"],
        )


class TestMixedFormatNoCrash(unittest.TestCase):
    """``(dict) -> (str)`` used to crash with a missing-converter exception."""

    def test_str_vs_dict(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            'a', {'k': 'v'}, _config())
        self.assertEqual(as_plain_text(left), 'a')
        self.assertEqual(as_plain_text(right), "{'k': 'v'}")

class TestAsPlainTextPropertyListValue(unittest.TestCase):
    """Regression: a property-list value that is itself rich text must render
    as text (not as the Python repr of the segment dict)."""

    def test_rich_value_renders_as_text(self):
        self.assertEqual(
            as_plain_text([{'name': 'a', 'value': {'role': 'added', 'text': '1'}}]),
            '[ a = "1" ]',
        )

    def test_plain_value_unchanged(self):
        self.assertEqual(
            as_plain_text([{'name': 'a', 'value': '1'}]),
            '[ a = "1" ]',
        )


class TestKnownMultiLineIssues(unittest.TestCase):
    """Known correctness gap: when two multi-line texts differ in their number
    of lines, the linebreak padding can introduce spurious spaces. Documented
    here so it is tracked and fixed, rather than silently ignored."""

    @unittest.expectedFailure
    def test_removed_line_does_not_add_space(self):
        left, _ = diff_functions.finddiff_values_general_formatsidebyside(
            'a\nb\nc', 'a\nb', _config())
        # Currently produces 'a\nb \nc' (note the spurious space after 'b').
        self.assertEqual(as_plain_text(left), 'a\nb\nc')

    @unittest.expectedFailure
    def test_inserted_line_does_not_add_space(self):
        _, right = diff_functions.finddiff_values_general_formatsidebyside(
            'a\nb', 'a\nb\nc', _config())
        self.assertEqual(as_plain_text(right), 'a\nb\nc')


class TestCountLinebreaks(unittest.TestCase):
    """``count_linebreaks`` reports the number of *visual* lines: a trailing
    newline is an (empty) line of its own, so ``'a\\n'`` is 2 lines."""

    def test_semantics(self):
        self.assertEqual(count_linebreaks('a'), 1)
        self.assertEqual(count_linebreaks('a\n'), 2)
        self.assertEqual(count_linebreaks('a\nb'), 2)
        self.assertEqual(count_linebreaks('a\nb\n'), 3)
        self.assertEqual(count_linebreaks(''), 1)

    def test_rich_text(self):
        self.assertEqual(count_linebreaks({'text': 'a\nb'}), 2)
        # segments concatenate; newlines inside them contribute to the count
        self.assertEqual(count_linebreaks([{'text': 'a\nb'}, {'text': '\nc'}]), 3)


class TestFillSameNumberLinebreaks(unittest.TestCase):
    """``fill_same_number_linebreaks`` pads the shorter side with trailing
    newline characters (rendered as empty lines) so both sides line up."""

    def test_left_shorter_gets_padded(self):
        left, right = fill_same_number_linebreaks('a\nb', 'a\nb\nc')
        self.assertEqual(left, ['a\nb', {'role': 'context', 'text': '\n'}])
        self.assertEqual(right, 'a\nb\nc')
        self.assertEqual(count_linebreaks(left), 3)
        self.assertEqual(count_linebreaks(right), 3)

    def test_right_shorter_gets_padded(self):
        left, right = fill_same_number_linebreaks('a\nb\nc', 'a\nb')
        self.assertEqual(left, 'a\nb\nc')
        self.assertEqual(right, ['a\nb', {'role': 'context', 'text': '\n'}])
        self.assertEqual(count_linebreaks(left), 3)
        self.assertEqual(count_linebreaks(right), 3)

    def test_single_line_to_multiline(self):
        left, right = fill_same_number_linebreaks('a', 'a\nb')
        self.assertEqual(count_linebreaks(left), 2)
        self.assertEqual(count_linebreaks(right), 2)

    def test_equal_is_unchanged(self):
        left, right = fill_same_number_linebreaks('a\nb', 'a\nb')
        self.assertEqual(left, 'a\nb')
        self.assertEqual(right, 'a\nb')


# Multi-line rich-text shapes whose rendering is preserved (no plain dicts, no
# role-bearing segments — those are covered by the dedicated tests above).
MULTILINE_CORPUS = [
    'a\nb', 'a\nb\nc', 'a\nb\nc\nd', 'line one\nline two', 'line one\nline three',
    'x\ny\nz', 'x\ny', 'a\n', '\n',
    {'text': 'a\nb'}, {'text': 'a\nb\nc'},
    {'parts': [{'text': 'a\nb'}, {'text': 'c'}]},
    [{'text': 'a\nb'}, {'text': 'c'}],
    [{'text': 'a\nb\nc'}], [{'text': 'a\nb'}],
]


class TestSideBySideLineAlignment(unittest.TestCase):
    """Side-by-side results must occupy the same number of lines so they can be
    rendered in lockstep; the shorter side is padded with trailing empty lines."""

    def test_line_counts_match(self):
        for left, right in itertools.product(MULTILINE_CORPUS, MULTILINE_CORPUS):
            with self.subTest(left=left, right=right):
                l_res, r_res = diff_functions.finddiff_values_general_formatsidebyside(
                    left, right, _config())
                self.assertEqual(count_linebreaks(l_res), count_linebreaks(r_res))

    def test_empty_side_is_padded_to_match(self):
        l_res, r_res = diff_functions.finddiff_values_general_formatsidebyside(
            '', 'a\nb\nc', _config())
        self.assertEqual(count_linebreaks(l_res), 3)
        self.assertEqual(count_linebreaks(r_res), 3)

    def test_empty_side_padded_other_direction(self):
        l_res, r_res = diff_functions.finddiff_values_general_formatsidebyside(
            'a\nb\nc', '', _config())
        self.assertEqual(count_linebreaks(l_res), 3)
        self.assertEqual(count_linebreaks(r_res), 3)


class TestKnownPropertyListEmptyValueIssue(unittest.TestCase):
    """A property list whose every value is empty is treated as ``(none)`` by
    ``is_empty``, so diffing ``[{'name': 'k', 'value': ''}]`` against a non-empty
    value loses the key and can produce mismatched line counts. Documented as a
    known issue until ``is_empty`` semantics for property lists are revisited."""

    @unittest.expectedFailure
    def test_empty_valued_property_is_not_lost(self):
        l_res, r_res = diff_functions.finddiff_values_general_formatsidebyside(
            [{'name': 'k', 'value': ''}], [{'name': 'k', 'value': 'a\nb'}], _config())
        # Currently the left side collapses to [] and line counts mismatch (1 vs 2).
        self.assertEqual(as_plain_text(l_res), '[ k = "" ]')
        self.assertEqual(count_linebreaks(l_res), count_linebreaks(r_res))


if __name__ == '__main__':
    unittest.main()
