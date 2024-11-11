@ECHO OFF

ECHO -
ECHO - MDM Diff. Starting...
ECHO -

REM set MDD file names
SET "MDD_A=p2401015_auto_20240729.mdd"
SET "MDD_B=p2401015_auto_20240806.mdd"






REM get reports
ECHO -
ECHO "- Getting report for MDD_A %MDD_A%"
SET "REPORT_A=report.%MDD_A%.json"
SET "REPORT_B=report.%MDD_B%.json"
mrscriptcl mdmrep.mrs "/a:INPUT_MDD=%MDD_A%" "/a:RUN_FEATURES=label,properties,translations"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )
python mdmcreatehtmlrep.py "%REPORT_A%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )
ECHO "- Getting report for MDD_B %MDD_B%"
mrscriptcl mdmrep.mrs "/a:INPUT_MDD=%MDD_B%" "/a:RUN_FEATURES=label,properties,translations"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )
python mdmcreatehtmlrep.py "%REPORT_B%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )





REM get diff
SET "REPORT_DIFF=report.diff-report.%MDD_A%-%MDD_B%.json"
ECHO -
ECHO - Calling the diff script
python mdmfinddiff.py "%REPORT_A%" "%REPORT_B%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )
::report.diff-report.{mdd_a}-{mdd_b}.json
python mdmcreatehtmlrep.py "%REPORT_DIFF%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )

ECHO -
ECHO - MDM Diff. Reached the end of script
ECHO -
