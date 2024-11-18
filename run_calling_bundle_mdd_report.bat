@ECHO OFF


SET "MDD_A=examples\p221366_wave19.mdd"


set "MDD_A_JSON=%MDD_A%.json"


ECHO -
ECHO 1. read MDD A
ECHO read from: %MDD_A%
ECHO write to: .json
python dist/mdmtoolsap_bundle.py --program read_mdd --mdd "%MDD_A%" --config-features label,attributes,properties,translations --config-section languages,shared_lists,fields,pages
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

ECHO -
ECHO 2. generate html
python dist/mdmtoolsap_bundle.py --program report --inpfile "%MDD_A_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

ECHO -
ECHO 7 del .json temporary files
DEL "%MDD_A%.json"
@REM DEL "%MDD_A%.json.html"
DEL "%MDD_B%.json"
@REM DEL "%MDD_B%.json.html"
@REM DEL "%MDD_FINAL_DIFF_JSON%"

ECHO -
:CLEANUP
ECHO 999. Clean up
REM REM :: comment: just deleting trach .pyc files after the execution - they are saved when modules are loaded from within bndle file created with pinliner
REM REM :: however, it is necessary to delete these .pyc files before every call of the mdmtoolsap_bundle
REM REM :: it means, 6 more times here, in this script; but I don't do it cause I have this added to the linliner code - see my pinliner fork
DEL *.pyc
IF EXIST __pycache__ (
DEL /F /Q __pycache__\*
)
IF EXIST __pycache__ (
RMDIR /Q /S __pycache__
)

ECHO done!
exit /b %errorlevel%

