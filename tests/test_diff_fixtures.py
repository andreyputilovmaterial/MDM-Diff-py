"""End-to-end tests of the diff tool against the committed example fixtures.

``tests/fixtures/`` holds real inputs (MDD reader outputs) and the diff tool's own
outputs (including a diff-on-diff). These tests re-run the diffs and check the results
match the committed outputs structurally.

Volatile fields — timestamps, source paths, script versions, and (for the diff-on-diff)
the fine-grained rich-text *content*, which evolves as the engine is fixed — are
deliberately not compared byte-for-byte. The stable contract (columns, flags, section
names, change flags, row statistics, and the plain diffs' full content) is pinned.
"""

import json
import unittest
from pathlib import Path

from src import diff as diff_mod
from src.helper_utility.perfmonitor import PerformanceMonitor

FIXTURES = Path(__file__).resolve().parent / 'fixtures'

READER_INPUTS = [
    'a1_v1.mdd.json',
    'a1_v2.mdd.json',
    'b1_today.mdd.json',
    'b1_tomorrow.mdd.json',
]

# (left, right, diff format, committed output) — plain diffs reproduce exactly.
PLAIN_DIFFS = [
    ('a1_v1.mdd.json', 'a1_v2.mdd.json', 'combined', 'report.diff.a1_-v1-v2-.mdd.json'),
    ('b1_today.mdd.json', 'b1_tomorrow.mdd.json', 'combined', 'report.diff.b1_-today-tomorrow-.mdd.json'),
]

DIFF_ON_DIFF = (
    'report.diff.a1_-v1-v2-.mdd.json',
    'report.diff.b1_-today-tomorrow-.mdd.json',
    'sidebyside',
    'report.diff.report.diff.-a1_-b1_---v1-today---v2-tomorrow--.mdd.json',
)


def _load(name):
    with (FIXTURES / name).open(encoding='utf-8') as f:
        return json.load(f)


def _run(left_name, right_name, fmt):
    config = {
        'format': fmt,
        'inp_filename_left': left_name,
        'inp_filename_right': right_name,
        'script_version': 'test',
        'PerformanceMonitor': PerformanceMonitor,
    }
    return diff_mod.find_diff(_load(left_name), _load(right_name), config)


class TestReaderInputs(unittest.TestCase):
    def test_every_reader_input_is_a_valid_mdd_report(self):
        for name in READER_INPUTS:
            with self.subTest(name=name):
                report = _load(name)
                self.assertEqual(report.get('report_type'), 'MDD')
                self.assertIn('columns', report['report_scheme'])
                self.assertTrue(report['sections'])


class TestPlainDiffs(unittest.TestCase):
    def test_plain_diffs_reproduce_committed_output(self):
        for left, right, fmt, out in PLAIN_DIFFS:
            with self.subTest(out=out):
                result = _run(left, right, fmt)
                committed = _load(out)
                self.assertEqual(result['report_type'], 'diff')
                self.assertEqual(
                    result['report_scheme']['columns'],
                    committed['report_scheme']['columns'],
                )
                self.assertEqual(
                    result['report_scheme']['flags'],
                    committed['report_scheme']['flags'],
                )
                self.assertEqual(result['sections'], committed['sections'])


class TestDiffOnDiff(unittest.TestCase):
    def test_diff_on_diff_reproduces_stable_structure(self):
        left, right, fmt, out = DIFF_ON_DIFF
        result = _run(left, right, fmt)
        committed = _load(out)
        self.assertEqual(result['report_type'], 'diff')
        self.assertEqual(
            result['report_scheme']['columns'],
            committed['report_scheme']['columns'],
        )
        self.assertEqual(
            result['report_scheme']['flags'],
            committed['report_scheme']['flags'],
        )
        # The rich-text content of a diff-on-diff legitimately changes as the engine's
        # nested-role handling is fixed, so only the stable structure is pinned here.
        self.assertEqual(
            [s['name'] for s in result['sections']],
            [s['name'] for s in committed['sections']],
        )
        self.assertEqual(
            [s['changed'] for s in result['sections']],
            [s['changed'] for s in committed['sections']],
        )
        self.assertEqual(
            [s['statistics'] for s in result['sections']],
            [s['statistics'] for s in committed['sections']],
        )


if __name__ == '__main__':
    unittest.main()
