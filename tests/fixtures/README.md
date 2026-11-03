# Example inputs and outputs of the diff tool

These files are small synthetic reports — **not real/sensitive data** — kept here as
example *inputs* and *outputs* for the root diff tool (`src/diff.py`,
`src/diff_engine/`). They are used by `tests/test_diff_fixtures.py`.

- `a1_v1.mdd.json` / `a1_v2.mdd.json` and `b1_today.mdd.json` / `b1_tomorrow.mdd.json`
  — example *inputs*: reader outputs produced by `mdmreadpy` from two versions of two
  small surveys.
- `report.diff.a1_-v1-v2-.mdd.json` and `report.diff.b1_-today-tomorrow-.mdd.json`
  — example *outputs*: `combined`-format diffs of the two pairs above.
- `report.diff.report.diff.-a1_-b1_---v1-today---v2-tomorrow--.mdd.json`
  — a **diff-on-diff** (`sidebyside` format): the diff of the two diff reports above,
  so it is both an output of this tool and a valid higher-level input again.

The filenames of the diff outputs are exactly what the tool writes on disk (the
`report.diff.` prefix is the default output prefix). They are committed despite the
repo-wide `report.*` ignore rule thanks to the local `.gitignore` in this folder.

`tests/test_diff_fixtures.py` re-runs each diff and checks it reproduces the committed
output. Timestamps, source paths, script versions and (for the diff-on-diff) the
fine-grained rich-text *content* are volatile across code versions and are therefore
not compared byte-for-byte; the committed diff columns, flags, section names, change
flags and row statistics are pinned.
