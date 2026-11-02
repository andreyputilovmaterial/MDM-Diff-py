"""Smoke test: ``src/launcher.py --program done`` must print ``done`` in green.

The ``done`` program is intentionally dependency-free: it must run in a freshly
cloned repository, before any build step (so ``src/GENERATED/`` does not exist)
or optional third-party packages are installed. Printing the message proves the
launcher module loaded and routed a program successfully.
"""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "src" / "launcher.py"

GREEN = "\033[32m"
RESET = "\033[0m"


class TestDoneProgram(unittest.TestCase):
    def test_done_program_prints_green_done(self):
        proc = subprocess.run(
            [sys.executable, str(LAUNCHER), "--program", "done"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertIn(f"{GREEN}done{RESET}", proc.stdout)


if __name__ == "__main__":
    unittest.main()
