# MDM-Diff-py
A new iteration of diff between MDD files, Excel files (wow!), SPSS (inluding only columns/variables, or also data), Tab Scripts, DMS, Text and many more formats. All in python. No mrs vbscript code and much less js.

## How to start it
Download mdmtoolsap_bundle.py and a BAT for your file type file from
[Releases](../../releases/latest).

Edit the BAT file and insert paths to compared files.

You obviously need some dependencies - python, IBM Professional... Just standard things.

### On necessary dependencies and ms markitdown
If you don't need to read input files with ms markitdown, dependencies are minimal. You just won't be able to use that ms markitdown way of reading files. Actually, ms markitdown is quite powerful - using it, you can read, html, excel, pdf, images, transcribed audio, etc. But it has a lot of dependencies now (it was much simpler is earlier versions), including openai libraries, azure-ai-documentintelligence, etc... Ms markitdown now comes with docker file - a different way of running the scripts - it is supposed that you create a run a container with python code. This diff tool was initially started as a simple script, so I am not sure if it worth it installing all these complicated dependencies without version control on your local machine.

## Frequently asked questions
* Q: What do I need to run this?<br />A: You need python environment (any modern version) and IBM (Unicom) software that shoud be installed on your machine by default (you don't even need Unicom if you are not producing any outputs from MDD files)
* Q: Why the chosen language is python?<br />A: I can't write it all in mrs scripts in VBScript. This language is too limited and too stupid. So I had to go for some other alternative, and python is fine, it's a simple scripting language and it has all necessary dependencies. My earier attempts were to keep code partially in mrs scripts but then I realized everything can be done in python so it's easier to opt for one single language. Also I have some additions in JS but this is designed itentionally to add some unnecessary code that runs separately just to beautify the page at the very last stage, add more control over it, add the ability to show or hide columns. But all JS here is unnecessary and can be removed for simplification
* Q: Why are you doing this?<br />A: Everyone has some hobbies. I am not doing it at work/labor time. I find it interesting to find what we can do. It's some demonstrator of technologies. Maybe saying "tech" sounds too loud when I did not actually invent anything outstanding here - I am just reading fields utilizing existing API and writing it to HTML - nothing extraordinary - but I believe it can be developed to more sophisticated shapes.

## Which types of files can be compared?
* MDD files. That's why this tool was invented. It can also compare it with routing or with translations. It is configurable, it can handle.
* Excel tabs. This is maybe even more important than comparing MDDs
* SPSS - I suggest only comparing metadata (columns/variables and category analysis values) and not comparing data (this can be configured from within BAT file) because the results are printed in html page - if you include data - the page would probably be too big to load in browser, even in smallest projects. However, the tool is capable of reading and comparing SPSS file contents.
* Any text files, including tab scripts and dms scripts. I highly recommend using it for DA exports
* Any pdf, ppts, word, xlsx, even transcripted audio or images - everything that can be read with ms markitdown (WARNING: see a note above on "On necessary dependencies and ms markitdown")

## For End Users: how to debug?
Ok, you are starting the tool and it crashes. Error messages report some problem and line number but you don't know where to check - where do you find that line number? Ok, there's a solution. Open mdmtoolsap_bundle.py and change CONFIG_VERBOSE to True (twice). Run the tool again. Ok, nothing changed, it crashes, it reportes the line number. But now you have modules saved in the same working folder where you start the script. So you can find the line number and see what is going on!

Besides that, I tried to make error messages very descriptive, reporting anything that is going on not really well. I am also printing blocks where it happened - row names, seciton names... so that it's easy to understand what's causing the problem.

## For developers: how to build distributable files?
There is a script, build.bat

You need pinliner to run this, but the version found on internet was not working well for me. I made certain fixes, please use my personal pinliner version (inluded in src-make folder, so this is a part of the distribution).

Everything else that is going on can be clearly found in the build.bat script - the bundle created is renamed to mdmtoolsap_bundle, couple more lines are added to get it running, the bat files are renamed, and the path to bundle is changed to mdmtoolsap_bundle within those bat files. Results are in dist/ subdirectory.

