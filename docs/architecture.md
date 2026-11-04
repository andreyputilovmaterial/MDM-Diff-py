# MDM-Diff-py — architecture

Stable overview. Living working-memory notes (decisions, findings, roadmap) live in
`docs/project-context.md`, which is updated on every agent run and is not linked from
user-facing docs.

## Data flow

Every reader produces the same JSON "report" shape, and every reporter consumes it:

```
[input file] --reader--> [JSON report] --reporter--> [HTML / Excel]
```

- **Readers** live under `src/lib/otherformatsreadpy_*` and `src/lib/mdmreadpy`.
- **MDD reader** — `src/lib/mdmreadpy` (`read_mdd.py`), drives the COM API of
  IBM/Unicom Professional (Windows + Professional required).
- **Diff tool** — `src/diff_engine` (current) / `src/diff_older` (legacy). Reads one or
  two JSON reports and writes a new JSON report. A diff report is itself a valid input, so
  two diffs can be diffed again (diff-on-diff). Internals are documented in
  `docs/diff-engine.md` (duplicated at `src/diff_engine/README.md`), including the
  diff-on-diff `source_*` role relocation and `context`/`change` block splitting.
- **HTML reporter** — `src/lib/mdmreadpy/src/lib/mdmreportpy` (`report_create.py`).
- **Excel reporter** — `src/lib/mdmexcelreportpy`.
- **Translation overlay helper** — `MDM-TranslationOverlayHelper`
  (<https://github.com/andreyputilovmaterial/MDM-TranslationOverlayHelper.git>).
- **Universal dispatcher** — `src/launcher.py` (`--program ...`).
- **Schema generator** — `src/mddtoschema` (MDD → JSON schema; distinct from the
  reader).

For example, the MDD diff workflow is:

```
MDD A --mdmreadpy--> JSON A --\
                               diff --> JSON diff --mdmreportpy--> HTML
MDD B --mdmreadpy--> JSON B --/
```

## Data format — source of truth

The **report JSON format** and the **rich-text content format** are specified once, in
`mdmreportpy`, and are the master definition for the whole toolchain:

- `src/lib/mdmreadpy/src/lib/mdmreportpy/docs/report-json-format.md` — the JSON
  "report" shape.
- `src/lib/mdmreadpy/src/lib/mdmreportpy/docs/rich-text-format.md` — cell / header
  content shapes and `role` semantics.

Every reader (the MDD reader and the `otherformatsreadpy_*` readers), the diff tool
(`src/diff.py` / `src/diff_engine`), and every reporter (`mdmreportpy`,
`mdmexcelreportpy`) defer to those two files. Per-tool docs may describe their own
producer/consumer view, but the two files above are authoritative for the common shape.

## Submodules (`.gitmodules`)

| Path | Purpose | Remote |
| --- | --- | --- |
| `src/lib/mdmreadpy` | MDD → JSON. | <https://github.com/andreyputilovmaterial/MDM-Read-py.git> |
| `src/lib/mdmreadpy/src/lib/mdmreportpy` | JSON → HTML. | <https://github.com/andreyputilovmaterial/MDM-Report-py.git> |
| `src/lib/mdmexcelreportpy` | JSON → Excel. | <https://github.com/andreyputilovmaterial/MDM-ExcelReport-py.git> |
| `src/lib/mddtoschema` | MDD → JSON schema. | <https://github.com/andreyputilovmaterial/MDM-ToSchema-py.git> |
| `src/lib/otherformatsreadpy_*` | Other readers. | — |
| `src_dev_build/lib/pinliner` | Single-file bundling. | <https://github.com/The-city-not-present/pinliner.git> |

## Build & distribution

`build.bat` (Windows) / `build.sh` (macOS/Linux) use the vendored `pinliner` fork to
produce a single-file `dist/mdmtoolsap_bundle.py` with a `--main src.launcher
--main-attr main` entry point (the bundle runs `launcher.main()` when executed), and
copy LICENSE/README into `dist/`. BAT launchers
in `src_bat_scripts/` drive specific workflows; they are copied (and renamed) into
`dist/`, and during that copy the bundle path is rewritten to `mdmtoolsap_bundle.py`
and the launcher python is switched to the venv python (`.venv\Scripts\python.exe`).

`src_dev_build/inline_run_init.py` then turns each launcher into a self-contained,
two-file distribution: it parses the root `requirements.txt` and every
`requirements.txt` under `src/lib/` (each reader's/reporter's own *runtime*
dependencies) into explicit `pip install "pkg1" "pkg2"` rows, regenerates the marked
dependency section of `run_init.bat`/`run_init.sh`, and splices that venv-setup preamble
directly into each launcher (replacing the `CALL "run_init.bat"` line). Build/dev-only
dependencies live in `requirements-dev.txt`, which the helper intentionally does not
scan, so they are never shipped. The result is a `dist/` that ships only the launchers,
the bundle, and LICENSE/README — no `requirements.txt`, `optional_dependencies/`, or
`run_init.*` files. The venv setup creates a local `.venv`; the optional packages are
installed best-effort (a missing optional package only disables the corresponding
reader/reporter).

The build requires the vendored `pinliner` fork (`src_dev_build/lib/pinliner`, a git
submodule with local fixes) — use this copy rather than the upstream package. The only
build-time helpers are `csscompressor` and `rjsmin`, declared in `mdmreportpy`'s
`requirements-dev.txt` (not `requirements.txt`, so they are not inlined into the
distributed launchers); they minify the HTML report's embedded CSS/JS when the template
is built, and the build falls back to un-minified assets (with a one-time warning) when
they are missing.

## Three ways to launch a program

Every part that ships a `launcher.py` (`src/`, `mdmreadpy`, `mdmreportpy`,
`mdmexcelreportpy`, `mddtoschema`) can be started three equivalent ways:

1. **Single-file bundle** (distribution). `pinliner` bundles the tree with a
   `--main src.launcher --main-attr main` entry point. Run it with the venv Python:

   ```
   .venv\Scripts\python.exe mdmtoolsap_bundle.py --program <name> [args]
   ```

2. **Direct module invocation** (development). Run an entry-point module with `-m`:

   ```
   python -m src.diff [args]          # e.g. the diff tool
   python -m src.lib.mdmreadpy.src.read_mdd --mdd file.mdd
   ```

3. **Launcher proxy** (development). Run the universal dispatcher with `-m`:

   ```
   python -m src.launcher --program <name> [args]
   ```

The three root-level BAT examples in `src_bat_scripts/` map one-to-one onto these:
`run_calling_bundle_*.bat` (bundle), `run_individual_scripts.bat` (direct module), and
`run_as_directory.bat` (launcher proxy).
