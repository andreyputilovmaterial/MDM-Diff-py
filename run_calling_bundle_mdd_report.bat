@ECHO OFF


SET "MDD_A=examples\p221366_wave19.mdd"


set "MDD_A_JSON=%MDD_A%.json"


ECHO -
ECHO 1. read MDD A
ECHO read from: %MDD_A%
ECHO write to: .json
python dist/bundle.py --program read --mdd "%MDD_A%" --config-features label,properties --config-section mdmproperties,languages,shared_lists,fields
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 2. generate html
python dist/bundle.py --program report --inpfile "%MDD_A_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 999. Clean up
REM REM :: comment: just deleting trach .pyc files after the execution - they are saved when modules are loaded from within bndle file created with pinliner
REM REM :: however, it is necessary to delete these .pyc files before every call of the bundle
REM REM :: it means, 6 more times here, in this script; but I don't do it cause I have this added to the linliner code - see my pinliner fork
DEL *.pyc
IF EXIST __pycache__ (
DEL /F /Q __pycache__\*
)
IF EXIST __pycache__ (
RMDIR /Q /S __pycache__
)

ECHO done!

