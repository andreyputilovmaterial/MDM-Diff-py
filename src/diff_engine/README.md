# Diff engine (`src/diff_engine`)

> This document is a **duplicate** of `docs/diff-engine.md` (the canonical copy),
> placed here next to the code for convenience. Keep the two in sync.

## Overview

`src/diff_engine` is the implementation behind the diff tool (`src/diff.py`). It reads
two JSON "report" files (see `docs/architecture.md` and the report/rich-text format docs)
and produces a new report in which every changed cell/header value is annotated with
rich-text `role`s that the reporters render as added/removed highlighting.

The engine is format-agnostic at its core: it knows nothing about MDD, Excel, SPSS, etc.
It only manipulates the rich-text JSON values described in
`mdmreportpy/docs/rich-text-format.md`.

## Core principle

Rich text is mapped to a plain sequence of characters, like normal text. We diff that
plain character sequence. Then we map the diff back to the blocks (segments) that make
up the rich text.

Concretely:

1. **Flatten.** Any rich-text value is converted into a flat sequence of `(role, char)`
   tuples via `as_sequence_with_roles()`. `as_plain_text()` gives the plain string.
   Because flattening is character-for-character (including the punctuation used to
   render property lists, quotes, etc.), offsets in the flat text map back to positions
   in the original blocks.
2. **Diff.** The diff runs on the flat text (or on lines/words derived from it) using
   `difflib.SequenceMatcher` and the `TextWithRolesSequenceMatcher` wrapper.
3. **Project back.** The resulting opcodes are mapped back onto the original blocks via
   `split_piece()`. Each opcode span `[i1, i2)` over the flat text is sliced out of the
   corresponding block(s), and the slices are wrapped as `change` segments
   (`role: added` / `removed`) or `context` segments.

## Value formats (`detect_format`)

All diff functions dispatch on the "format" of a value, detected by `detect_format()`:

| Format | Detected when | Diff behavior |
| --- | --- | --- |
| `(none)` | `None`, empty string/list/dict, or an all-empty value | treated as empty; no diff |
| `(str)` | `str`, `int`, `float`, `bool` | plain-text diff (two-step line/word) |
| `(list)` | a `list` that is not a property list | rich-text list of segments; diff as text then project back |
| `(propertylist)` | a list of `{"name": …, "value": …}` records | structural, keyed on `name` |
| `(dict)` | any other `dict` | key-by-key structural compare |
| `(segment)` | a `dict` with a `text` or `parts` payload (+ optional `role`) | compare roles, then recurse into payload |
| `(uncategorized)` | anything else | passed through / stringified |

Note: `(segment)` is the rich-text "segment" shape (`{"text": …}` or
`{"parts": […]}`), and `(propertylist)` is how `source_file_metadata` and attribute
lists are represented (see `rich-text-format.md`).

## Common format denominator

Before diffing, both sides are cast to a **common format**:

- `find_common_format_denominator(sig1, sig2)` does a breadth-first search over the
  allowed format conversions (`possible_transformations`) to find the closest format both
  sides can be converted to.
- `find_common_format_denominator_with_fallback_str(...)` falls back to `(str)` when no
  common format is found.
- `as_format(inp, source_fmt, dest_fmt)` performs the actual conversion. Conversion may
  take several intermediate steps: `as_format` walks the shortest path through
  `possible_transformations` (BFS), so a destination reachable only indirectly (e.g.
  `(dict) → (str)` via `(uncategorized)`) still converts.

This is why, for example, a `(list)` on one side and a `(str)` on the other can still be
diffed — both are cast to a common format before the format-specific handler runs.

## Three output modes

Every format has three handler families, chosen by the caller (`src/diff.py`):

- **`finddiff_values_*_formatsidebyside(left, right, config)`** — returns
  `(left_result, right_result)` as two separate rich-text values, for side-by-side
  display.
- **`finddiff_values_*_formatcombined(left, right, config)`** — returns a single
  rich-text value with `added`/`removed` segments interleaved, for a combined view.
- **`finddiff_values_*_formatsimple(left, right, config)`** — returns a value of the same
  type, without wrapping in `change`/`context` segments (used where only the merged/changed
  result is needed).

