@ECHO OFF
SETLOCAL enabledelayedexpansion

REM :: folder to take files for comparison:
SET "FOLDER_RECENT=P:\150_Jagou\150_BES Fiscal Year 25 Global\IPS\Tables\12.18.2024"

REM :: folder with older files, something what we compare to
SET "FOLDER_OLD_TO_COMPARE_TO=P:\150_Jagou\150_BES Fiscal Year 24 Global\IPS\Tables\10.01.2024"

REM :: fallback folder, if there are no files in that "older" folder we take even older files from here
SET "FOLDER_OLD_TO_COMPARE_TO_ALT=P:\150_Jagou\150_BES Fiscal Year 24 Global\IPS\Tables\09.25.2024"


REM ::and also we can replace certain part of file names, for example, if project number in older files file name was different
SET "FNAME_SUBSTITUTE_PART_USE=2400814"
SET "FNAME_SUBSTITUTE_PART_INSTEADOF=2301349"


REM FOR /f %%i IN ('echo %cd%') DO SET "CURRDIR=%%i"
SET "CURRDIR=%cd%"
PUSHD "%FOLDER_RECENT%"

    FOR /f "delims=" %%f IN ('DIR /b /a-d-h-s *.xlsx') DO (
        
		ECHO .
		ECHO "processing %%f"
		
        PUSHD "%CURRDIR%"
        SET "left=%FOLDER_OLD_TO_COMPARE_TO%\%%f"
        SET "right=%FOLDER_RECENT%\%%f"

        REM :: Example: if file names were different: replace 2400814 with 2301349 (i.e., diff proj number last wave)
        SET "left=!left:%FNAME_SUBSTITUTE_PART_USE%=%FNAME_SUBSTITUTE_PART_INSTEADOF%!"

        :: REM Example: fallback directory: if the last directory does not include all files, we can point it to prev. wxports
        IF EXIST "!left!" (
            SET "left=!left!"
        ) ELSE (
            ECHO "Hm, left (!left!) does not exist, trying alt folder instead..."
            SET "left=!left:%FOLDER_OLD_TO_COMPARE_TO%=%FOLDER_OLD_TO_COMPARE_TO_ALT%!"
            ECHO "...trying this: (!left!)"
        )

		ECHO "comparing (!left!) to (!right!)"
		IF EXIST "!left!" (
            IF EXIST "!right!" (
				REM :: ECHO calling run_diff_excel...
                CALL run_diff_excel "!left!" "!right!"
            ) ELSE (
                ECHO "ERR: right does not exist: !right!"
            )
        ) ELSE (
            ECHO "ERR: left does not exist: !left!"
        )
		ECHO .
        if !ERRORLEVEL! NEQ 0 ( echo ERROR: Failure && pause && exit /b !ERRORLEVEL! )
        POPD        
    )

POPD


