# Tag messages

These rules only specify a style guide for the annotated-tag message (`git tag -a v... -m "..."`)
and the baseline it compares against; they are not an encouragement to create tags.

## Version naming (context, not the message)

Tags are named `v<major>.<version>.<revision>` — e.g. `v2.021.003`:

- `<major>` — `2`, the stable major version; changes only on a breaking major release.
- `<version>` — the real version number, zero-padded to 3 digits (`021`).
- `<revision>` — a revision within the version, zero-padded to 3 digits (`003`).

The version string shown by `git describe --tags --dirty` (and baked into the build)
is the tag name. This rule governs the tag *message*, not the tag name.

## The message must not repeat the tag name

- Never use the tag name alone as the whole message (e.g. `v2.021.004`).
- The message must describe *what changed*, for a reader of release notes.

## Structure

- First line: a short, user-facing summary of what this release brings — the same
  intent as a commit subject: what changed for the user, not implementation details.
- Body: a bullet list grouped by the widely used release-note categories
  (Keep a Changelog / Conventional Commits):
  - `Added` — new features / behavior.
  - `Changed` — changes to existing behavior.
  - `Fixed` — bug fixes.
  - `Removed` — removed features / behavior.
  - `Deprecated` / `Security` — only when applicable.
- Focus on user-visible changes; omit internal refactoring, tests, build, and
  style-only changes.

## Comparison baseline: the previous *version*, not the previous revision

"What's new in this version" always compares against the last tag of the previous
`<version>` (the middle part), never against the previous `<revision>`:

- For `v2.021.004`, summarize changes since the last `v2.020.*` tag, **not** since
  `v2.021.003`.
- Rationale: `021` is the version; `003`/`004` are revisions *within* version `021`.
  Revisions are internal checkpoints, so the message accumulates everything new in
  version `021` relative to version `020`, and grows as further revisions are added.
- If `<major>` changes (e.g. `2` → `3`), compare against the last tag of the previous
  major line instead.

### Practical recipe

Find the previous version's latest tag, then summarize that range:

    PREV=$(git tag --list 'v2.020.*' --sort=-v:refname | head -1)   # e.g. v2.020.001
    git log --no-merges --oneline "$PREV..v2.021.004"

Turn the resulting commit subjects into the `Added` / `Changed` / `Fixed` / `Removed`
bullets above; a tag that repeats the name is the failure this rule prevents.
