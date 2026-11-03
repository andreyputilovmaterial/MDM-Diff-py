"""Tests for the hierarchical row-name grouping guard in ``src.diff.py``.

A group whose children are present but whose parent row is missing is malformed.
When hierarchical grouping is enabled the diff must raise
``MDMDiffWrappersGroupingMissingParentException``; when
``config_use_hierarchical_name_structure`` is disabled the same input is diffed
flat and must not raise.
"""

import unittest

from src import diff as diff_mod
from src.diff_engine.diff_functions import MDMDiffWrappersGroupingMissingParentException
from src.helper_utility.perfmonitor import PerformanceMonitor


def _report(rows):
    return {
        'report_type': 'MDD',
        'report_scheme': {
            'columns': ['name', 'label'],
            'column_headers': {'name': 'Item name', 'label': 'Label'},
            'flags': ['data-type:mdd'],
        },
        'sections': [
            {
                'name': 'fields',
                'content': [{'name': name, 'label': f'{name} label'} for name in rows],
            },
        ],
    }


def _config(use_hierarchical):
    return {
        'format': 'combined',
        'inp_filename_left': 'left.mdd.json',
        'inp_filename_right': 'right.mdd.json',
        'script_version': 'test',
        'PerformanceMonitor': PerformanceMonitor,
        'config_use_hierarchical_name_structure': use_hierarchical,
    }


class TestGroupingMissingParentGuard(unittest.TestCase):
    # ``g.a`` / ``g.b`` exist on the left, but their parent row ``g`` is missing
    # on the left (and present on the right), so hierarchical grouping cannot
    # find the parent element on the left.
    LEFT = ['', 'g.a', 'g.b']
    RIGHT = ['', 'g', 'g.a', 'g.b']

    def test_hierarchical_grouping_raises_on_missing_parent(self):
        with self.assertRaises(MDMDiffWrappersGroupingMissingParentException):
            diff_mod.find_diff(_report(self.LEFT), _report(self.RIGHT), _config(True))

    def test_non_grouping_mode_does_not_raise(self):
        result = diff_mod.find_diff(_report(self.LEFT), _report(self.RIGHT), _config(False))
        self.assertEqual(result['report_type'], 'diff')
        self.assertTrue(result['sections'])


if __name__ == '__main__':
    unittest.main()
