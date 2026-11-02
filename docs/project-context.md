# Project Context — MDM-Diff-py

> Last updated: 2026-11-03
> (2026-11-03) Launcher smoke test: added a dependency-free ``--program done`` (prints
> ``done`` in green) to ``src/launcher.py`` plus ``tests/test_done_program.py``. To let
> ``done`` load before any build step (no ``GENERATED/``) or optional deps, the launcher
> now imports every entry-point module lazily via ``_import_module`` and the version
> string via ``_import_version`` (falls back to ``unknown``). Also trimmed
> ``helper_make_diff_output_filename.py``'s three-way starter import to a two-way
> flat/relative form (it's a top-level helper imported flat by directly-run starters, so
> a plain relative import would break ``python src/diff.py``). Same ``done`` program +
> test added to the mdmreadpy/mdmreportpy/mdmexcelreportpy/mddtoschema submodules.
> `build.sh`/`build.bat` now finish with `python dist/mdmtoolsap_bundle.py --program done`
> to smoke-test the built bundle (prints green `done`, fails the build on error).
> (2026-11-03) Removed all traces of the deprecated `<<ADDED>>` / `<<REMOVED>>` /
> `<<ENDADDED>>` / `<<ENDREMOVED>>` / `<<DATE:...>>` / `<<KEYWORD>>` text markers.
> `mdmreportpy`'s `html_sanitize_text` no longer rewrites markers into diff `<span>`s or
> raises on them (it just HTML-escapes them as plain text), `diff_add_classes` no longer
> detects the old string markers, and `diff_engine` dropped its commented-out marker
> check. Diff highlighting now relies purely on the structural rich-text `role` format.
> `src/diff_older/` is left frozen as a historical capture (see
> `.clinerules/05-diff-older-frozen.md`). Closes GitHub issue #13.
> (2026-11-03) Standardized the `.gitignore` test-directory rule across root + all
> submodules: the old broad `[Tt]est*` pattern (which hid any `test_*`/`tests/` folder)
> was replaced with the explicit `tests-real-sensitive-data/` ignore, so regular `tests/`
> and `test_*` folders are tracked. Fixed in root, `mdmreadpy`, `mddtoschema`,
> `mdmreportpy`, `diff-lib`, `MDM-Syntax-Parser-py` (`mdmexcelreportpy` already had it in
> `bac1bec`); stale comments updated to match. Closes GitHub issue #29.
> (2026-11-03) GitHub issue triage: closed #4 (argparse params now handled in
> `src/launcher.py` and passed down to each entry point), #17 (errors printed red in all
> active programs), #33 (`build.sh`/`build.bat` copy LICENSE into `dist/`), and
> `MDM-ExcelReport-py` #1 (Excel reporter handles rich-text `role`). Added a status
> comment on #5 (markitdown/pinliner warnings resolved; `= open()` → `with open()` cleanup
> remains).
> (2026-11-02) Added `.clinerules/09-github-issues.md` (root + all 6
> `andreyputilovmaterial/*` submodules): when asked to commit/push, the agent derives the
> repo from `git remote get-url origin` and fetches open issues from the public GitHub REST
> API (`GET /repos/{owner}/{repo}/issues?state=open`, no token needed — repo and submodules
> are public). It matches issue titles/bodies against the pending diff; a strong match gets
> an automatic `Closes #N` / `Fixes #N` / `Resolves #N` reference in the commit message, a
> weak match is confirmed with the user first. Fallback on rate-limit/private: ask the user
> or use a `GH_TOKEN`. Also listed the previously-missing 08/09/11 rules in §5.

> (2026-11-02) Regression guard: pinliner is a build-time-only tool and must never be
> inlined into `dist/mdmtoolsap_bundle.py`. Added
> `tests/test_bundle_excludes_pinliner.py` (root) plus the same test in the `mdmreadpy`
> and `mdmreportpy` submodules. The test runs the exact `pinliner ... src` step and
> asserts the bundle's `inliner_packages` table contains no module named `*pinliner*` or
> `*src_dev_build*`. Finding: pinliner does **not** scan imports — it walks the package
> directory and inlines every `.py` file inside a Python package (a dir with an
> `__init__.py`); `src_dev_build/` (like `tests/`/`dist/`) is skipped only because it has
> no `__init__.py`, so the exclusion is implicit and fragile — the test guards against a
> future `__init__.py` being added there.

