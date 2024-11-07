@ECHO OFF

ECHO Clear up dist\...
DEL /F /Q dist\*

ECHO Calling pinliner...
pinliner src -o dist/bundle.py
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )
ECHO Done

ECHO Pathcing bundle.py...
ECHO # print('within bundle') >> dist/bundle.py
@REM ECHO # import bundle >> dist/bundle.py
ECHO from src import run_universal >> dist/bundle.py
ECHO run_universal.main() >> dist/bundle.py
ECHO # print('out of bundle') >> dist/bundle.py

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

