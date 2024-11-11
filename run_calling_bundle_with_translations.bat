@ECHO OFF


SET "MDD_A=examples\p221366_wave19.mdd"
SET "MDD_B=examples\p221366_v77.mdd"


set "MDD_A_JSON=%MDD_A%.json"
set "MDD_B_JSON=%MDD_B%.json"

set "MDD_FINAL_DIFF_JSON=examples\report.diff.p221366_wave19.mdd-p221366_v77.mdd.json"


ECHO -
ECHO 1. read MDD A
ECHO read from: %MDD_A%
ECHO write to: .json
python dist/bundle.py --program read --mdd "%MDD_A%" --config-features label,properties,translations --config-section mdmproperties,languages,shared_lists,fields
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 2. generate html
python dist/bundle.py --program report --inpfile "%MDD_A_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 3. read MDD B
ECHO read from: %MDD_B%
ECHO write to: .json
python dist/bundle.py --program read --mdd "%MDD_B%" --config-features label,properties,translations --config-section mdmproperties,languages,shared_lists,fields
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 4. generate html
python dist/bundle.py --program report --inpfile "%MDD_B_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 5. diff
python dist/bundle.py --program diff --mdd_scheme_left "%MDD_A_JSON%" --mdd_scheme_right "%MDD_B_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 6. final html with diff!
python dist/bundle.py --program report --inpfile "%MDD_FINAL_DIFF_JSON%"
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

