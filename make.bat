@ECHO OFF

ECHO Clear up dist\...
DEL /F /Q dist\*

ECHO Calling pinliner...
REM REM :: comment: please delete .pyc files before every call of the bundle - this is implemented in my fork of the pinliner
pinliner src -o dist/bundle.py
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )
ECHO Done

ECHO Pathcing bundle.py...
ECHO # ... >> dist/bundle.py
ECHO # print('within bundle') >> dist/bundle.py
REM REM :: no need for this, the root package is loaded automatically
@REM ECHO # import bundle >> dist/bundle.py
ECHO from src import run_universal >> dist/bundle.py
ECHO run_universal.main() >> dist/bundle.py
ECHO # print('out of bundle') >> dist/bundle.py

PUSHD dist
COPY ..\run_calling_bundle.bat .\run_mdd_diff.bat
COPY ..\run_calling_bundle_with_routing.bat .\run_mdd_diff_with_routing.bat
COPY ..\run_calling_bundle_with_translations.bat .\run_mdd_diff_with_translations.bat
COPY ..\run_calling_bundle_mdd_report.bat .\run_mdd_report.bat
REN bundle.py mdmtoolsap.py
powershell -Command "(gc 'run_mdd_diff.bat' -encoding 'Default') -replace '(dist[/\\])?bundle.py', 'mdmtoolsap.py' | Out-File -encoding 'Default' 'run_mdd_diff.bat'"
powershell -Command "(gc 'run_mdd_diff_with_routing.bat' -encoding 'Default') -replace '(dist[/\\])?bundle.py', 'mdmtoolsap.py' | Out-File -encoding 'Default' 'run_mdd_diff_with_routing.bat'"
powershell -Command "(gc 'run_mdd_diff_with_translations.bat' -encoding 'Default') -replace '(dist[/\\])?bundle.py', 'mdmtoolsap.py' | Out-File -encoding 'Default' 'run_mdd_diff_with_translations.bat'"
powershell -Command "(gc 'run_mdd_report.bat' -encoding 'Default') -replace '(dist[/\\])?bundle.py', 'mdmtoolsap.py' | Out-File -encoding 'Default' 'run_mdd_report.bat'"
POPD

@REM ECHO Clear up ..\test_pinliner_results\...
@REM PUSHD ..\test_pinliner_results
@REM DEL /F /Q *
@REM FOR /D %%G IN (*) DO RMDIR /S /Q %%G
@REM POPD

@REM ECHO Bring the bundle to ..\test_pinliner_results\...
@REM COPY dist\bundle.py ..\test_pinliner_results\

@REM PUSHD ..\test_pinliner_results
@REM Echo within ..\test_pinliner_results\
@REM REM python
@REM python bundle.py --program test
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

