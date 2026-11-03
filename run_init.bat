@echo off
setlocal

echo Prep python
echo set venv

if exist ".venv\Scripts\python.exe" (
    set "pythonexecutable=.venv\Scripts\python.exe"
) else (
    echo Creating Python virtual environment...
    python -m venv .venv
    if exist ".venv\Scripts\python.exe" (
        set "pythonexecutable=.venv\Scripts\python.exe"
    ) else (
        echo No Python virtual environment found
        exit /b 1
    )
)

echo Upd dependencies
@REM === BEGIN GENERATED DEPENDENCIES ===
"%pythonexecutable%" -m pip install -r requirements.txt
@REM Install optional per-reader/per-reporter dependencies (best-effort).
@REM The distributed copy installs these from explicit pip package lists
@REM generated at build time (no requirements.txt files ship in dist/).
if exist "src\lib" (
    for /r "src\lib" %%f in (requirements.txt) do (
        if exist "%%f" (
            echo Installing optional dependencies: %%f
            "%pythonexecutable%" -m pip install -r "%%f"
            if errorlevel 1 echo WARNING: optional dependencies in %%f not installed - the corresponding reader/reporter will be unavailable
        )
    )
)
@REM === END GENERATED DEPENDENCIES ===
echo done
echo.
echo.

endlocal
