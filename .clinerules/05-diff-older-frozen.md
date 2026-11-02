# Frozen legacy code (`src/diff_older`)

- `src/diff_older/` is a frozen capture of the older diff implementation, kept for
  reference/comparison only. It must stay matching its state on the remote `main`.
- Do not edit, refactor, "fix", or modernize anything under `src/diff_older/`.
  Formatting/style mismatches there are expected and acceptable.
- In particular, do not apply the modern rich-text `role` cleanup (or remove the
  deprecated `<<ADDED>>` / `<<REMOVED>>` markers) in this folder — those markers are
  part of the frozen snapshot.
