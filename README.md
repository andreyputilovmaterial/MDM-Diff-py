# MDM-Diff-py

A new iteration of diff between MDD files, Excel files (wow!), SPSS (inluding only columns/variables, or also data), Tab Scripts, DMS, Text and many more formats. All in python. No mrs vbscript code and much less js.

## How to start it

Download mdmtoolsap_bundle.py and a BAT for your file type file from
[Releases](../../releases/latest).

Edit the BAT file and insert paths to compared files.

Each distributed BAT (e.g. `run_diff_excel.bat`) starts by calling `run_init.bat`,
which creates a local `.venv` virtual environment, installs `requirements.txt`, and
then installs the optional per-reader/per-reporter dependencies from
`optional_dependencies/` best-effort. The BAT then runs the bundle with the virtual
environment's Python (`.venv\Scripts\python.exe`). On macOS/Linux use `run_init.sh`
and the corresponding `.sh` launchers.

You need python installed to run this. To compare MDDs, you need IBM/Unicom Professional to have this tool running. It is a requirement. If not dealing with MDDs, having Unicom/IBM Professional is unnecessary.

### On necessary dependencies and ms markitdown

If you don't need to read input files with ms markitdown, dependencies are minimal. You just won't be able to use that ms markitdown way of reading files. Actually, ms markitdown is quite powerful - using it, you can read, html, excel, pdf, images, transcribed audio, etc. But it has a lot of dependencies now (it was much simpler is earlier versions), including openai libraries, azure-ai-documentintelligence, etc... Ms markitdown now comes with docker file - a different way of running the scripts - it is supposed that you create and run a container with python code. This diff tool was initially started as a simple script, so I am not sure if it worth it installing all these complicated dependencies without version control on your local machine. It's not a good practice, cause versions of packages might be important.

The core dependencies (`pandas`, `numpy`, `xlsxwriter`, `pydantic`) live in the root
`requirements.txt` and are always installed. Everything else — including `pywin32`
(MDD, Windows-only) and `markitdown` (heavy) — is declared in each reader's/reporter's
own `requirements.txt` under `src/lib/`; `build.bat`/`build.sh` copy those into
`dist/optional_dependencies/` and `run_init` installs them best-effort, so a missing
optional package only disables the corresponding reader/reporter. `markitdown` is
installed from PyPI as a regular optional dependency (it is *not* bundled into
`mdmtoolsap_bundle.py`).

## Frequently asked questions

* Q: What do I need to run this?<br />A: You need python installed to run this. To compare MDDs, you need IBM/Unicom Professional to have this tool running. It is a requirement. If not dealing with MDDs, having Unicom/IBM Professional is unnecessary.
* Q: Why the chosen language is python?<br />A: I can't write it all in mrs scripts in VBScript. This language is too limited and too stupid. So I had to go for some other alternative, and python is fine, it's a simple scripting language and it has all necessary dependencies. My earier attempts were to keep code partially in mrs scripts but then I realized everything can be done in python so it's easier to opt for one single language. Also I have some additions in JS but this is designed itentionally to add some unnecessary code that runs separately just to beautify the page at the very last stage, add more control over it, add the ability to show or hide columns. But all JS here is unnecessary and can be removed for simplification
* Q: Why are you doing this?<br />A: Everyone has some hobbies. I am not doing it at work/labor time. I find it interesting to find what we can do. It's some demonstrator of technologies. Maybe saying "tech" sounds too loud when I did not actually invent anything outstanding here - I am just reading fields utilizing existing API and writing it to HTML - nothing extraordinary - but I believe it can be developed to more sophisticated shapes.

## Which types of files can be compared?

* MDD files. That's why this tool was invented. It can also compare it with routing or with translations. It is configurable, it can handle.
* Excel tabs. This is maybe even more important than comparing MDDs
* SPSS - I suggest only comparing metadata (columns/variables and category analysis values) and not comparing data (this can be configured from within BAT file) because the results are printed in html page - if you include data - the page would probably be too big to load in browser, even in smallest projects. However, the tool is capable of reading and comparing SPSS file contents.
* Any text files, including tab scripts and dms scripts. I highly recommend using it for DA exports
* Any pdf, ppts, word, xlsx, even transcripted audio or images - everything that can be read with ms markitdown (WARNING: see a note above on "On necessary dependencies and ms markitdown")
* Diff on diffs! The concept is:<br />Step 1, we find diff between workflow 1 before and after, save as diff 1. Step 2, we find diff between workflow 2 before and after, save as diff 2. Step 3, we compare diff 1 vs diff 2, to see that same updates were implemented in both workflows. Like, same changes are seen in old and new auto-mdd from DA, and same updates are made in old and new survey mdd.

