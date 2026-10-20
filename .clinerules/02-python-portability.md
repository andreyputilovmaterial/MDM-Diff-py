# Python code style

It must be usable as an imported module *or* included as a git submodule, bundled via
`pinliner`, so it obeys strict portability constraints:

1. Relative imports only — entry-point scripts that are also run directly are the exception (see below),
2. Liftable to a different location in a bigger project without changes,
3. Every folder on the path to every module contains `__init__.py`,
4. No static files/assets used as-is at runtime — static assets are discouraged and,
   if needed, must be embedded into a generated Python module at build time (see below),
5. Minimal dependencies.

## Entry-point scripts and conditional imports

This project can be used in different ways: distributed as a single-file bundle created
with `pinliner`, or called directly during development. To support both, a few scripts
are also launched as a program in development and therefore use a three-way conditional
import block instead of a single import style:

```python
if __name__ == '__main__':
    # run as a program, e.g. `python src/entry_point.py`
    from sibling_module import some_function
elif '.' in __name__:
    # imported as a package member
    from .sibling_module import some_function
else:
    # included in the pinliner bundle with no parent package
    from sibling_module import some_function
```

The module and function names above are illustrative — replace them with the real
sibling module of your entry point. In this repo the scripts that follow this pattern
are `src/launcher.py` and `src/read_mdd.py`. Any script that is meant to be launched
directly should use this pattern; every other module (the ones that are only ever
imported) uses plain relative imports.

## Static assets and the `GENERATED` folder

The default distributable is a single-file bundle produced with `pinliner`, which can
only embed Python modules. A plain static file (an HTML/CSS/JS template, a version
string, or anything that is not a python module, etc.) cannot be used as-is in that bundle, so:

1. **Static assets are discouraged.** It is easier to avoid them than to solve their
   embedding into the pinliner bundle.
2. **When a static asset is necessary — or clearly beneficial (faster development, more
   modular and easier to maintain) — it is allowed, but only via this technique:** the
   build script converts the asset into a Python module written to a `GENERATED`
   subfolder, which the real source code then imports like any other module.

This is a slightly circular workflow: the build script *generates* code that the real
source modules import. Not entirely clean, but it solves the pinliner bundling problem.

Existing example in this repo:

- `build.bat` runs `git describe --tags --dirty` (a non-Python "static asset") and
  writes the result into `src/GENERATED/_VERSION.py` as the `_VERSION` variable, which
  `src/launcher.py` and `src/read_mdd.py` import.

### Embedding larger static assets (illustrative)

The same technique scales to larger static assets such as HTML/CSS/JS templates. The
concrete files below are for illustration only — a report generator would implement it
like this:

- **Development time:** a `*_html_template.py` module loads the files under a
  `src/templates/` directory with `importlib.resources` and minifies them in memory.
- **Build time:** a `build_compiled_template.py` script imports the source package, then
  writes the assembled strings as literals into `src/GENERATED/TEMPLATE.py`.
- **Runtime inside the pinliner bundle:** the module that needs the templates first
  tries to import the source `*_html_template` module; when that fails (a bundle has no
  filesystem resource files) it falls back to
  `from GENERATED import TEMPLATE as html_template`.

(The vendored `mdmreportpy` submodule under `src/lib/mdmreportpy/` is a concrete
instance of this pattern in this repo.)

Note: `importlib.resources` references such as `resources.files("src.templates")` and
build-time imports such as `from src import ...` hardcode the package name (`src` in
this repo). That is part of the technique, but it means the subtree is not relocatable
under a different package name without updating those references.

## When inspecting source code

Any code under a `GENERATED` folder is **generated output, not maintained source code**:

- It exists only to solve the bundling/embedding problem described above.
- It is produced by the build script and can be regenerated at any time.
- It is **not tracked in git** (`.gitignore` excludes `**/GENERATED/`).
- Do not edit it by hand; change the original asset or the build script that produces it
  instead.
