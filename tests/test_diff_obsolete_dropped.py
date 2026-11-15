"""Regression test: ``--program diff_obsolete`` must fail with a clear message.

``src/diff_older`` was removed and its support was dropped from tag ``v2.020.001``.
Invoking the obsolete program through the launcher must fail (non-zero exit) with an
error that mentions that tag, instead of silently importing a removed module.
"""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestDiffObsoleteDropped(unittest.TestCase):
    def test_diff_obsolete_fails_with_dropped_support_message(self):
        proc = subprocess.run(
            [sys.executable, "-m", "src.launcher", "--program", "diff_obsolete"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertIn("v2.020.001", proc.stderr)


if __name__ == "__main__":
    unittest.main()