> (2026-11-02) Expanded `.clinerules/00-non-interactive-terminal-commands.md` (root +
> submodules) to also forbid here-documents (use `git commit -m` flags or a
> `printf`-written `-F` file) and to disable editors/credential prompts
> (`--no-pager -c core.editor=true`, `GIT_EDITOR=true GIT_TERMINAL_PROMPT=0`), after a
> `git commit -F - <<'EOF'` heredoc left the terminal stuck at the `heredoc>` prompt.
> (2026-11-02) Decision: dropped the `Makefile` in favor of plain shell build scripts.
> There is no uniform cross-platform way to run Make; a simple `.sh` build script is
> much more universally supported — `build.sh` runs natively on macOS/Linux and on
> Windows via Git Bash, while `make` cannot. The root `Makefile` is removed (it was
> also incomplete — `build.sh`/`build.bat` already cover the whole build: clean,
> version, mdmread, template, bundle, patch, copy scripts, copy test). `build.bat`
> (Windows) and `build.sh` (macOS/Linux) remain the two build entry points.
> Closes GitHub issue #31.
> (2026-11-02) README dependency note corrected: `read_excel` also needs `openpyxl`
> (it hardcodes `pd.ExcelFile(..., engine='openpyxl')` in `read_excel_lrw.py` /
> `read_excel_general.py`), so `otherformatsreadpy_excel/requirements.txt` now lists it;
> `xlsxwriter` remains only for `report_excel` (writing). README "On dependencies"
> section shortened; `mdd_to_schema` marked "not actively used, a future feature".
> (2026-11-02) Removed the vendored `microsoft/markitdown` submodule from
> `src/lib/otherformatsreadpy_general_msmarkitdown/lib/`. The reader now imports
> `markitdown` as a normal pip dependency (its `requirements.txt` declares
> `markitdown[pdf,xlsx,docx,pptx,xls,outlook]`), so markitdown is no longer inlined
> into the pinliner bundle.
> (2026-11-02) Root `requirements.txt` is now stdlib-only (a comment-only no-op).
> `src/launcher.py` imports readers/reporters lazily, so the bundle loads without
> `pandas`/`numpy`/`xlsxwriter`/`pydantic`; each reader/reporter declares its own
> dependency (e.g. `pyreadstat` for SPSS, `pandas`+`numpy`+`openpyxl` for Excel,
> `pandas`+`xlsxwriter` for the Excel report, `pydantic` for schema), installed
> best-effort as optional dependencies.
> (2026-11-02) README restructured to be user-facing: removed the ms-markitdown
> explainer and the `csscompressor`/`rjsmin` dependency note; "three ways to launch"
> and the detailed build steps live in `docs/architecture.md`, with the README keeping
> a short "For developers" summary that links there.
> (2026-11-02) BAT launchers restructured: each `src_bat_scripts/run_calling_bundle_*.bat`
> now has a "GLOBAL DEFINITIONS" section at the top (input files, output options,
> config switches) followed by an "EXECUTION" section that starts by calling
> `run_init.bat`. README "How to start it" rewritten around this: edit paths at the
> top, then run the BAT.
> (2026-11-02) Build & packaging: per-reader/per-reporter `requirements.txt` added under
> `src/lib/`; `build.bat` + a new `build.sh` collect them into
> `dist/optional_dependencies/` and copy `run_init.bat`/`run_init.sh` into `dist/`;
> `run_init` prepares a `.venv` and installs base + optional requirements best-effort;
> dist BAT run scripts now drive the bundle with the venv Python. The three launch
> strategies (bundle / direct module / launcher proxy) are documented in `README.md` and
> `docs/architecture.md`.
> Status: `mdmreportpy` backend plugins extracted to `src/plugins/` with a uniform
> hook contract; sanitization helpers extracted to `src/common_functions.py`; tests
> added. NOTE: `--disable-plugin` backend plugin names changed.
> (2026-11-02) Decision: rich-text (`parts`/`role`) `column_headers` are supported in
> the common JSON shape; the diff tool needs a follow-up to pass them through (see §6).
> (2026-11-02) Added a `--output-filename` CLI option to both reporters (`mdmreportpy`
> and `mdmexcelreportpy`); when set it is used verbatim as the output path (matching
> `src/diff_print_expected_filename.py`), otherwise the name is derived from the input
> JSON as before.
>
> **Convention:** read this file at the start of every task and update it at the end,
> so it stays the permanently updated context of the current work (see
> `.clinerules/00-project-context.md`).

## 1. What this project is

MDM-Diff-py is a multi-format **diff / report** tool written in Python. It reads a
variety of proprietary and common formats, normalizes them into a common JSON "report"
shape, and renders the result (primarily) as self-contained HTML — with Excel export
available for grabbing texts/translations.

Formats handled (see `README.md` for the full list):

