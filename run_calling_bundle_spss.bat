@ECHO OFF
SETLOCAL enabledelayedexpansion


@REM :: link your files here
SET "SPSS_A=examples\p221366_wave19.spss"
SET "SPSS_B=examples\p221366_v77.spss"




@REM :: adjust config options per your needs
@REM :: when using "if" in BAT files, "1==1" is true and "1==0" is false

@REM :: should we also compare data?
@REM :: Warning, performance is poor, I don't recommend, even in small projects
SET "CONFIG_INCLUDE_DATA=1==0"

@REM :: if we do include data comparison, we have to provide which variable should be used as an ID
SET "CONFIG_ID_KEY_VARIABLE=Respondent_ID"

@REM :: do we need to create HTML with SPSS markup?
@REM :: on one side, you can see variables and labels, on the other side, you can see the same, and much more, in IBM SPSS Statistics
@REM :: so you probably don't need it
SET "CONFIG_PRODUCE_HTML_EACH_SPSS=1==0"








@REM :: default is true, I recommend including variabes, that's what we compare, that's why this tool exists
SET "CONFIG_INCLUDE_VARIABLES_META=1==1"

@REM :: default is true, I recommend including variabes, that's what we compare, that's why this tool exists
SET "CONFIG_INCLUDE_VALUELABELS_META=1==1"





REM :: prepare helper config strings
SET "SPSS_READ_CONFIG=@"
IF %CONFIG_INCLUDE_VARIABLES_META% ( SET "SPSS_READ_CONFIG=!SPSS_READ_CONFIG! --config-read-variables yes" ) ELSE ( SET "SPSS_READ_CONFIG=!SPSS_READ_CONFIG! --config-read-variables no" )
IF %CONFIG_INCLUDE_VALUELABELS_META% ( SET "SPSS_READ_CONFIG=!SPSS_READ_CONFIG! --config-read-value-labels yes" ) ELSE ( SET "SPSS_READ_CONFIG=!SPSS_READ_CONFIG! --config-read-value-labels no" )
IF %CONFIG_INCLUDE_DATA% ( SET "SPSS_READ_CONFIG=!SPSS_READ_CONFIG! --config-read-data yes" ) ELSE ( SET "SPSS_READ_CONFIG=!SPSS_READ_CONFIG! --config-read-data no" )

IF %CONFIG_INCLUDE_DATA% ( IF "%CONFIG_ID_KEY_VARIABLE%"=="" ( ECHO "id_key not specified" ) ELSE ( SET "SPSS_READ_CONFIG=!SPSS_READ_CONFIG! --id-key !CONFIG_ID_KEY_VARIABLE!" ) )

SET "SPSS_READ_CONFIG=!SPSS_READ_CONFIG:@,=!"


REM :: file names with file schemes in json
SET "SPSS_A_JSON=%SPSS_A%.json"
SET "SPSS_B_JSON=%SPSS_B%.json"

@REM FOR /F "delims=" %%i IN ('python -c "import sys;from pathlib import Path;import re;inp_mdd_l = sys.argv[1];inp_mdd_r = sys.argv[2];report_part_mdd_left_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_l).name );report_part_mdd_right_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_r).name );report_filename = 'report.diff.{mdd_l}-{mdd_r}.json'.format(mdd_l=report_part_mdd_left_filename,mdd_r=report_part_mdd_right_filename);result_json_fname = ( Path(inp_mdd_l).parents[0] / report_filename );print(result_json_fname)" "%SPSS_A%" "%SPSS_B%"') DO SET "SPSS_FINAL_DIFF_JSON=%%i"
FOR /F "delims=" %%i IN ('python dist/mdmtoolsap_bundle.py --program diff --cmp-scheme-left "%SPSS_A_JSON%" --cmp-scheme-right "%SPSS_B_JSON%" --norun-special-onlyprintoutputfilename') DO SET "SPSS_FINAL_DIFF_JSON=%%i"


ECHO -
ECHO 1. read SPSS A
ECHO read from: %SPSS_A%
ECHO write to: .json
python dist/mdmtoolsap_bundle.py --program read_spss --inpfile "%SPSS_A%" %SPSS_READ_CONFIG%
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

IF %CONFIG_PRODUCE_HTML_EACH_SPSS% (
    ECHO -
    ECHO 2. generate html
    python dist/mdmtoolsap_bundle.py --program report --inpfile "%SPSS_A_JSON%"
    if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )
)

ECHO -
ECHO 3. read SPSS B
ECHO read from: %SPSS_B%
ECHO write to: .json
python dist/mdmtoolsap_bundle.py --program read_spss --inpfile "%SPSS_B%" %SPSS_READ_CONFIG%
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

IF %CONFIG_PRODUCE_HTML_EACH_SPSS% (
    ECHO -
    ECHO 4. generate html
    python dist/mdmtoolsap_bundle.py --program report --inpfile "%SPSS_B_JSON%"
    if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )
)

ECHO -
ECHO 5. diff
python dist/mdmtoolsap_bundle.py --program diff --cmp-scheme-left "%SPSS_A_JSON%" --cmp-scheme-right "%SPSS_B_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

ECHO -
ECHO 6. final html with diff!
python dist/mdmtoolsap_bundle.py --program report --inpfile "%SPSS_FINAL_DIFF_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

ECHO -
ECHO 7 del .json temporary files
DEL "%SPSS_A%.json"
@REM DEL "%SPSS_A%.json.html"
DEL "%SPSS_B%.json"
@REM DEL "%SPSS_B%.json.html"
DEL "%SPSS_FINAL_DIFF_JSON%"

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

