@ECHO OFF


SET "TEXTFILE_A=prepdatadms.dms"
SET "TEXTFILE_B=prepdatadms.txt"


set "TEXTFILE_A_JSON=%TEXTFILE_A%.json"
set "TEXTFILE_B_JSON=%TEXTFILE_B%.json"

@REM FOR /F "delims=" %%i IN ('python -c "import sys;from pathlib import Path;import re;inp_mdd_l = sys.argv[1];inp_mdd_r = sys.argv[2];report_part_mdd_left_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_l).name );report_part_mdd_right_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_r).name );report_filename = 'report.diff.{mdd_l}-{mdd_r}.json'.format(mdd_l=report_part_mdd_left_filename,mdd_r=report_part_mdd_right_filename);result_json_fname = ( Path(inp_mdd_l).parents[0] / report_filename );print(result_json_fname)" "%TEXTFILE_A%" "%TEXTFILE_B%"') DO SET "TEXTFILE_FINAL_DIFF_JSON=%%i"
FOR /F "delims=" %%i IN ('python dist/mdmtoolsap_bundle.py --program diff --cmp-scheme-left "%TEXTFILE_A_JSON%" --cmp-scheme-right "%TEXTFILE_B_JSON%" --norun-special-onlyprintoutputfilename') DO SET "TEXTFILE_FINAL_DIFF_JSON=%%i"


ECHO -
ECHO 1. read FILE A
ECHO read from: %TEXTFILE_A%
ECHO write to: .json
@REM python -c "import sys;from pathlib import Path;import re;import argparse;import json;from datetime import datetime, timezone;data=json.loads('{ ""report_type"": ""TextFile"", ""source_file"": ""insert"", ""report_datetime_utc"": ""insert"", ""report_datetime_local"": ""insert"", ""source_file_metadata"": [ ], ""report_scheme"": { ""columns"": [ ""rawtextcontents"" ], ""column_headers"": { ""rawtextcontents"": ""File Contents"" }, ""flags"": [] }, ""sections"": [ { ""name"": ""filecontents"", ""content"": [ { ""name"": """", ""rawtextcontents"": ""insert"" } ] } ] }');parser = argparse.ArgumentParser();parser.add_argument( '--inpfile' );args = parser.parse_args();inp_file = Path(args.inpfile);data['source_file']='{f}'.format(f=inp_file);data['report_datetime_utc']='{f}'.format(f=(datetime.now()).astimezone(tz=timezone.utc).strftime('%%Y-%%m-%%dT%%H:%%M:%%SZ'),);data['report_datetime_local']='{f}'.format(f=(datetime.now()).strftime('%%Y-%%m-%%dT%%H:%%M:%%SZ'));inp_file_obj=open(inp_file,'r');filecontents=inp_file_obj.read();data['sections'][0]['content'][0]['rawtextcontents']=filecontents;result_json_fname = ( Path(inp_file).parents[0] / '{basename}{ext}'.format(basename=Path(inp_file).name,ext='.json') if Path(inp_file).is_file() else re.sub(r'^\s*?(.*?)\s*?$',lambda m: '{base}{added}'.format(base=m[1],added='.json'),'{path}'.format(path=inp_file)) );outfile = open(result_json_fname, 'w');outfile.write(json.dumps(data))" --inpfile "%TEXTFILE_A%"
python dist/mdmtoolsap_bundle.py --program read_txt --inpfile "%TEXTFILE_A%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

@REM ECHO -
@REM ECHO 2. generate html
@REM python dist/mdmtoolsap_bundle.py --program report --inpfile "%TEXTFILE_A_JSON%"
@REM if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

ECHO -
ECHO 3. read FILE B
ECHO read from: %TEXTFILE_B%
ECHO write to: .json
@REM python -c "import sys;from pathlib import Path;import re;import argparse;import json;from datetime import datetime, timezone;data=json.loads('{ ""report_type"": ""TextFile"", ""source_file"": ""insert"", ""report_datetime_utc"": ""insert"", ""report_datetime_local"": ""insert"", ""source_file_metadata"": [ ], ""report_scheme"": { ""columns"": [ ""rawtextcontents"" ], ""column_headers"": { ""rawtextcontents"": ""File Contents"" }, ""flags"": [] }, ""sections"": [ { ""name"": ""filecontents"", ""content"": [ { ""name"": """", ""rawtextcontents"": ""insert"" } ] } ] }');parser = argparse.ArgumentParser();parser.add_argument( '--inpfile' );args = parser.parse_args();inp_file = Path(args.inpfile);data['source_file']='{f}'.format(f=inp_file);data['report_datetime_utc']='{f}'.format(f=(datetime.now()).astimezone(tz=timezone.utc).strftime('%%Y-%%m-%%dT%%H:%%M:%%SZ'),);data['report_datetime_local']='{f}'.format(f=(datetime.now()).strftime('%%Y-%%m-%%dT%%H:%%M:%%SZ'));inp_file_obj=open(inp_file,'r');filecontents=inp_file_obj.read();data['sections'][0]['content'][0]['rawtextcontents']=filecontents;result_json_fname = ( Path(inp_file).parents[0] / '{basename}{ext}'.format(basename=Path(inp_file).name,ext='.json') if Path(inp_file).is_file() else re.sub(r'^\s*?(.*?)\s*?$',lambda m: '{base}{added}'.format(base=m[1],added='.json'),'{path}'.format(path=inp_file)) );outfile = open(result_json_fname, 'w');outfile.write(json.dumps(data))" --inpfile "%TEXTFILE_B%"
python dist/mdmtoolsap_bundle.py --program read_txt --inpfile "%TEXTFILE_B%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

@REM ECHO -
@REM ECHO 4. generate html
@REM python dist/mdmtoolsap_bundle.py --program report --inpfile "%TEXTFILE_B_JSON%"
@REM if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

ECHO -
ECHO 5. diff
python dist/mdmtoolsap_bundle.py --program diff --cmp-scheme-left "%TEXTFILE_A_JSON%" --cmp-scheme-right "%TEXTFILE_B_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

ECHO -
ECHO 6. final html with diff!
python dist/mdmtoolsap_bundle.py --program report --inpfile "%TEXTFILE_FINAL_DIFF_JSON%"
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && goto CLEANUP && exit /b %errorlevel% )

ECHO -
ECHO 7 del .json temporary files
DEL "%TEXTFILE_A%.json"
@REM DEL "%TEXTFILE_A%.json.html"
DEL "%TEXTFILE_B%.json"
@REM DEL "%TEXTFILE_B%.json.html"
DEL "%TEXTFILE_FINAL_DIFF_JSON%"

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

