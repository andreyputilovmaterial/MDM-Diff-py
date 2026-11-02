"""Regression guard: the pinliner build tool must never be bundled into
``dist/mdmtoolsap_bundle.py``.

Pinliner is a *build-time* tool only. It lives in ``src_dev_build/lib/pinliner/``
(next to, not inside, the ``src/`` package it bundles), and it does not scan imports —
it walks the directory tree of the package passed on the command line and inlines every
``.py`` file that sits inside a Python package (a directory containing an
``__init__.py``). Because ``src_dev_build/`` (like ``tests/`` and ``dist/``) has no
``__init__.py``, pinliner's directory walk skips it.

This test reproduces the exact pinliner step from ``build.sh`` / ``build.bat`` and
asserts that none of the inlined module paths mention pinliner or the build tool. It
inspects the bundle's ``inliner_packages`` table (the list of bundled modules) rather
than grepping the raw text, because the embedded loader boilerplate legitimately
contains the word "pinliner".
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "src"  # the package bundled by build.sh / build.bat
PINLINER_SCRIPT = (
    ROOT / "src_dev_build" / "lib" / "pinliner" / "pinliner" / "pinliner.py"
)


def _bundled_module_names(bundle_text):
    """Return the set of module names inlined in a pinliner bundle."""
    marker = "inliner_packages = "
    start = bundle_text.index(marker) + len(marker)
    packages, _ = json.JSONDecoder().raw_decode(bundle_text[start:])
    return set(packages)


@unittest.skipUnless(PINLINER_SCRIPT.exists(), "pinliner submodule not checked out")
class TestBundleExcludesPinliner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "bundle.py"
            subprocess.run(
                [sys.executable, str(PINLINER_SCRIPT), PACKAGE, "-o", str(out)],
                cwd=str(ROOT),
                check=True,
                capture_output=True,
                text=True,
            )
            cls._names = _bundled_module_names(out.read_text(encoding="utf-8"))

    def test_bundle_contains_no_pinliner(self):
        leaked = sorted(n for n in self._names if "pinliner" in n)
        self.assertEqual([], leaked, "pinliner leaked into the bundle: %s" % leaked)

    def test_bundle_contains_no_build_tool_source(self):
        leaked = sorted(n for n in self._names if "src_dev_build" in n)
        self.assertEqual([], leaked, "build-tool source leaked into the bundle: %s" % leaked)


if __name__ == "__main__":
    unittest.main()
