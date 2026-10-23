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
- **Universal dispatcher** — `src/launcher.py` (`--program ...`).
- **Schema generator** — `src/mddtoschema` (MDD → JSON schema; distinct from the
  reader).

For example, the MDD diff workflow is:

```
MDD A --mdmreadpy--> JSON A --\
                               diff --> JSON diff --mdmreportpy--> HTML
MDD B --mdmreadpy--> JSON B --/
```

## Submodules (`.gitmodules`)

| Path | Purpose |
| --- | --- |
| `src/lib/mdmreadpy` | MDD → JSON. |
| `src/lib/mdmreadpy/src/lib/mdmreportpy` | JSON → HTML. |
| `src/lib/mdmexcelreportpy` | JSON → Excel. |
| `src/lib/mddtoschema` | MDD → JSON schema. |
| `src/lib/otherformatsreadpy_*` | Other readers. |
| `src_dev_build/lib/pinliner` | Single-file bundling. |

## Build & distribution

`build.bat` uses the vendored `pinliner` fork to produce a single-file
`dist/mdmtoolsap_bundle.py`, patches it to call `src.launcher.main()`, and copies
LICENSE/README/requirements into `dist/`. BAT launchers in `src_bat_scripts/` drive
specific workflows.
