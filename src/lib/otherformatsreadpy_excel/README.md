# Excel reader (`otherformatsreadpy_excel`)

Reads Microsoft Excel workbooks (`.xlsx`) and writes their contents as JSON that the
rest of the MDM toolchain understands (the common JSON "report" shape). This is one of
several "readers" in the global project; its output is consumed by the HTML reporter
(`mdmreportpy`), the Excel reporter (`mdmexcelreportpy`), the diff tool, and any other
consumer of the common JSON shape.

## What it does

1. Opens an Excel workbook with pandas (`engine='openpyxl'`).
2. Converts its sheets into the common JSON "report": each sheet becomes a `section`,
   each row of a sheet becomes a row in the section's `content`, and every row is given
   a unique `name`.
3. Saves the JSON next to the workbook (same base name, `.json` suffix).

The reader does **not** assume a single fixed layout. It first tries to interpret the
workbook as an LRW-style tab dump (`read_excel_lrw`); when that is not recognized, it
falls back to a generic, layout-agnostic reader (`read_excel_general`). The entry point
(`read_excel_entry`) wires the two together.

## The core problem: turning "just tabular data" into keyed rows

The input and the output look almost identical — the input is a table arranged in
sheets, and the report, once rendered by `mdmreportpy`, is also tabular and arranged in
sections. But there is a conceptual difference:

- **Input** is plain tabular data. A sheet may carry a dedicated index column (a first
  column of unique row labels, or a leading index row / banner of column headers) — or
  it may not. Nothing guarantees that the index is present, or where it is.
- **Output** is expected to be *keyed*: every row in a section has a `name` that is a
  unique identifier. Consumers (the diff tool, the reporters) match and group rows by
  that `name`.

So most of this reader is **not** cell copying — it is trying to adapt to the possible
input forms and to heuristically detect the index row and the index column, and then to
manufacture unique keys from whatever the input provides (or fails to provide). That
detection, not the reading itself, is where almost all the complexity lives.

### Two ways this can go wrong

1. **Unexpected input layout.** The detection relies on heuristics, so it can be thrown
   off by an unexpected number of pre-header rows, or by several independent tables
   inside a single sheet. The generic reader explicitly looks for and splits multiple
   data areas per sheet, but there is no layout it can parse with certainty.
2. **The cost of uniqueness.** Even after an index column is detected, the reader still
   has to guarantee unique keys. It enforces uniqueness by comparing each candidate row
   name against every name already emitted for that sheet and, on a collision, appending
   a `[Duplicate #<n>]` suffix. That comparison loop is O(n²) in the number of rows,
   and a sheet can contain on the order of a million rows — so this step, not the actual
   reading, can dominate the runtime.

## Two readers and the fallback

| Module | Role |
| --- | --- |
| `read_excel_entry.py` | Entry point (`--program read_excel`). Tries the LRW reader first, then falls back to the generic reader; writes the JSON. |
| `read_excel_lrw.py` | Reads the LRW tab layout (an `IndexSheet`/`TOC` with a "Table of Contents" and `T1`, `T2`, … data sheets). Raises `MDMExcelReadFormatException` when the layout is not recognized. |
| `read_excel_general.py` | Generic fallback with no layout assumptions: detects data areas, a header row, and an index column on its own. |

## Output JSON shape

The master definition of the common JSON "report" shape lives in `mdmreportpy`
(`src/lib/mdmreadpy/src/lib/mdmreportpy/docs/report-json-format.md`); this is the
producer-specific view for Excel input.

```text
{
  report_type: "Excel File",
  source_file,
  report_datetime_utc,
  report_datetime_local,
  source_file_metadata: [ {name, value} ],
  report_scheme: {
    columns: ["name", ...],
    column_headers: {"name": "Row unique identifier", ...},
    flags: ["data-type:excel", ("excel-type:lrw" for LRW input)]
  },
  sections: [ {name, columns, column_headers, content: [row, ...]}, ... ]
}
```

Each row in `content` is a flat dict keyed by column ids from `report_scheme.columns`
(or the per-section `columns`). Its `name` is the row's unique identifier:

- In the LRW reader, names are composite (section name + ` / ` + row label, with a
  `[Duplicate #<n>]` suffix when a label collides), and rows without a label are folded
  into the previous row.
- In the generic reader, the `name` is either the detected index column's cell value or
  a positional `Line #<n>` fallback.

## Requirements

- `pandas`
- `numpy`
- `openpyxl`

## Usage

```text
python -m src.launcher --program read_excel --inpfile "path\to\file.xlsx"
```

The JSON is written next to the input (same base name, `.json` suffix).
