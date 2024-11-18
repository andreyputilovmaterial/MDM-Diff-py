@ECHO OFF


SET "MDD_A=examples\p221366_wave19.mdd"
SET "MDD_B=examples\p221366_v77.mdd"


set "MDD_A_JSON=%MDD_A%.json"
set "MDD_B_JSON=%MDD_B%.json"

@REM FOR /F "delims=" %%i IN ('python -c "import sys;from pathlib import Path;import re;inp_mdd_l = sys.argv[1];inp_mdd_r = sys.argv[2];report_part_mdd_left_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_l).name );report_part_mdd_right_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_r).name );report_filename = 'report.diff.{mdd_l}-{mdd_r}.json'.format(mdd_l=report_part_mdd_left_filename,mdd_r=report_part_mdd_right_filename);result_json_fname = ( Path(inp_mdd_l).parents[0] / report_filename );print(result_json_fname)" "%MDD_A%" "%MDD_B%"') DO SET "MDD_FINAL_DIFF_JSON=%%i"
FOR /F "delims=" %%i IN ('python dist/mdmtoolsap_bundle.py --program diff --cmp-scheme-left "%MDD_A_JSON%" --cmp-scheme-right "%MDD_B_JSON%" --norun-special-onlyprintoutputfilename') DO SET "MDD_FINAL_DIFF_JSON=%%i"


ECHO -
ECHO 1. read MDD A
ECHO read from: %MDD_A%
ECHO write to: .json
python src/lib/mdmreadpy/read_mdd.py --mdd "%MDD_A%" --config-features label,properties --config-section languages,shared_lists,fields
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 2. generate html
python src/lib/mdmreadpy/lib/mdmreportpy/report_create.py --inpfile "%MDD_A_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 3. read MDD B
ECHO read from: %MDD_B%
ECHO write to: .json
python src/lib/mdmreadpy/read_mdd.py --mdd "%MDD_B%" --config-features label,properties --config-section languages,shared_lists,fields
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 4. generate html
python src/lib/mdmreadpy/lib/mdmreportpy/report_create.py --inpfile "%MDD_B_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 5. diff
python src/find_mdm_diff.py --cmp-scheme-left "%MDD_A_JSON%" --cmp-scheme-right "%MDD_B_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 6. final html with diff!
python src/lib/mdmreadpy/lib/mdmreportpy/report_create.py --inpfile "%MDD_FINAL_DIFF_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 7 del .json temporary files
DEL "%MDD_A%.json"
@REM DEL "%MDD_A%.json.html"
DEL "%MDD_B%.json"
@REM DEL "%MDD_B%.json.html"
DEL "%MDD_FINAL_DIFF_JSON%"

ECHO done!

