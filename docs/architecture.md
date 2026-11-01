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
  two JSON reports and writes a new JSON report.
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

`build.bat` uses the vendored `pinliner` fork to produce a single-file
`dist/mdmtoolsap_bundle.py`, patches it to call `src.launcher.main()`, and copies
LICENSE/README/requirements into `dist/`. BAT launchers in `src_bat_scripts/` drive
specific workflows.