## What are the output formats that this tool can generate?

* The default one, which I encourage you to use, is **html****
* Before that, a **.json** scheme is produced. However, in BAT files distributed with this tool, this is configured that .json files are deleted after the execution
* An **Excel** can also be generated. I know most people love Excel. But in fact it's not as useful if used by this tool. It can't give you as detailed output as you wish, with every property and value in its own cell. And when multiple properties are printed within one cell, it's quite hard to use  
However, Excel is super useful if you need to grab texts or translations from your MDD

## For End Users: how to debug?

Ok, you are starting the tool and it crashes. Error messages report some problem and line number but you don't know where to check - where do you find that line number? Ok, there's a solution. Open mdmtoolsap_bundle.py and change CONFIG_VERBOSE to True (twice). Run the tool again. Ok, nothing changed, it crashes, it reportes the line number. But now you have modules saved in the same working folder where you start the script. So you can find the line number and see what is going on!

Besides that, I tried to make error messages very descriptive, reporting anything that is going on not really well. I am also printing blocks where it happened - row names, seciton names... so that it's easy to understand what's causing the problem.

## Three ways to launch the program

There is one universal dispatcher — `src/launcher.py` — that routes `--program <name>`
to the right entry point, but the same program can be started three equivalent ways.
This schema is repeated in every submodule that ships a `launcher.py`
(`mdmreadpy`, `mdmreportpy`, `mdmexcelreportpy`, `mddtoschema`).

1. **From the single-file bundle** (what end users get). `build.bat`/`build.sh` run
   `pinliner` to produce `dist/mdmtoolsap_bundle.py` and append
   `from src import launcher; launcher.main()`. The BAT launchers in
   `src_bat_scripts/` are copied (and renamed) into `dist/` — e.g.
   `run_calling_bundle_excel.bat` → `dist/run_diff_excel.bat` — and drive the bundle
   with the venv Python:

       run_init.bat
       .venv\Scripts\python.exe mdmtoolsap_bundle.py --program diff ...

2. **Pointing at the exact program module** (development, most direct). Run the
   entry-point module itself, bypassing the dispatcher:

       python "../src/diff.py" --cmp-scheme-left A.json --cmp-scheme-right B.json

   See `src_bat_scripts/run_individual_scripts.bat`.

3. **Through the launcher proxy** (development, single dispatch point). Run the
   dispatcher directly:

       python "../src/launcher.py" --program diff ...

   See `src_bat_scripts/run_as_directory.bat`.

## For developers: how to build distributable files?

There are two equivalent scripts: `build.bat` (Windows) and `build.sh` (macOS/Linux).

You need pinliner to run this, but the version found on internet was not working well for me. I made certain fixes, please use my personal pinliner version (inluded in src-make folder, so this is a part of the distribution).

Everything else that is going on can be clearly found in the build scripts: the bundle
created is renamed to `mdmtoolsap_bundle.py`, a couple more lines are added to get it
running, the bat files are renamed, and the path to the bundle is changed to
`mdmtoolsap_bundle.py` (and the launcher python is switched to the venv python) within
those bat files. The build also collects every `requirements.txt` under `src/lib/`
into `dist/optional_dependencies/` and copies `run_init.bat`/`run_init.sh` into
`dist/`. Results are in `dist/` subdirectory.

## Documentation

- [Architecture](docs/architecture.md) — stable overview of the toolchain and how the
  readers, diff, and reporters fit together.
- **Source of truth for the data format** — the report JSON format and the rich-text
  format are defined once, in `mdmreportpy`
  ([`src/lib/mdmreadpy/src/lib/mdmreportpy/docs/report-json-format.md`](src/lib/mdmreadpy/src/lib/mdmreportpy/docs/report-json-format.md)
  and
  [`.../docs/rich-text-format.md`](src/lib/mdmreadpy/src/lib/mdmreportpy/docs/rich-text-format.md)).
  Every reader, the diff tool, and every reporter defer to those two files as the master
  definition.

