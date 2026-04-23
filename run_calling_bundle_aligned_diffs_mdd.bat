@ECHO OFF
SETLOCAL enabledelayedexpansion


@REM put your files here
SET "MDD_WORKFLOW1_BEFORE=examples\p221366_wave19.mdd"
SET "MDD_WORKFLOW1_AFTER=examples\p221366_v77.mdd"

SET "MDD_WORKFLOW2_BEFORE=examples\p221366_wave19.mdd"
SET "MDD_WORKFLOW2_AFTER=examples\p221366_v77.mdd"




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
SET "MDD_WORKFLOW1_BEFORE_JSON=%MDD_WORKFLOW1_BEFORE%.json"
SET "MDD_WORKFLOW1_AFTER_JSON=%MDD_WORKFLOW1_AFTER%.json"

@REM FOR /F "delims=" %%i IN ('python -c "import sys;from pathlib import Path;import re;inp_mdd_l = sys.argv[1];inp_mdd_r = sys.argv[2];report_part_mdd_left_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_l).name );report_part_mdd_right_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_r).name );report_filename = 'report.diff.{mdd_l}-{mdd_r}.json'.format(mdd_l=report_part_mdd_left_filename,mdd_r=report_part_mdd_right_filename);result_json_fname = ( Path(inp_mdd_l).parents[0] / report_filename );print(result_json_fname)" "%MDD_WORKFLOW1_BEFORE%" "%MDD_WORKFLOW1_AFTER%"') DO SET "DIFF_WORKFLOW1_JSON=%%i"
FOR /F "delims=" %%i IN ('python dist/mdmtoolsap_bundle.py --program diff --cmp-scheme-left "%MDD_WORKFLOW1_BEFORE_JSON%" --cmp-scheme-right "%MDD_WORKFLOW1_AFTER_JSON%" --norun-special-onlyprintoutputfilename') DO SET "DIFF_WORKFLOW1_JSON=%%i"


ECHO -
ECHO 1. read MDD WORKFLOW1 BEFORE
ECHO read from: %MDD_WORKFLOW1_BEFORE%
ECHO write to: .json
python dist/mdmtoolsap_bundle.py --program read_mdd --mdd "%MDD_WORKFLOW1_BEFORE%" %MDD_READ_CONFIG_SETTINGS%
if !ERRORLEVEL! NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b !ERRORLEVEL! )

IF %CONFIG_PRODUCE_HTML_EACH_MDD% (
    ECHO -
    ECHO 2. generate html
    python dist/mdmtoolsap_bundle.py --program report --inpfile "%MDD_WORKFLOW1_BEFORE_JSON%"
    if !ERRORLEVEL! NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b !ERRORLEVEL! )
)

ECHO -
ECHO 3. read MDD WORKFLOW1 AFTER
ECHO read from: %MDD_WORKFLOW1_AFTER%
ECHO write to: .json
python dist/mdmtoolsap_bundle.py --program read_mdd --mdd "%MDD_WORKFLOW1_AFTER%" %MDD_READ_CONFIG_SETTINGS%
if !ERRORLEVEL! NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b !ERRORLEVEL! )

IF %CONFIG_PRODUCE_HTML_EACH_MDD% (
    ECHO -
    ECHO 4. generate html
    python dist/mdmtoolsap_bundle.py --program report --inpfile "%MDD_WORKFLOW1_AFTER_JSON%"
    if !ERRORLEVEL! NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b !ERRORLEVEL! )
)

ECHO -
ECHO 5. diff
python dist/mdmtoolsap_bundle.py --program diff --cmp-scheme-left "%MDD_WORKFLOW1_BEFORE_JSON%" --cmp-scheme-right "%MDD_WORKFLOW1_AFTER_JSON%" --output-filename "!DIFF_WORKFLOW1_JSON!" --config-casesensitive-item-list-comparison ignorecase --cmp-format structural --config-do-not-include-rows-moved
if !ERRORLEVEL! NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b !ERRORLEVEL! )

IF %CONFIG_PRODUCE_HTML_EACH_MDD% (
    ECHO -
    ECHO 6. html with diff!
    python dist/mdmtoolsap_bundle.py --program report --inpfile "%DIFF_WORKFLOW1_JSON%"
    if !ERRORLEVEL! NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b !ERRORLEVEL! )
)




REM :: file names with file schemes in json
SET "MDD_WORKFLOW2_BEFORE_JSON=%MDD_WORKFLOW2_BEFORE%.json"
SET "MDD_WORKFLOW2_AFTER_JSON=%MDD_WORKFLOW2_AFTER%.json"

@REM FOR /F "delims=" %%i IN ('python -c "import sys;from pathlib import Path;import re;inp_mdd_l = sys.argv[1];inp_mdd_r = sys.argv[2];report_part_mdd_left_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_l).name );report_part_mdd_right_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_r).name );report_filename = 'report.diff.{mdd_l}-{mdd_r}.json'.format(mdd_l=report_part_mdd_left_filename,mdd_r=report_part_mdd_right_filename);result_json_fname = ( Path(inp_mdd_l).parents[0] / report_filename );print(result_json_fname)" "%MDD_WORKFLOW2_BEFORE%" "%MDD_WORKFLOW2_AFTER%"') DO SET "DIFF_WORKFLOW2_JSON=%%i"
FOR /F "delims=" %%i IN ('python dist/mdmtoolsap_bundle.py --program diff --cmp-scheme-left "%MDD_WORKFLOW2_BEFORE_JSON%" --cmp-scheme-right "%MDD_WORKFLOW2_AFTER_JSON%" --norun-special-onlyprintoutputfilename') DO SET "DIFF_WORKFLOW2_JSON=%%i"


