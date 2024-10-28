@ECHO OFF


SET "MDD_A=examples\p221366_wave19.mdd"
SET "MDD_B=examples\p221366_v77.mdd"


set "MDD_A_JSON=%MDD_A%.json"
set "MDD_B_JSON=%MDD_B%.json"

set "MDD_FINAL_DIFF_JSON=examples\report.diff.p221366_wave19.mdd-p221366_v77.mdd.json"


@REM ECHO -
@REM ECHO 1. read MDD A
@REM ECHO read from: %MDD_A%
@REM ECHO write to: .json
@REM python lib\MDD-Read-py\read_mdd.py --mdd "%MDD_A%"
@REM if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

@REM ECHO -
@REM ECHO 2. generate html
@REM python lib\MDD-Read-py\lib\MDM-Report-py\report_create.py "%MDD_A_JSON%"
@REM if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

@REM ECHO -
@REM ECHO 3. read MDD B
@REM ECHO read from: %MDD_B%
@REM ECHO write to: .json
@REM python lib\MDD-Read-py\read_mdd.py --mdd "%MDD_B%"
@REM if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

@REM ECHO -
@REM ECHO 4. generate html
@REM python lib\MDD-Read-py\lib\MDM-Report-py\report_create.py "%MDD_B_JSON%"
@REM @REM if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 5. diff
python find_mdm_diff.py --mdd_scheme_left "%MDD_A_JSON%" --mdd_scheme_right "%MDD_B_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO 6. final html with diff!
python lib\MDD-Read-py\lib\MDM-Report-py\report_create.py "%MDD_FINAL_DIFF_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO done!

