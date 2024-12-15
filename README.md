# MDM-Diff-py
A new iteration of diff between MDD files, much cleaner, all in python. No mrs vbscript code and much less js, all should be in python

## How to start it
To get it running you only need mdmtoolsap.py and run_mdd_diff.bat. Just find the most recent release and download these 2 files.

Edit the BAT file and insert your MDD file names at the top.

You obviously need some dependencies - python, IBM Professional... Just standard things.

## Frequently asked questions
* Q: What do I need to run this?<br />A: You need python environment (any modern version) and IBM (Unicom) software that shoud be installed on your machine by default (you don't even need Unicom if you are not producing any outputs from MDD files)
* Q: Why the chosen language is python?<br />A: I can't write it all in mrs scripts in VBScript. This language is too limited and too stupid. So I had to go for some other alternative, and python is fine, it's a simple scripting language and it has all necessary dependencies. My earier attempts were to keep code partially in mrs scripts but then I realized everything can be done in python so it's easier to opt for one single language. Also I have some additions in JS but this is designed itentionally to add some unnecessary code that runs separately just to beautify the page at the very last stage, add more control over it, add the ability to show or hide columns. But all JS here is unnecessary and can be removed for simplification
* Q: Why are you doing this?<br />A: Everyone has some hobbies. I am not doing it at work/labor time. I find it interesting to find what we can do. It's some demonstrator of technologies. Maybe saying "tech" sounds too loud when I did not actually invent anything outstanding here - I am just reading fields utilizing existing API and writing it to HTML - nothing extraordinary - but I believe it can be developed to more sophisticated shapes.

## For End Users: how to debug?
Ok, you are starting the tool and it crashes. Error messages report some problem and line number but you don't know where to check - where do you find that line number? Ok, there's a solution. Open mdmtoolsap_bundle.py and change CONFIG_VERBOSE to True (twice). Run the tool again. Ok, nothing changed, it crashes, it reportes the line number. But now you have modules saved in the same working folder where you start the script. So you can find the line number and see what is going on!

Besides that, I tried to make error messages very descriptive, reporting anything that is going on not really well. I am also printing blocks where it happened - row names, seciton names... so that it's easy to understand what's causing the problem.

## For developers: how to build distributable files?
There is a script, build.bat

You need pinliner to run this, but the version found on internet was not working well for me. I made certain fixes, please use my personal pinliner version (inluded in src-make folder, so this is a part of the distribution).

Everything else that is going on can be clearly found in the build.bat script - the bundle created is renamed to mdmtoolsap_bundle, couple more lines are added to get it running, the bat files are renamed, and the path to bundle is changed to mdmtoolsap_bundle within those bat files. Results are in dist/ subdirectory.

## Biggest problems of this tool
Ok we are here to talk about downsides.<br />I believe most important concerns are the following:
* It can't handle everything. Yeah the tool is nice but I still want more from it
* Memory consumptoion of large html reports.<br />Actually I did not look at it in very close detail but it looks the problem is just the number of rows and columns, just the whole size of tables. My code includes some js but it looks it does not make things much worse - the opposite - I am hiding certain sections and columns and it's making the page more efficient. I also tried to color some outputs more but it increases memory consumption a lot. The solution could be to select what we need more carefully, only show the necessary parts, not the whole content. The other solution could be to develop some sophisticated framework with ajax-loaded content and only load the visible part. But this is a different level of development, I wanted to keep this thing simple.
* The price for support<br />I always wanted to keep this tool simple, but unfortunately I am actively using it and I always want something more, to see this tool smarter, to detect columns better, rows better, and having all different types of inputs - excel tabs of very different format, mdds from wa and from live projects, table scripts, dms code, etc... - the number of lines of code is growing and growing. I can handle it, not problem, it's easy for me. But this is growing out of limits that a different person can easily understand.
