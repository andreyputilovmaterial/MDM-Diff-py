"""Tests for rich-text ``column_headers`` support in the diff tool.

The diff tool must pass header values through unchanged (rather than flattening
them with f-strings) and append the `` (Left file)`` / `` (Right file)`` suffix
as a separate part, so the HTML and Excel reporters keep rendering them as rich
text. These tests exercise the two building blocks directly; the diff engine is
importable without the generated ``GENERATED/`` version module.
"""

import unittest

from src.diff_engine import diff_functions
from src.diff_engine.common_functions import did_change, with_appended_part
from src.helper_utility.perfmonitor import PerformanceMonitor


def _config():
    # Only the list-diff path reads config; it expects a PerformanceMonitor.
    return {'PerformanceMonitor': PerformanceMonitor}


class TestWithAppendedPart(unittest.TestCase):
    def test_plain_string(self):
        self.assertEqual(
            with_appended_part('Item name', {'text': ' (Left file)'}),
            {'parts': [{'text': 'Item name'}, {'text': ' (Left file)'}]},
        )

    def test_segment_text(self):
        self.assertEqual(
            with_appended_part({'role': 'context', 'text': 'Item name'}, {'text': ' (Left file)'}),
            {'parts': [{'role': 'context', 'text': 'Item name'}, {'text': ' (Left file)'}]},
        )

    def test_segment_parts(self):
        value = {'parts': [{'role': 'context', 'text': 'A'}, {'role': 'added', 'text': 'B'}]}
        self.assertEqual(
            with_appended_part(value, {'text': ' (Left file)'}),
            {'parts': [
                {'role': 'context', 'text': 'A'},
                {'role': 'added', 'text': 'B'},
                {'text': ' (Left file)'},
            ]},
        )

    def test_list_of_segments(self):
        value = [{'role': 'context', 'text': 'A'}, {'role': 'removed', 'text': 'B'}]
        self.assertEqual(
            with_appended_part(value, {'text': ' (Left file)'}),
            {'parts': [
                {'role': 'context', 'text': 'A'},
                {'role': 'removed', 'text': 'B'},
                {'text': ' (Left file)'},
            ]},
        )

    def test_none(self):
        self.assertEqual(
            with_appended_part(None, {'text': ' (Left file)'}),
            {'parts': [{'text': ' (Left file)'}]},
        )


class TestColumnHeaderDiffing(unittest.TestCase):
    def test_equal_headers_are_context_with_suffix(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside('Item name', 'Item name', _config())
        self.assertEqual(left, {'role': 'context', 'text': 'Item name'})
        self.assertEqual(right, {'role': 'context', 'text': 'Item name'})
        self.assertEqual(
            with_appended_part(left, {'text': ' (Left file)'}),
            {'parts': [{'role': 'context', 'text': 'Item name'}, {'text': ' (Left file)'}]},
        )

    def test_differing_headers_produce_added_and_removed_parts(self):
        left, right = diff_functions.finddiff_values_general_formatsidebyside('Item name', 'Item label', _config())
        combined = diff_functions.finddiff_values_general_formatcombined('Item name', 'Item label', _config())
        self.assertTrue(did_change(left))
        self.assertTrue(did_change(right))
        self.assertTrue(did_change(combined))
        # the suffix is appended as a separate, unhighlighted part
        left_with_suffix = with_appended_part(left, {'text': ' (Left file)'})
        self.assertEqual(left_with_suffix['parts'][-1], {'text': ' (Left file)'})

    def test_rich_text_header_is_preserved(self):
        # right header is rich text; the left side is a plain string
        left, right = diff_functions.finddiff_values_general_formatsidebyside(
            'Item',
            [{'text': 'Item'}, {'text': ' name', 'role': 'added'}],
            _config(),
        )
        self.assertTrue(did_change(right))


if __name__ == '__main__':
    unittest.main()
