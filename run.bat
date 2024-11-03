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
python lib\MDD-Read-py\read_mdd.py --mdd "%MDD_A%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 2. generate html
python lib\MDD-Read-py\lib\MDM-Report-py\report_create.py "%MDD_A_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 3. read MDD B
ECHO read from: %MDD_B%
ECHO write to: .json
python lib\MDD-Read-py\read_mdd.py --mdd "%MDD_B%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 4. generate html
python lib\MDD-Read-py\lib\MDM-Report-py\report_create.py "%MDD_B_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 5. diff
python find_mdm_diff.py --mdd_scheme_left "%MDD_A_JSON%" --mdd_scheme_right "%MDD_B_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 6. final html with diff!
python lib\MDD-Read-py\lib\MDM-Report-py\report_create.py "%MDD_FINAL_DIFF_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO done!

