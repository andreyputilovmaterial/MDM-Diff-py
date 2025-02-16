@ECHO OFF
SETLOCAL enabledelayedexpansion


@REM put your files here
SET "MDD_A=examples\p221366_wave19.mdd"
SET "MDD_B=examples\p221366_v77.mdd"




@REM adjust config options per your needs
@REM when using "if" in BAT files, "1==1" is true and "1==0" is false
SET "CONFIG_INCLUDE_SHAREDLISTS=1==1"
SET "CONFIG_INCLUDE_LANGUAGES=1==1"
SET "CONFIG_INCLUDE_PAGES=1==1"
SET "CONFIG_INCLUDE_ROUTING=1==1"
SET "CONFIG_INCLUDE_SCRIPTING=1==1"
SET "CONFIG_INCLUDE_TRANSLATIONS=1==0"

SET "CONFIG_INCLUDE_CUSTOMPROPERTIES=1==1"
SET "CONFIG_INCLUDE_ATTRIBUTES=1==1"
SET "CONFIG_INCLUDE_LABELS=1==1"

SET "CONFIG_PRODUCE_HTML_EACH_MDD=1==0"

SET "CONFIG_SHAREDLISTS_STEPINTO=1==0"







REM :: prepare helper config strings
SET "MDD_READ_CONFIG_FEATURELIST=@"
IF %CONFIG_INCLUDE_LABELS% ( SET "MDD_READ_CONFIG_FEATURELIST=!MDD_READ_CONFIG_FEATURELIST!,label" )
IF %CONFIG_INCLUDE_ATTRIBUTES% ( SET "MDD_READ_CONFIG_FEATURELIST=!MDD_READ_CONFIG_FEATURELIST!,attributes" )
IF %CONFIG_INCLUDE_CUSTOMPROPERTIES% ( SET "MDD_READ_CONFIG_FEATURELIST=!MDD_READ_CONFIG_FEATURELIST!,properties" )
IF %CONFIG_INCLUDE_TRANSLATIONS% ( SET "MDD_READ_CONFIG_FEATURELIST=!MDD_READ_CONFIG_FEATURELIST!,translations" )
IF %CONFIG_INCLUDE_SCRIPTING% ( SET "MDD_READ_CONFIG_FEATURELIST=!MDD_READ_CONFIG_FEATURELIST!,scripting" )
SET "MDD_READ_CONFIG_FEATURELIST=!MDD_READ_CONFIG_FEATURELIST:@,=!"

SET "MDD_READ_CONFIG_SECTIONLIST=@"
IF %CONFIG_INCLUDE_LANGUAGES% ( SET "MDD_READ_CONFIG_SECTIONLIST=!MDD_READ_CONFIG_SECTIONLIST!,languages" )
IF %CONFIG_INCLUDE_SHAREDLISTS% ( SET "MDD_READ_CONFIG_SECTIONLIST=!MDD_READ_CONFIG_SECTIONLIST!,shared_lists" )
IF 1==1 ( SET "MDD_READ_CONFIG_SECTIONLIST=!MDD_READ_CONFIG_SECTIONLIST!,fields" )
IF %CONFIG_INCLUDE_PAGES% ( SET "MDD_READ_CONFIG_SECTIONLIST=!MDD_READ_CONFIG_SECTIONLIST!,pages" )
IF %CONFIG_INCLUDE_ROUTING% ( SET "MDD_READ_CONFIG_SECTIONLIST=!MDD_READ_CONFIG_SECTIONLIST!,routing" )
SET "MDD_READ_CONFIG_SECTIONLIST=!MDD_READ_CONFIG_SECTIONLIST:@,=!"

SET "MDD_READ_CONFIG_SETTINGS="
IF %CONFIG_SHAREDLISTS_STEPINTO% (
    SET MDD_READ_CONFIG_SETTINGS=!MDD_READ_CONFIG_SETTINGS! --config-sharedlists-listcats stepinto
) ELSE (
    SET MDD_READ_CONFIG_SETTINGS=!MDD_READ_CONFIG_SETTINGS! --config-sharedlists-listcats stepover
)
SET MDD_READ_CONFIG_SETTINGS=!MDD_READ_CONFIG_SETTINGS!  --config-features %MDD_READ_CONFIG_FEATURELIST% --config-section %MDD_READ_CONFIG_SECTIONLIST%


REM :: file names with file schemes in json
SET "MDD_A_JSON=%MDD_A%.json"
SET "MDD_B_JSON=%MDD_B%.json"

@REM FOR /F "delims=" %%i IN ('python -c "import sys;from pathlib import Path;import re;inp_mdd_l = sys.argv[1];inp_mdd_r = sys.argv[2];report_part_mdd_left_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_l).name );report_part_mdd_right_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_r).name );report_filename = 'report.diff.{mdd_l}-{mdd_r}.json'.format(mdd_l=report_part_mdd_left_filename,mdd_r=report_part_mdd_right_filename);result_json_fname = ( Path(inp_mdd_l).parents[0] / report_filename );print(result_json_fname)" "%MDD_A%" "%MDD_B%"') DO SET "MDD_FINAL_DIFF_JSON=%%i"
FOR /F "delims=" %%i IN ('python src/run_universal.py --program diff --cmp-scheme-left "%MDD_A_JSON%" --cmp-scheme-right "%MDD_B_JSON%" --norun-special-onlyprintoutputfilename') DO SET "MDD_FINAL_DIFF_JSON=%%i"


ECHO -
ECHO 1. read MDD A
ECHO read from: %MDD_A%
ECHO write to: .json
python src/run_universal.py --program read_mdd --mdd "%MDD_A%" %MDD_READ_CONFIG_SETTINGS%
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

IF %CONFIG_PRODUCE_HTML_EACH_MDD% (
    ECHO -
    ECHO 2. generate html
    python src/run_universal.py --program report --inpfile "%MDD_A_JSON%"
    if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )
)

ECHO -
ECHO 3. read MDD B
ECHO read from: %MDD_B%
ECHO write to: .json
python src/run_universal.py --program read_mdd --mdd "%MDD_B%" %MDD_READ_CONFIG_SETTINGS%
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

IF %CONFIG_PRODUCE_HTML_EACH_MDD% (
    ECHO -
    ECHO 4. generate html
    python src/run_universal.py --program report --inpfile "%MDD_B_JSON%"
    if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )
)

ECHO -
ECHO 5. diff
python src/run_universal.py --program diff --cmp-scheme-left "%MDD_A_JSON%" --cmp-scheme-right "%MDD_B_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

ECHO -
ECHO 6. final html with diff!
python src/run_universal.py --program report --inpfile "%MDD_FINAL_DIFF_JSON%"
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