- MDD (IBM SPSS Data Collection / Unicom Intelligence project files) — the original
  motivation; diff, routing, translations.
- Excel tabs.
- SPSS (`.sav`) — metadata (columns/variables/categories) and optionally data.
- Plain text, tab scripts, DMS scripts.
- Anything readable by `ms markitdown` (pdf, pptx, docx, xlsx, images, audio, …).
- "Diff on diffs" — compare two previously computed diffs.

## 2. High-level architecture / data flow

Every reader produces the same JSON "report" shape, and every reporter consumes it:

```
[input file] --reader--> [JSON report] --reporter--> [HTML / Excel]
```

- **Readers** live under `src/lib/otherformatsreadpy_*` and `src/lib/mdmreadpy`.
- **The canonical JSON producer for MDDs** is `src/lib/mdmreadpy` (`read_mdd.py`),
  which drives the COM API of IBM/Unicom Professional (Windows + Professional
  required).
- **The canonical JSON consumer / HTML reporter** is
  `src/lib/mdmreadpy/src/lib/mdmreportpy` (`report_create.py`); Excel export lives in
  `src/lib/mdmexcelreportpy`.
- **Translation overlay helper** — `MDM-TranslationOverlayHelper`
  (<https://github.com/andreyputilovmaterial/MDM-TranslationOverlayHelper.git>).
- **Diffing** lives in `src/diff_engine` (current) and `src/diff_older` (legacy).
- **`src/launcher.py`** is the universal dispatcher (`--program ...`) used by the
  bundled `mdmtoolsap_bundle.py`.
- **`src/mddtoschema`** derives a JSON *schema* from an MDD (a sibling of the reader,
  not the same thing).

Submodules (see `.gitmodules`):

| Path | Purpose | Remote |
| --- | --- | --- |
| `src/lib/mdmreadpy` | Read MDD → JSON (Windows + IBM/Unicom Professional). | <https://github.com/andreyputilovmaterial/MDM-Read-py.git> |
| `src/lib/mdmreadpy/src/lib/mdmreportpy` | JSON → HTML report. | <https://github.com/andreyputilovmaterial/MDM-Report-py.git> |
| `src/lib/mdmexcelreportpy` | JSON → Excel. | <https://github.com/andreyputilovmaterial/MDM-ExcelReport-py.git> |
| `src/lib/mddtoschema` | MDD → JSON schema. | <https://github.com/andreyputilovmaterial/MDM-ToSchema-py.git> |
| `src/lib/otherformatsreadpy_*` | Other readers (excel, spss, txt, metadata, ms markitdown). | — |
| `src_dev_build/lib/pinliner` | Single-file bundling. | <https://github.com/The-city-not-present/pinliner.git> |

## 3. Build & distribution

`build.bat` (root) uses the vendored `pinliner` fork to produce a single-file
`dist/mdmtoolsap_bundle.py`, patches it to call `src.launcher.main()`, and copies
LICENSE/README/requirements into `dist/`. BAT launchers in `src_bat_scripts/` and
`dist/` drive specific workflows (read, report, diff, aligned diffs, …).

Static assets (HTML/CSS/JS templates, the git `_VERSION` string) are embedded via the
`GENERATED/` folder technique described in `.clinerules/02-python-portability.md`.

## 4. Key design decisions

- **One language:** everything is Python; JS is used only at the very last stage to
  beautify/enhance the HTML page and is intentionally removable (see root `README.md`
  FAQ).
- **JSON is the interchange format.** Readers emit JSON; reporters consume it. The
  intermediate `.json` files are normally deleted after execution in the shipped BATs.
- **Source of truth for the data format is `mdmreportpy`.** The report JSON format and
  the rich-text content format are defined once, in
  `src/lib/mdmreadpy/src/lib/mdmreportpy/docs/report-json-format.md` and
  `.../docs/rich-text-format.md`. All readers, the diff tool, and all reporters defer to
  those files as the master definition.
- **Portability constraints** (see `.clinerules/02-python-portability.md`): relative
  imports, `__init__.py` everywhere, no runtime static assets, minimal dependencies.
- **Dependencies are optional and per-program.** The root bundle is stdlib-only; the
  launcher imports readers/reporters lazily, and each reader/reporter declares its own
  `requirements.txt` under `src/lib/` (collected to `dist/optional_dependencies/`,
  installed best-effort). A missing dependency only disables the program that needs it,
  and only when that program is run.
- **Windows/COM only for MDD input.** Reading MDDs requires IBM/Unicom Professional;
  all other formats are platform-independent.
- **Row names are configurable.** `mdmreadpy` builds each row's `name` via a pluggable
  row-name convention (`--config-row-name-convention ap|mdm`; see `mdmreadpy`'s README/docs).
  The active convention is recorded in `report_scheme.flags` as
  `mdmreadpy:config:row-name-convention:<name>`. The default (`ap`) uses a `.`
  separator, which the diff tool relies on for hierarchical grouping.
- **`mdmreportpy` backend plugins** are isolated in `src/plugins/` with a uniform
  contract (`PluginContext` + named hook points + `run_plugins`), and sanitization
  helpers live in `src/common_functions.py`. Breaking change: the `--disable-plugin`
  values were renamed to `mdd_combine_attributes`, `mdd_validate_labels`,
  `diff_add_classes`, `page_wrap_tables_for_memory_saving`.
- **Non-standard properties on rich-text segments.** Rich-text segments (`text`/`parts`
  plus a `role`) may carry extra, non-standard properties. They must not be a blocker
  in any tool (HTML report, diff, Excel, …) and must not become visible text in the
  HTML report, but they are **not guaranteed** to be preserved, interpreted, or diffed
  meaningfully — e.g. `role` is not semantically diffable. See
  `mdmreportpy/docs/rich-text-format.md`.
- **Reporter output file name.** Both reporters (`mdmreportpy` HTML and
  `mdmexcelreportpy` Excel) derive the output name from the input JSON (`.json` →
  `.html` / `.xlsx`, written next to the input). A `--output-filename` CLI option now
  overrides this; when set it is used **verbatim** as the path (no extension appended),
  consistent with `--output-filename` in `src/diff_print_expected_filename.py`.

## 5. Repository rules

- `.clinerules/00-project-context.md` — read/update this file each task.
- `.clinerules/00-non-interactive-terminal-commands.md` — no pagers/editors/prompts,
  no here-documents; prefer non-interactive commands that exit on their own.
- `.clinerules/01-design-principles.md` — modularity, testing, minimal deps, consistency.
- `.clinerules/02-python-portability.md` — pinliner/`GENERATED` constraints.
- `.clinerules/03-code-style-errors.md` — fail early, readable errors, no over-validation.
- `.clinerules/04-testing.md` — test new features, guard regressions.
- `.clinerules/05-diff-older-frozen.md` — `src/diff_older/` is a frozen historical capture; do not edit.
- `.clinerules/08-commit-messages.md` — commit subject/body style.
- `.clinerules/09-github-issues.md` — fetch open issues at commit/push time and add
  `Closes #N` / `Fixes #N` / `Resolves #N` references.
- `.clinerules/11-submodules-commits.md` — submodule commits must exist on their remote.

## 6. Current focus / roadmap

1. Introduce `docs/project-context.md` (this file) and the read/update convention at
   root and in the `mdmreadpy` / `mdmreportpy` submodules. *(this step)*
2. Align the JSON format between `mdmreadpy` (producer) and `mdmreportpy` (consumer) —
   the output spec of the former should be the input spec of the latter. The source of
   truth for this alignment is `mdmreportpy`'s `docs/report-json-format.md` and
   `docs/rich-text-format.md`.
3. Add tests around the JSON shaping / reporting pure functions.
   *(Partial: `mdmreadpy` has `tests/test_row_name_maker.py`; `mdmreportpy` now has
   `tests/test_common_functions.py` and `tests/test_backend_plugins.py`.)*
4. **Rich-text `column_headers` in the diff tool — need/plan, no implementation yet.**
   *(Decision 2026-11-02: the common JSON shape supports rich-text `column_headers`
   (`parts`/`role`) like cell values.)* `src/diff.py` (plus `src/diff_engine` /
   `src/diff_older`) currently stringifies header values with f-strings
   (`f'{header}'`, `f'{header} (Left file)'`), which flattens any list/dict into its
   Python `repr`. It must be changed to pass rich-text values through unchanged and to
   append the `(Left file)` / `(Right file)` suffix as a separate `part` (or a role)
   rather than concatenating strings.

## 7. Open questions

- Exact final list of report cell-content shapes and `role` values (now drafted in
  `mdmreportpy/docs/rich-text-format.md`; still to be validated against real producer
  output).
- ~~Whether `ms markitdown`'s heavy dependency set should remain optional/vendored.~~
  *(Resolved 2026-11-02: the vendored submodule was removed; `markitdown` is now a
  pip dependency installed best-effort, still optional — see root `README.md`.)*
- Whether rich-text `column_headers` should be *produced* by readers (e.g. `mdmreadpy`
  translation headers) or only *accepted* by reporters, and which custom `role` values
  reporters should render specially.
