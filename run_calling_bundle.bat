@ECHO OFF


SET "MDD_A=examples\p221366_wave19.mdd"
SET "MDD_B=examples\p221366_v77.mdd"


set "MDD_A_JSON=%MDD_A%.json"
set "MDD_B_JSON=%MDD_B%.json"

FOR /F "delims=" %%i IN ('python -c "import sys;from pathlib import Path;import re;inp_mdd_l = sys.argv[1];inp_mdd_r = sys.argv[2];report_part_mdd_left_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_l).name );report_part_mdd_right_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_r).name );report_filename = 'report.diff.{mdd_l}-{mdd_r}.json'.format(mdd_l=report_part_mdd_left_filename,mdd_r=report_part_mdd_right_filename);result_json_fname = ( Path(inp_mdd_l).parents[0] / report_filename );print(result_json_fname)" "%MDD_A%" "%MDD_B%"') DO SET "MDD_FINAL_DIFF_JSON=%%i"


ECHO -
ECHO 1. read MDD A
ECHO read from: %MDD_A%
ECHO write to: .json
python dist/mdmtoolsap_bundle.py --program read --mdd "%MDD_A%" --config-features label,attributes,properties --config-section languages,shared_lists,fields,pages
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

ECHO -
ECHO 2. generate html
python dist/mdmtoolsap_bundle.py --program report --inpfile "%MDD_A_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

ECHO -
ECHO 3. read MDD B
ECHO read from: %MDD_B%
ECHO write to: .json
python dist/mdmtoolsap_bundle.py --program read --mdd "%MDD_B%" --config-features label,attributes,properties --config-section languages,shared_lists,fields,pages
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

ECHO -
ECHO 4. generate html
python dist/mdmtoolsap_bundle.py --program report --inpfile "%MDD_B_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

ECHO -
ECHO 5. diff
python dist/mdmtoolsap_bundle.py --program diff --mdd_scheme_left "%MDD_A_JSON%" --mdd_scheme_right "%MDD_B_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

ECHO -
ECHO 6. final html with diff!
python dist/mdmtoolsap_bundle.py --program report --inpfile "%MDD_FINAL_DIFF_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

ECHO -
ECHO 7 del .json temporary files
DEL "%MDD_A%.json"
@REM DEL "%MDD_A%.json.html"
DEL "%MDD_B%.json"
@REM DEL "%MDD_B%.json.html"
DEL "%MDD_FINAL_DIFF_JSON%"

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

