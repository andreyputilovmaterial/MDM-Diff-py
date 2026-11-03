"""Tests for the build-time helper ``src_dev_build/inline_run_init.py``.

The helper turns the per-reader/per-reporter ``requirements.txt`` files (plus the
root one) into explicit ``pip install "pkg1" "pkg2"`` rows and splices the venv-setup
preamble into each distributed launcher, so ``dist/`` ships as a single BAT + the
Python bundle (no ``requirements.txt`` / ``run_init.*`` / ``optional_dependencies/``).
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "src_dev_build" / "inline_run_init.py"

_spec = importlib.util.spec_from_file_location("inline_run_init", HELPER_PATH)
inline_run_init = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(inline_run_init)


class TestParseRequirements(unittest.TestCase):
    def test_parses_specs_and_skips_comments_and_blanks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "requirements.txt"
            path.write_text(
                "# comment\n\npandas\nnumpy\n   # indented comment\nopenpyxl\n",
                encoding="utf-8",
            )
            self.assertEqual(
                inline_run_init.parse_requirements(path),
                ["pandas", "numpy", "openpyxl"],
            )

    def test_rejects_pip_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "requirements.txt"
            path.write_text("-r other.txt\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                inline_run_init.parse_requirements(path)

    def test_missing_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                inline_run_init.parse_requirements(Path(tmp) / "missing.txt"), []
            )


class TestGenerateBlocks(unittest.TestCase):
    def test_bat_block_quotes_extras_and_groups(self):
        groups = [
            ("mddtoschema", ["pydantic", "pywin32"]),
            ("markitdown", ["markitdown[pdf,xlsx,docx,pptx,xls,outlook]"]),
            ("emptyreader", []),
        ]
        block = inline_run_init.generate_bat_block([], groups)
        self.assertIn('"markitdown[pdf,xlsx,docx,pptx,xls,outlook]"', block)
        self.assertIn('"%pythonexecutable%" -m pip install "pydantic" "pywin32"', block)
        self.assertIn(
            "if errorlevel 1 echo WARNING: optional dependencies for mddtoschema", block
        )
        self.assertIn("@REM emptyreader: no dependencies", block)
        self.assertNotIn("install -r", block)

    def test_sh_block_uses_if_not_for_best_effort(self):
        block = inline_run_init.generate_sh_block([], [("spss", ["pyreadstat"])])
        self.assertIn('if ! "$pythonexecutable" -m pip install "pyreadstat"; then', block)
        self.assertIn('echo "WARNING: optional dependencies for spss', block)
        self.assertIn("fi", block)

    def test_root_specs_become_plain_install(self):
        block = inline_run_init.generate_bat_block(["requests"], [])
        self.assertIn('"%pythonexecutable%" -m pip install "requests"', block)
        self.assertNotIn("WARNING", block)


class TestRegenerateSection(unittest.TestCase):
    def test_replaces_section_and_keeps_markers(self):
        template = (
            "@REM " + inline_run_init.BEGIN_MARKER + "\nold\n"
            + "@REM " + inline_run_init.END_MARKER + "\nendlocal\n"
        )
        out = inline_run_init.regenerate_section(
            template, "new", inline_run_init.BAT_BEGIN, inline_run_init.BAT_END
        )
        self.assertIn(inline_run_init.BAT_BEGIN, out)
        self.assertIn("new", out)
        self.assertNotIn("old", out)
        self.assertIn("endlocal", out)

    def test_missing_markers_raises(self):
        with self.assertRaises(ValueError):
            inline_run_init.regenerate_section(
                "no markers here", "new", inline_run_init.BAT_BEGIN, inline_run_init.BAT_END
            )


class TestInlineRegexes(unittest.TestCase):
    def test_bat_call_re_matches_both_forms(self):
        self.assertIsNotNone(inline_run_init.BAT_CALL_RE.search('CALL "..\\run_init.bat"\n'))
        self.assertIsNotNone(inline_run_init.BAT_CALL_RE.search('CALL "run_init.bat"\n'))

    def test_sh_call_re(self):
        self.assertIsNotNone(inline_run_init.SH_CALL_RE.search("source ./run_init.sh\n"))
        self.assertIsNotNone(inline_run_init.SH_CALL_RE.search(". ./run_init.sh\n"))


class TestRealTemplates(unittest.TestCase):
    """Guard that the checked-in run_init templates still carry the markers and that
    regeneration strips the dev-time ``-r requirements.txt`` / ``find src/lib`` loop."""

    def test_bat_preamble_has_no_dev_install_loop(self):
        preamble = inline_run_init.build_preamble("bat", [], [("x", ["pkg"])])
        self.assertNotIn("-r requirements.txt", preamble)
        self.assertNotIn("for /r", preamble)
        self.assertIn('pip install "pkg"', preamble)
        self.assertIn(inline_run_init.BAT_BEGIN, preamble)

    def test_sh_preamble_has_no_dev_install_loop(self):
        preamble = inline_run_init.build_preamble("sh", [], [("x", ["pkg"])])
        self.assertNotIn("-r requirements.txt", preamble)
        self.assertNotIn("find src/lib", preamble)
        self.assertIn('pip install "pkg"', preamble)
        self.assertIn(inline_run_init.SH_BEGIN, preamble)


if __name__ == "__main__":
    unittest.main()