The entry points are the three dispatchers:

- `finddiff_values_general_formatsidebyside()`
- `finddiff_values_general_formatcombined()`
- `finddiff_values_general_formatsimple()`

Each detects both formats, finds the common denominator, casts both sides, then calls the
per-format handler for that mode (falling back to string diff if the formats still differ).

## Text diffing (two-step, multi-line)

`finddiff_values_text_*` handles plain `(str)`/numeric values. For multi-line text it
diffs in two steps:

1. **Rows first.** `text_split_lines()` splits into lines (after
   `sanitize_text_normalizelinebreaks()`), and `SequenceMatcher` runs at the line level.
2. **Then within each row.** Each aligned line pair is split into words via
   `text_split_words()` and diffed again with `SequenceMatcher` at the word level.

Inserted/removed lines are padded (`fill_same_number_linebreaks()`) so left and right stay
aligned for side-by-side rendering.

## Side-by-side line alignment

For side-by-side output the two sides are rendered next to each other, so they must
occupy the **same number of lines**. The engine guarantees this with two helpers:

- `count_linebreaks(value)` — the number of *visual* lines the value renders as. A
  trailing newline is an (empty) line of its own, so `'a\n'` is 2 lines, `'a\nb\n'` is 3,
  and `''` is 1.
- `fill_same_number_linebreaks(left, right)` — appends a `context` segment holding
  `'\n' * N` to the **shorter** side, i.e. appends trailing empty lines, until both sides
  have the same line count.

This padding is the "append empty lines so blocks align on left and right" behaviour: the
shorter column gains trailing empty lines, never the longer one. Every side-by-side
handler runs this (either inline in the text path or via a final
`fill_same_number_linebreaks` call), so `count_linebreaks(left) == count_linebreaks(right)`
holds — verified by `tests/test_diff_engine_richtext.py::TestSideBySideLineAlignment`.

Note: this only pads the *shorter* side with trailing newlines; it never changes the
longer side, so it cannot drive a different line count on its own.

## Rich-text list diffing (as text, then project back)

`finddiff_values_list_formatsidebyside()` delegates to
`finddiff_values_list_matchingastext_formatsidebyside()` (the "newer" implementation; the
older `finddiff_values_list_onlyelements_formatsidebyside()` compares element sequences
directly and is kept for reference).

The newer path is the canonical illustration of the core principle:

1. `as_sequence_with_roles(cmpdata)` flattens the list to `(role, char)` tuples.
2. `TextWithRolesSequenceMatcher` (in `difflib_wrapper.py`) diffs the two flat sequences
   **hierarchically**:
   - **Step 1 — line level.** Lines are compared using their **trimmed** text
     (`.strip()`), so a change of indentation alone does not break the match.
   - **Step 2 — character level.** Within each line group, the original (untrimmed)
     characters are diffed again with `SequenceMatcher`.
   - **Whitespace caveat.** Because step 1 ignores leading/trailing whitespace but step 2
     does not, a line pair that step 1 reports as "equal" can still produce
     `replace`/`insert`/`delete` opcodes in step 2. This is deliberate: even when the
     trimmed rows are identical, the real difference may live entirely in those ignored
     leading/trailing spaces, so left and right are **always** compared within each block.
3. **Project back.** The character-level opcodes are mapped back onto the original list
   elements by `split_piece()`, which slices each block at the opcode boundaries. Full
   blocks are reused as-is; partial blocks are re-split recursively.

### The hard part: mapping back to blocks

The projection in step 3 is the trickiest part of the engine. `split_piece(input, start,
end, to_hash)` slices a block at flat-text offsets `[start, end)`:

- For `(str)` and `(list)` pieces it recurses and re-slices.
- For `(segment)` pieces it re-slices the inner `text`/`parts` payload.
- For `(propertylist)` and `(dict)` pieces it **cannot** split meaningfully and raises
  `ErrorCantSplitAtomicPiece` — these are "atomic" from the text-diff's point of view.
  This is the case where a text change cannot be mapped back into the block structure, and
  the engine surfaces it explicitly rather than silently producing a wrong result.

