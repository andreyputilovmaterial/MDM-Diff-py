@ECHO OFF
setlocal enabledelayedexpansion

SET "FOLDER_A=P:\150_Jagou\150_BES Fiscal Year 24 Global\IPS\Tables\10.01.2024"
SET "FOLDER_B=P:\150_Jagou\150_BES Fiscal Year 25 Global\IPS\Tables\12.18.2024"


REM FOR /f %%i IN ('echo %cd%') DO SET "CURRDIR=%%i"
SET "CURRDIR=%cd%"
PUSHD "%FOLDER_B%"

    FOR /f "delims=" %%f IN ('dir /b /a-d-h-s *.xlsx') DO (
        PUSHD "%CURRDIR%"
        SET "left=%FOLDER_A%\%%f"
        SET "right=%FOLDER_B%\%%f"

        @REM :: REM Example: if file names were different: replace 2400814 with 2301349 (i.e., diff proj number last wave)
        @REM SET "left=!left:2400814=2301349!"

        @REM :: REM Example: fallback directory: if the last directory does not include all files, we can point it to prev. wxports
        @REM if exist "!left!" (
        @REM     SET "left=!left!"
        @REM ) ELSE (
        @REM     ECHO "left does not exist, renaming !left! to ..."
        @REM     SET "left=!left:10.01.2024=09.25.2024!"
        @REM )

        if exist "!left!" (
            if exist "!right!" (
                CALL run_diff_excel "!left!" "!right!"
            ) ELSE (
                ECHO "right does not exist: !right!"
            )
        ) ELSE (
            ECHO "left does not exist: !left!"
        )
        if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )
        POPD        
    )

POPD


