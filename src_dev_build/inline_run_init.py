"""Build-time helper: inline ``run_init`` (venv setup + explicit pip installs) into
every distributed launcher.

This is a *build tool*, not runtime code. It lives under ``src_dev_build/`` (which
has no ``__init__.py``), so pinliner never bundles it into ``dist/mdmtoolsap_bundle.py``.

Why this exists
---------------

Historically the distributed ``dist/run_*.bat`` launchers did ``CALL run_init.bat``
and shipped a separate ``run_init.bat`` / ``run_init.sh`` plus every ``requirements.txt``
under ``dist/optional_dependencies/``. That forced an end user to carry several files.

This script turns the launchers into two-file distributions:

* ``dist/mdmtoolsap_bundle.py`` — the single-file Python bundle, and
* one ``dist/run_*.bat`` per workflow, self-contained.

The dependency *lists* stay in the repository as the single source of truth — the root
``requirements.txt`` and each reader/reporter's ``requirements.txt`` under ``src/lib/``.
At build time this script parses those lists and turns them into explicit
``pip install "pkg1" "pkg2"`` rows, so no ``requirements.txt`` (and no
``optional_dependencies/``) needs to ship.

``run_init.bat`` / ``run_init.sh`` remain the single source of truth for the venv-setup
logic. They contain a clearly delimited section

    === BEGIN GENERATED DEPENDENCIES ===
    ... (dev behaviour: `pip install -r requirements.txt` + scan of src/lib/) ...
    === END GENERATED DEPENDENCIES ===

which this script regenerates with the explicit package rows before splicing the whole
preamble into each launcher (replacing the ``CALL "run_init.bat"`` /
``source ./run_init.sh`` line).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_LIB = ROOT / "src" / "lib"
DIST = ROOT / "dist"

# Delimiters of the section of run_init.* that this script regenerates. The text
# between them is replaced; the markers themselves are kept in the output.
BEGIN_MARKER = "=== BEGIN GENERATED DEPENDENCIES ==="
END_MARKER = "=== END GENERATED DEPENDENCIES ==="

BAT_BEGIN = "@REM " + BEGIN_MARKER
BAT_END = "@REM " + END_MARKER
SH_BEGIN = "# " + BEGIN_MARKER
SH_END = "# " + END_MARKER

# The line(s) in a distributed launcher that get replaced by the inlined preamble.
BAT_CALL_RE = re.compile(r'CALL "(?:\.\.\\)?run_init\.bat"\n(?:if errorlevel 1 exit /b %errorlevel%\n)?')
SH_CALL_RE = re.compile(r"(?:source|\.) \./run_init\.sh\n")


def parse_requirements(path: Path) -> list[str]:
    """Return the non-comment, non-blank package specs in a ``requirements.txt``.

    Fails early on lines that cannot be inlined into a single ``pip install``
    command (``-r`` includes, editable installs, pip options, ...).
    """
    if not path.exists():
        return []

    specs: list[str] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-"):
            raise ValueError(
                "%s:%d: cannot inline pip option line %r into a single "
                "`pip install` command (only package specs are supported)"
                % (path, lineno, raw)
            )
        specs.append(line)
    return specs


def discover_optional_requirements() -> list[tuple[str, list[str]]]:
    """Return ``(label, specs)`` for each ``requirements.txt`` under ``src/lib/``.

    Labels are the directory path relative to ``src/lib/`` (``/``-separated), so
    ``mdmreadpy`` and the nested ``mdmreadpy/src/lib/mdmreportpy`` stay distinct.
    Sorted for a deterministic output.
    """
    if not SRC_LIB.exists():
        return []

    groups: list[tuple[str, list[str]]] = []
    for path in sorted(SRC_LIB.rglob("requirements.txt")):
        parts = path.relative_to(SRC_LIB).parts
        if any(part in (".git", "dist", "GENERATED", "__pycache__") for part in parts):
            continue
        label = Path(*parts[:-1]).as_posix()
        if label == ".":
            label = "."
        groups.append((label, parse_requirements(path)))
    return groups


def _quoted_specs(specs: list[str]) -> str:
    return " ".join('"%s"' % spec for spec in specs)


def generate_bat_block(root_specs: list[str], groups: list[tuple[str, list[str]]]) -> str:
    lines: list[str] = []
    if root_specs:
        lines.append('"%pythonexecutable%" -m pip install ' + _quoted_specs(root_specs))
    else:
        lines.append("@REM Root dependencies (requirements.txt): none")

    lines.append("@REM Optional per-reader/per-reporter dependencies (best-effort):")
    for label, specs in groups:
        if not specs:
            lines.append("@REM %s: no dependencies" % label)
            continue
        lines.append('"%pythonexecutable%" -m pip install ' + _quoted_specs(specs))
        lines.append(
            "if errorlevel 1 echo WARNING: optional dependencies for %s not installed"
            " - the corresponding reader/reporter will be unavailable" % label
        )
    return "\n".join(lines)


def generate_sh_block(root_specs: list[str], groups: list[tuple[str, list[str]]]) -> str:
    lines: list[str] = []
    if root_specs:
        lines.append('"$pythonexecutable" -m pip install ' + _quoted_specs(root_specs))
    else:
        lines.append("# Root dependencies (requirements.txt): none")

    lines.append("# Optional per-reader/per-reporter dependencies (best-effort):")
    for label, specs in groups:
        if not specs:
            lines.append("# %s: no dependencies" % label)
            continue
        lines.append('if ! "$pythonexecutable" -m pip install ' + _quoted_specs(specs) + "; then")
        lines.append(
            '    echo "WARNING: optional dependencies for %s not installed'
            ' - the corresponding reader/reporter will be unavailable"' % label
        )
        lines.append("fi")
    return "\n".join(lines)


def regenerate_section(template: str, generated_block: str, begin: str, end: str) -> str:
    pattern = re.compile(re.escape(begin) + r"\n.*?" + re.escape(end), re.DOTALL)
    if not pattern.search(template):
        raise ValueError(
            "run_init template is missing the %r ... %r section" % (begin, end)
        )
    replacement = begin + "\n" + generated_block.rstrip("\n") + "\n" + end
    return pattern.sub(lambda _m: replacement, template, count=1)


def read_text(path: Path) -> tuple[str, str]:
    """Return ``(text, newline)`` where text uses ``\\n`` and newline is ``\\n`` or ``\\r\\n``."""
    raw = path.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8-sig").replace("\r\n", "\n")
    return text, newline


def write_text(path: Path, text: str, newline: str) -> None:
    if newline != "\n":
        text = text.replace("\n", newline)
    path.write_bytes(text.encode("utf-8"))


def build_preamble(kind: str, root_specs: list[str], groups: list[tuple[str, list[str]]]) -> str:
    """Return the full inlinable run_init preamble for ``kind`` (``bat``/``sh``)."""
    if kind == "bat":
        template = ROOT / "run_init.bat"
        block = generate_bat_block(root_specs, groups)
        begin, end = BAT_BEGIN, BAT_END
    elif kind == "sh":
        template = ROOT / "run_init.sh"
        block = generate_sh_block(root_specs, groups)
        begin, end = SH_BEGIN, SH_END
    else:
        raise ValueError("unknown kind: %r" % kind)

    text, _ = read_text(template)
    return regenerate_section(text, block, begin, end)


def main() -> int:
    root_specs = parse_requirements(ROOT / "requirements.txt")
    groups = discover_optional_requirements()

    bat_preamble = build_preamble("bat", root_specs, groups)
    sh_preamble = build_preamble("sh", root_specs, groups)

    targets = sorted(DIST.glob("*.bat")) + sorted(DIST.glob("*.sh"))
    if not targets:
        print("No dist launchers found under %s — nothing to inline." % DIST)
        return 0

    for path in targets:
        text, newline = read_text(path)
        if path.suffix == ".bat":
            preamble = bat_preamble
            call_re = BAT_CALL_RE
        else:
            preamble = sh_preamble
            call_re = SH_CALL_RE
        if not call_re.search(text):
            print("SKIP %s: no run_init CALL/source line found" % path.name)
            continue
        text = call_re.sub(lambda _m: preamble + "\n", text, count=1)
        write_text(path, text, newline)
        print("INLINED run_init + explicit pip installs into %s" % path.name)

    return 0


if __name__ == "__main__":
    sys.exit(main())