This is the known, deliberately-hard case: when a character diff spans a property list or
dict, there is no faithful block-level representation, so the engine refuses and lets the
caller see exactly where it happened (see the `# TODO:` re-raise comments in the list
matcher).

## Property list (keyed structural compare)

`finddiff_values_propertylist_*` treats a property list as a collection keyed by `name`:

1. The two lists are indexed into dicts keyed by `name`.
2. A combined, ordered key list is built (`diff_make_combined_list()`).
3. For each key: if it exists on both sides, the two `value`s are diffed (recursively);
   if only on one side, it is marked `added`/`removed`.

This is how `source_file_metadata` and attribute lists are compared structurally — by key,
not as flat text.

## Segment diffing

`finddiff_values_segment_*` handles a single `(segment)`:

- If both `role`s are `context`, the payloads are passed through as context without
  diffing (this is the "context block" pass-through used by diff-on-diff).
- If roles differ but payloads are identical, one side is marked `removed` and the other
  `added` (a role change is not semantically diffable — see `rich-text-format.md`).
- Otherwise it recurses into the `text`/`parts` payload (casting `text` to a `(list)` of
  parts when needed).

## Dict diffing

`finddiff_values_dict_*` combines the two dicts' keys and diffs each value recursively.
Keys present on only one side produce an `added`/`removed` value (or `None` on the missing
side in side-by-side mode).

## Diff-on-diff (diffing a diff)

The diff tool's own output is a valid report JSON (`report_type: "diff"`), so two diff
reports can themselves be diffed, producing a **second-level diff**. `src/diff.py`
`find_diff` detects this — when either input is a diff report (the
`diff_source_*:data-type:diff` flag) it sets `config['input_is_diff']` and enters a special
mode. Concrete example files live in `tests-real-sensitive-data/testsuite/`:
`a1_*.mdd.json` / `b1_*.mdd.json` are the sources, `report.diff.a1_…` and
`report.diff.b1_…` are first-level diffs, and
`report.diff.report.diff.-a1_-b1_---…---….mdd.json` is the second-level diff.

Two global techniques make this possible.

### 1. Relocating existing roles (`source_*`)

Before a cell value coming from a previous diff is compared,
`normalize_input_relocate_diff_markers()` rewrites every change role it already carries:

| input role | relocated to |
| --- | --- |
| `added` | `source_added` |
| `removed` | `source_removed` |
| `source_added` / `source_removed` / `source_change` | `source_`-prefixed again |
| `context` / `None` / anything else | unchanged |

This pushes the *previous* diff's `added`/`removed` marks out of the way so the second
pass can freely assign fresh `added`/`removed` without the two layers colliding.

### 2. Splitting into `context` and `change` blocks

Every segment is classified as either a **`change`** block (`role` in `added`, `removed`,
`source_added`, `source_removed`, `source_change`) or a **`context`** block
(`role: context`), via `detect_diffsegment_role()` / `detect_segment_role()`. The segment
handler (`finddiff_values_segment_*`) uses this classification: two `context` blocks are
passed through untouched, while `change` blocks are processed and receive new
`added`/`removed` marks.

The **goal** of this splitting is an invariant: the changes found on the left must line up
with the same changes on the right. Large unchanged runs in between (`context` blocks) are
allowed — indeed expected — to be identical on both sides; what matters is that the
`change` blocks correspond left ↔ right.

### Result: nested roles

A second-level diff therefore nests roles. For example, from
`tests-real-sensitive-data/testsuite/`:

```json
{"role": "removed", "text": {"role": "source_added", "text": " listed"}}
```

reads as: the text ` listed` was *added* in the first-level diff (inner `source_added`),
and is now *removed* in the second-level diff (outer `removed`).

### How it is highlighted

`mdmreportpy` renders roles as (possibly nested) spans — see
`src/lib/mdmreadpy/src/lib/mdmreportpy/src/common_functions.py`
(`html_sanitize_value_general`) and `src/templates/mdmreporttable.css`:

