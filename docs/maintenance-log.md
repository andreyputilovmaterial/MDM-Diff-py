# Maintenance log

> Cross-project maintenance notes. Entries here capture **structural** changes
> that apply to any project sharing this repo's shape — a `launcher` used as the
> key router (`--program <name>`), and `pinliner` producing a one-file bundle.
>
> Repo-specific changes do **not** belong here; they stay in the commit history
> and `docs/project-context.md`. Anything recorded here is meant to be repeatable
> in other projects of the same structure.
>
> Entries are ordered **newest first**.

## How to read an entry

Each entry is a section whose heading reads like a commit subject: it states the
**intent** of the change and **where** the change happens (component/module).
The body states the **requirement first** — how the code should be — and only
then the change that reaches it. The point is that an agent can *verify* the
requirement against any project, even when its current code does not look exactly
like the `Input` example; anything that does not match should be updated.

- **When** — date/time requested and implemented.
- **What & why** — the request and the reasoning behind the chosen approach.
- **Input** — a sample of the code/file **before** the change (one of several
  possible shapes; the real "before" may differ).
- **Output** — a sample of the code/file **after** the change.
- **Repeat** — the requirement to verify in another project, each item stated
  declaratively ("… should be …"); if the code does not match, change it to do so.

---

## Entry-point imports: replace the three-branch `__name__` split with a two-branch `__package__` split

- **Requested:** 2026-11-04 18:09 MSK
- **Implemented:** 2026-11-04 18:20 MSK (reworked)
- **Where:** entry-point modules (`src/launcher.py` + the `--program` targets);
  the build script and run scripts are covered in the Repeat checklist.

### What & why

The launcher and the starter modules it dispatches to are the only files that
are *invoked* (as `__main__` via `-m`, or imported by the bundle); every other
module is only ever imported. Two concepts are easy to conflate here, so they
are spelled out separately:

- **Invocation modes** — the ways to *start* the program:
  1. from the **bundle** (`python apqa_bundle.py --program X`),
  2. through the **launcher** (`python -m src.launcher --program X`),
  3. **directly** at a starter module (`python -m src.main_ui_program …`).
- **Import selection** — how the `import` statements of an entry-point module
  branch on the import context (package vs flat), set by Python via `__package__`.
  It is **not** a 1:1 map of the invocation modes.

The old code selected imports with a **three-branch `__name__` split**:

- `if __name__ == '__main__'` — "run as a program",
- `elif '.' in __name__` — "imported as a package",
- `else` — "inlined with no parent package".

That three-branch split is confusing because it is **not** the same as the
invocation modes, and its `__main__` branch meant different things in different
projects (see the three "before" variants below). In practice the `__main__`
branch and the `else` branch always used the **same** flat imports, so they
collapse into one; the only real distinction is *inside a package* vs *no parent
package*, which `__package__` encodes directly.

Plain-script invocation (`python src/X.py`, without `-m`) is **dropped**: making
it work required a `sys.path` bootstrap and non-relative `src.*` imports, which
are not worth it. Supported invocation modes are the bundle and `-m`.

### Input (before) — three variants that grew out of the confusion

Variant A — classical three-branch, flat `__main__` (MDM-Diff-py `src/diff.py`,
commit `7baf51c`):

```python
if __name__ == '__main__':
    from diff_engine import diff_functions       # flat (script dir on sys.path)
elif '.' in __name__:
    from .diff_engine import diff_functions      # relative (package)
else:
    from diff_engine import diff_functions       # flat (no parent package)
```

Variant B — three-branch with `src.` in the `__main__` branch (apqa's original
`src/launcher.py`, to make `python -m src.launcher` work):

```python
if __name__ == '__main__':
    from src.GENERATED.VERSION import _VERSION   # absolute src.* (repo root on path)
elif '.' in __name__:
    from .GENERATED.VERSION import _VERSION      # relative (package)
else:
    from GENERATED.VERSION import _VERSION       # flat (no parent package)
```