ECHO -
ECHO 7. read MDD WORKFLOW2 BEFORE
ECHO read from: %MDD_WORKFLOW2_BEFORE%
ECHO write to: .json
python dist/mdmtoolsap_bundle.py --program read_mdd --mdd "%MDD_WORKFLOW2_BEFORE%" %MDD_READ_CONFIG_SETTINGS%
if !ERRORLEVEL! NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b !ERRORLEVEL! )

IF %CONFIG_PRODUCE_HTML_EACH_MDD% (
    ECHO -
    ECHO 8. generate html
    python dist/mdmtoolsap_bundle.py --program report --inpfile "%MDD_WORKFLOW2_BEFORE_JSON%"
    if !ERRORLEVEL! NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b !ERRORLEVEL! )
)

ECHO -
ECHO 9. read MDD WORKFLOW2 AFTER
ECHO read from: %MDD_WORKFLOW2_AFTER%
ECHO write to: .json
python dist/mdmtoolsap_bundle.py --program read_mdd --mdd "%MDD_WORKFLOW2_AFTER%" %MDD_READ_CONFIG_SETTINGS%
if !ERRORLEVEL! NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b !ERRORLEVEL! )

IF %CONFIG_PRODUCE_HTML_EACH_MDD% (
    ECHO -
    ECHO 10. generate html
    python dist/mdmtoolsap_bundle.py --program report --inpfile "%MDD_WORKFLOW2_AFTER_JSON%"
    if !ERRORLEVEL! NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b !ERRORLEVEL! )
)

ECHO -
ECHO 11. diff
python dist/mdmtoolsap_bundle.py --program diff --cmp-scheme-left "%MDD_WORKFLOW2_BEFORE_JSON%" --cmp-scheme-right "%MDD_WORKFLOW2_AFTER_JSON%" --output-filename "!DIFF_WORKFLOW2_JSON!" --config-casesensitive-item-list-comparison ignorecase --cmp-format structural --config-do-not-include-rows-moved
if !ERRORLEVEL! NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b !ERRORLEVEL! )

IF %CONFIG_PRODUCE_HTML_EACH_MDD% (
    ECHO -
    ECHO 12. html with diff!
    python dist/mdmtoolsap_bundle.py --program report --inpfile "%DIFF_WORKFLOW2_JSON%"
    if !ERRORLEVEL! NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b !ERRORLEVEL! )
)




ECHO -
ECHO 13. FINAL DIFF

@REM FOR /F "delims=" %%i IN ('python -c "import sys;from pathlib import Path;import re;inp_mdd_l = sys.argv[1];inp_mdd_r = sys.argv[2];report_part_mdd_left_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_l).name );report_part_mdd_right_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_r).name );report_filename = 'report.diff.{mdd_l}-{mdd_r}.json'.format(mdd_l=report_part_mdd_left_filename,mdd_r=report_part_mdd_right_filename);result_json_fname = ( Path(inp_mdd_l).parents[0] / report_filename );print(result_json_fname)" "%MDD_WORKFLOW2_BEFORE%" "%MDD_WORKFLOW2_AFTER%"') DO SET "DIFF_WORKFLOW2_JSON=%%i"
FOR /F "delims=" %%i IN ('python dist/mdmtoolsap_bundle.py --program diff --cmp-scheme-left "%DIFF_WORKFLOW1_JSON%" --cmp-scheme-right "%DIFF_WORKFLOW2_JSON%" --norun-special-onlyprintoutputfilename') DO SET "DIFF_FINAL_JSON=%%i"

python dist/mdmtoolsap_bundle.py --program diff --cmp-scheme-left "%DIFF_WORKFLOW1_JSON%" --cmp-scheme-right "%DIFF_WORKFLOW2_JSON%" --output-filename "!DIFF_FINAL_JSON!" --config-casesensitive-item-list-comparison ignorecase
if !ERRORLEVEL! NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b !ERRORLEVEL! )


ECHO -
ECHO 14. final html with diff!
python dist/mdmtoolsap_bundle.py --program report --inpfile "%DIFF_FINAL_JSON%"
if !ERRORLEVEL! NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b !ERRORLEVEL! )











ECHO -
ECHO 999 del .json temporary files
DEL "!MDD_WORKFLOW1_BEFORE!.json"
@REM DEL "!MDD_WORKFLOW1_BEFORE!.json.html"
DEL "!MDD_WORKFLOW1_AFTER!.json"
@REM DEL "!MDD_WORKFLOW1_AFTER!.json.html"
DEL "!DIFF_WORKFLOW1_JSON!"
DEL "!MDD_WORKFLOW2_BEFORE!.json"
@REM DEL "!MDD_WORKFLOW2_BEFORE!.json.html"
DEL "!MDD_WORKFLOW2_AFTER!.json"
@REM DEL "!MDD_WORKFLOW2_AFTER!.json.html"
DEL "!DIFF_WORKFLOW2_JSON!"
DEL "!DIFF_FINAL_JSON!"

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
exit /b !ERRORLEVEL!