- **Plain diff** — `added` = green fill, `removed` = red fill.
- **Diff-of-diff** (the report is wrapped in `.mdmdiff-in-diff`) — the *new*
  `added`/`removed` become **outlines** (green/red borders, no fill), while the relocated
  `source_added`/`source_removed` become **light fills**. The two layers are therefore
  visually distinct and stack: the underlying first-level change shows through the outline
  of the new second-level change.

## Roles & segment terminology

- A **segment** is the unit of diff output: a dict with a `role` field. Its payload lives
  in `text` or `parts`.
- A **`change`** segment (`role: added` / `removed` / `source_added` / `source_removed` /
  `source_change`) is an actual result to display.
- A **`context`** segment (`role: context`) is not a change by itself, but is emitted so
  the display knows where the change sits relative to unchanged surroundings.

`detect_segment_role()` / `detect_diffsegment_role()` infer whether a value (or a whole
subtree) is a `change`, `context`, or `mixed`.

## Supporting helpers (in `common_functions.py`)

- `text_split_words(s)` / `text_split_lines(s)` — split into word/line pieces for the
  word/line-level passes.
- `sanitize_text_normalizelinebreaks(s)` — normalize `\r\n` and `\r` to `\n` **while
  preserving the string length** (important so offsets stay valid).
- `as_plain_text(value)` — extract the plain text of any format.
- `as_sequence_with_roles(value, …)` — extract the `(role, char)` sequence of any format
  (property lists are rendered with their `name = "value"` syntax so offsets match the
  rendered text).
- `as_hash(value)` — canonical string form, used for cheap equality checks.
- `count_linebreaks(value)` / `fill_same_number_linebreaks(left, right)` — keep left/right
  line counts equal for side-by-side alignment (see "Side-by-side line alignment").
- `is_empty(value)` — a format-aware "is this value empty" check.
- `as_segment_context(value)` / `as_segment_change(value, op)` — wrap a piece as a
  context/change segment.
- `with_appended_part(value, part)` — append an extra segment (e.g. ` (Left file)`) to a
  rich-text value without flattening it.
- `split_piece(input, start, end, to_hash)` — slice a block at flat-text offsets (see
  "mapping back to blocks").

## Testing

`tests/test_diff_engine_richtext.py` holds the correctness suite. Its backbone is a
round-trip invariant, applied over a matrix of rich-text shapes:

- side-by-side: `as_plain_text(left_result) == as_plain_text(left_input)` (and same for
  the right);
- combined: removing the `added` segments reproduces the left text, removing the
  `removed` segments reproduces the right text.

This catches *silent* corruption — a dropped last piece, a duplicated common block, or
spurious whitespace. It also pins the atomic-split behaviour (issue #21), the combined
no-duplication guarantee (issue #24), and the multi-step `as_format` conversion.

## Known limitations / notes

- `diff_normalize()` raises `NotImplementedError` for `ignorewhitespace` and
  `ignoreaccents` (only `ignorecase` is implemented).
- Row-level diffing (`finddiff_row_names_respecting_groups`) returns `RowDiff(name, status)`
  objects (see `src/diff_engine/contracts.py`) rather than exposing `SequenceMatcher`
  opcodes; `status` is `ROW_STATUS_KEEP` / `ROW_STATUS_INSERT` / `ROW_STATUS_REMOVE`.
- `(propertylist)` and `(dict)` blocks are atomic with respect to text slicing; a
  character diff spanning them raises `ErrorCantSplitAtomicPiece`.
- Multi-line text where the two sides differ in line count can pick up spurious spaces
  (e.g. `a\nb\nc` vs `a\nb` yields `a\nb \nc` on the left). Tracked as an `xfail` test in
  `tests/test_diff_engine_richtext.py`.
- `did_change()` on a combined result containing a plain `(dict)` raises
  `ErrorDiffClassesNotPossibleToDetect` (a plain dict is not a defined rich-text shape,
  so this only arises for out-of-format inputs).
- A property list whose every value is empty is treated as `(none)` by `is_empty`, so
  diffing `[{"name": "k", "value": ""}]` against a non-empty value collapses the empty
  side to `[]` (losing the key) and can leave the side-by-side line counts unequal.
  Tracked as an `xfail` test in `tests/test_diff_engine_richtext.py`.
