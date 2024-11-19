@ECHO OFF

ECHO Clear up dist\...
IF EXIST dist (
    REM -
) ELSE (
    MKDIR dist
)
DEL /F /Q dist\*

ECHO Calling pinliner...
REM REM :: comment: please delete .pyc files before every call of the mdmtoolsap_bundle - this is implemented in my fork of the pinliner
python src-make\lib\pinliner\pinliner\pinliner.py src -o dist/mdmtoolsap_bundle.py
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )
ECHO Done

ECHO Pathcing mdmtoolsap_bundle.py...
ECHO # ... >> dist/mdmtoolsap_bundle.py
ECHO # print('within mdmtoolsap_bundle') >> dist/mdmtoolsap_bundle.py
REM REM :: no need for this, the root package is loaded automatically
@REM ECHO # import mdmtoolsap_bundle >> dist/mdmtoolsap_bundle.py
ECHO from src import run_universal >> dist/mdmtoolsap_bundle.py
ECHO run_universal.main() >> dist/mdmtoolsap_bundle.py
ECHO # print('out of mdmtoolsap_bundle') >> dist/mdmtoolsap_bundle.py

PUSHD dist
COPY ..\run_calling_bundle.bat .\run_mdd_diff.bat
COPY ..\run_calling_bundle_mdd_report.bat .\run_mdd_report.bat
COPY ..\run_calling_bundle_textfile.bat .\run_diff_textfile.bat
COPY ..\run_calling_bundle_excel.bat .\run_diff_excel.bat
@REM REN mdmtoolsap_bundle.py mdmtoolsap.py
@REM powershell -Command "(gc 'run_mdd_diff.bat' -encoding 'Default') -replace '(dist[/\\])?mdmtoolsap_bundle.py', 'mdmtoolsap.py' | Out-File -encoding 'Default' 'run_mdd_diff.bat'"
@REM powershell -Command "(gc 'run_mdd_diff_routing.bat' -encoding 'Default') -replace '(dist[/\\])?mdmtoolsap_bundle.py', 'mdmtoolsap.py' | Out-File -encoding 'Default' 'run_mdd_diff_routing.bat'"
@REM powershell -Command "(gc 'run_mdd_diff_with_translations.bat' -encoding 'Default') -replace '(dist[/\\])?mdmtoolsap_bundle.py', 'mdmtoolsap.py' | Out-File -encoding 'Default' 'run_mdd_diff_with_translations.bat'"
@REM powershell -Command "(gc 'run_mdd_report.bat' -encoding 'Default') -replace '(dist[/\\])?mdmtoolsap_bundle.py', 'mdmtoolsap.py' | Out-File -encoding 'Default' 'run_mdd_report.bat'"
powershell -Command "(gc 'run_mdd_diff.bat' -encoding 'Default') -replace '(dist[/\\])?mdmtoolsap_bundle.py', 'mdmtoolsap_bundle.py' | Out-File -encoding 'Default' 'run_mdd_diff.bat'"
powershell -Command "(gc 'run_mdd_report.bat' -encoding 'Default') -replace '(dist[/\\])?mdmtoolsap_bundle.py', 'mdmtoolsap_bundle.py' | Out-File -encoding 'Default' 'run_mdd_report.bat'"
powershell -Command "(gc 'run_diff_textfile.bat' -encoding 'Default') -replace '(dist[/\\])?mdmtoolsap_bundle.py', 'mdmtoolsap_bundle.py' | Out-File -encoding 'Default' 'run_diff_textfile.bat'"
powershell -Command "(gc 'run_diff_excel.bat' -encoding 'Default') -replace '(dist[/\\])?mdmtoolsap_bundle.py', 'mdmtoolsap_bundle.py' | Out-File -encoding 'Default' 'run_diff_excel.bat'"
COPY .\run_mdd_diff.bat .\run_mdd_diff_routing.bat
powershell -Command "(gc 'run_mdd_diff_routing.bat' -encoding 'Default') -replace '--config-features\s+\w[\w,]*\w', '--config-features label' | Out-File -encoding 'Default' 'run_mdd_diff_routing.bat'"
powershell -Command "(gc 'run_mdd_diff_routing.bat' -encoding 'Default') -replace '--config-section\s+\w[\w,]*\w', '--config-section routing' | Out-File -encoding 'Default' 'run_mdd_diff_routing.bat'"
powershell -Command "(gc 'run_mdd_diff_routing.bat' -encoding 'Default') -replace '--program diff', '--program diff --output-filename-suffix .routing' | Out-File -encoding 'Default' 'run_mdd_diff_routing.bat'"
COPY .\run_mdd_diff.bat .\run_mdd_diff_with_translations.bat
powershell -Command "(gc 'run_mdd_diff_with_translations.bat' -encoding 'Default') -replace '--config-features\s+\w[\w,]*\w', '--config-features label,attributes,properties,translations' | Out-File -encoding 'Default' 'run_mdd_diff_with_translations.bat'"
POPD

@REM ECHO Clear up ..\test_pinliner_results\...
@REM PUSHD ..\test_pinliner_results
@REM DEL /F /Q *
@REM FOR /D %%G IN (*) DO RMDIR /S /Q %%G
@REM POPD

@REM ECHO Bring the mdmtoolsap_bundle to ..\test_pinliner_results\...
@REM COPY dist\mdmtoolsap_bundle.py ..\test_pinliner_results\

@REM PUSHD ..\test_pinliner_results
@REM Echo within ..\test_pinliner_results\
@REM REM python
@REM python mdmtoolsap_bundle.py --program test
@REM DEL *.pyc
@REM IF EXIST __pycache__ (
@REM DEL /F /Q __pycache__\*
@REM )
@REM IF EXIST __pycache__ (
@REM RMDIR /Q /S __pycache__
@REM )
@REM POPD

@REM ECHO Out

ECHO End