Variant C — `_import_module` wrapper (MDM-Diff-py `src/launcher.py`):

```python
def _import_module(flat_name):
    if __name__ == '__main__':
        return importlib.import_module(flat_name)
    elif '.' in __name__:
        return importlib.import_module('.' + flat_name, package=__package__)
    else:
        return importlib.import_module(flat_name)
```

### Output (after) — two branches keyed on `__package__`

```python
if __package__:
    from .GENERATED.VERSION import _VERSION   # relative (package / -m / bundle)
else:
    from GENERATED.VERSION import _VERSION    # flat (no parent package)
```

Each entry-point module repeats this pattern for all its imports (one import is
shown here for brevity). No `sys.path` manipulation, no `src.*` absolute imports.

The bundle entry point is generated by pinliner (not hand-patched):

```bash
python pinliner/pinliner.py src -o dist/apqa_bundle.py --main src.launcher --main-attr main
```

### Repeat

1. **Entry-point modules** (the launcher and every module it dispatches to via
   `--program`) should select imports on `__package__` — never on `__name__`:
   - `__package__` truthy → relative imports (`from .X import …`).
   - `__package__` falsy → flat imports (`from X import …`).
   If a module still branches on `__name__` (in any of the "before" variants),
   replace that split with the two-branch `__package__` check above.
2. Each starter module should have an `if __name__ == '__main__':` block that
   calls its entry function, so `python -m pkg.module` works; if it is missing,
   add it.
3. **All other modules** should use plain relative imports only; if a non-entry
   module uses `src.*` absolute imports or `__package__`/`__name__` branching,
   change it to plain relative imports.
4. The **bundle entry point** should come from pinliner `--main <module>`
   --main-attr <attr>` (default attr `main`); the build script should **not**
   append `launcher.main()`. If it does, remove that call.
5. **Plain-script invocation** (`python pkg/module.py`) should stay unsupported:
   no `sys.path` hacks or `pkg.*` absolute imports to make it work — use `-m`
   instead. If such bootstraps or imports exist, remove them.


---

## maintenance-log: add a cross-project log for structural changes

- **Requested:** 2026-11-04 18:12 MSK
- **Implemented:** 2026-11-04 18:12 MSK
- **Where:** `docs/maintenance-log.md` (this file).

### What & why

The same structural conventions (import style, error reporting, output
coloring, argparse conventions, bundling/call conventions) are re-applied in
every project that shares the "launcher `--program` router + pinliner one-file
bundle" shape. Those need one dedicated place, separate from repo-specific
notes (`docs/project-context.md`) and the commit history, so they can be found
and repeated later. This file is that place.

### Input (before)

No dedicated file existed; structural notes were mixed into
`docs/project-context.md` and commit messages.

### Output (after)

`docs/maintenance-log.md` with a scoping header, a "How to read an entry"
format guide, and one section per structural change (**newest first**) — each
section headed like
a commit subject (intent + where) and answering When / What & why / Input /
Output / Repeat (requirement-first):

```markdown
# Maintenance log
> Cross-project maintenance notes. ...

## How to read an entry
- **When** — date/time requested and implemented.
- **What & why** — the request and the reasoning.
- **Input** — a sample of the code/file before the change.
- **Output** — a sample of the code/file after the change.
- **Repeat** — the requirement, stated first ("… should be …"); change anything that does not match.

---

## <change title, like a commit subject>
- **Requested:** ...
- **Implemented:** ...
- **Where:** ...
### What & why
...
### Input (before)
...
### Output (after)
...
### Repeat
... (each item: requirement first, then "if it does not match, change …")
```

### Repeat

1. The repo should have a `docs/maintenance-log.md`; create it in the docs folder of the repo if it is missing.
2. It should open with the scoping header and a "How to read an entry" guide; add them if they are missing.
3. It should contain one section per structural change, **newest first**, each in the exact shape defined above; add or adjust entries to match.

