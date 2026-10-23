# Project Context — MDM-Diff-py

> Last updated: 2026-10-23
> Status: initial capture for the root repository.
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
- **Diffing** lives in `src/diff_engine` (current) and `src/diff_older` (legacy).
- **`src/launcher.py`** is the universal dispatcher (`--program ...`) used by the
  bundled `mdmtoolsap_bundle.py`.
- **`src/mddtoschema`** derives a JSON *schema* from an MDD (a sibling of the reader,
  not the same thing).

Submodules (see `.gitmodules`):

| Path | Purpose |
| --- | --- |
| `src/lib/mdmreadpy` | Read MDD → JSON (Windows + IBM/Unicom Professional). |
| `src/lib/mdmreadpy/src/lib/mdmreportpy` | JSON → HTML report. |
| `src/lib/mdmexcelreportpy` | JSON → Excel. |
| `src/lib/mddtoschema` | MDD → JSON schema. |
| `src/lib/otherformatsreadpy_*` | Other readers (excel, spss, txt, metadata, ms markitdown). |
| `src_dev_build/lib/pinliner` | Single-file bundling. |

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
- **Portability constraints** (see `.clinerules/02-python-portability.md`): relative
  imports, `__init__.py` everywhere, no runtime static assets, minimal dependencies.
- **Windows/COM only for MDD input.** Reading MDDs requires IBM/Unicom Professional;
  all other formats are platform-independent.

## 5. Repository rules

- `.clinerules/00-project-context.md` — read/update this file each task.
- `.clinerules/01-design-principles.md` — modularity, testing, minimal deps, consistency.
- `.clinerules/02-python-portability.md` — pinliner/`GENERATED` constraints.
- `.clinerules/03-code-style-errors.md` — fail early, readable errors, no over-validation.
- `.clinerules/04-testing.md` — test new features, guard regressions.

## 6. Current focus / roadmap

1. Introduce `docs/project-context.md` (this file) and the read/update convention at
   root and in the `mdmreadpy` / `mdmreportpy` submodules. *(this step)*
2. Align the JSON format between `mdmreadpy` (producer) and `mdmreportpy` (consumer) —
   the output spec of the former should be the input spec of the latter.
3. Add tests around the JSON shaping / reporting pure functions (currently no automated
   tests anywhere).

## 7. Open questions

- Exact final list of report cell-content shapes and `role` values (being formalized in
  `mdmreportpy/docs/project-context.md`).
- Whether `ms markitdown`'s heavy dependency set should remain optional/vendored (see
  root `README.md`).
