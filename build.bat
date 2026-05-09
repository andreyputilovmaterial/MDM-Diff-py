@ECHO OFF

ECHO Clear up dist\...
IF EXIST dist (
    REM -
) ELSE (
    MKDIR dist
)
DEL /F /Q dist\*

ECHO -
ECHO -
ECHO Re-building html template...
python src\lib\mdmreadpy\lib\mdmreportpy\build_compiled_template.py
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )
ECHO Done

ECHO -
ECHO -
ECHO Produce distributable .py bundle - calling pinliner...
REM REM :: comment: please delete .pyc files before every call of the mdmtoolsap_bundle - this is implemented in my fork of the pinliner
@REM python src-make\lib\pinliner\pinliner\pinliner.py src -o dist/mdmtoolsap_bundle.py --verbose
python src-make\lib\pinliner\pinliner\pinliner.py src -o dist/mdmtoolsap_bundle.py
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )
ECHO Done

ECHO -
ECHO -
ECHO Patching mdmtoolsap_bundle.py...
ECHO # ... >> dist/mdmtoolsap_bundle.py
ECHO # print('within mdmtoolsap_bundle') >> dist/mdmtoolsap_bundle.py
REM REM :: no need for this, the root package is loaded automatically
@REM ECHO # import mdmtoolsap_bundle >> dist/mdmtoolsap_bundle.py
ECHO from src import launcher >> dist/mdmtoolsap_bundle.py
ECHO launcher.main() >> dist/mdmtoolsap_bundle.py
ECHO # print('out of mdmtoolsap_bundle') >> dist/mdmtoolsap_bundle.py
ECHO Done

ECHO -
ECHO -
ECHO Copy BAT run scripts
PUSHD dist
powershell -NoProfile -Command ^
"$runScripts = @{ ^
    'run_calling_bundle_mdd.bat' = 'run_diff_mdd.bat'; ^
    'run_calling_bundle_aligned_diffs_mdd.bat' = 'run_diff_aligned_workflows_mdds.bat'; ^
    'run_calling_bundle_mdd_report.bat' = 'run_mdd_report.bat'; ^
    'run_calling_bundle_mdd_report_in_excel.bat' = 'run_mdd_report_in_excel.bat'; ^
    'run_calling_bundle_textfile.bat' = 'run_diff_textfile.bat'; ^
    'run_calling_bundle_msmarkitdown.bat' = 'run_diff_msmarkitdown.bat'; ^
    'run_calling_bundle_excel.bat' = 'run_diff_excel.bat'; ^
    'run_calling_bundle_excel_wholedirectory.bat' = 'run_diff_excel_wholedirectory.bat'; ^
    'run_calling_bundle_spss.bat' = 'run_diff_spss.bat'; ^
}; ^
$src = '..'; ^
$dest = '.'; ^
ForEach ($pair in $runScripts.GetEnumerator()) { ^
    Copy-Item (Join-Path $src $pair.Key) (Join-Path $dest $pair.Value) ^
}; "
@REM COPY ..\run_calling_bundle_mdd.bat .\run_diff_mdd.bat
@REM COPY ..\run_calling_bundle_aligned_diffs_mdd.bat .\run_diff_aligned_workflows_mdds.bat
@REM COPY ..\run_calling_bundle_mdd_report.bat .\run_mdd_report.bat
@REM COPY ..\run_calling_bundle_mdd_report_in_excel.bat .\run_mdd_report_in_excel.bat
@REM COPY ..\run_calling_bundle_textfile.bat .\run_diff_textfile.bat
@REM COPY ..\run_calling_bundle_msmarkitdown.bat .\run_diff_msmarkitdown.bat
@REM COPY ..\run_calling_bundle_excel.bat .\run_diff_excel.bat
@REM COPY ..\run_calling_bundle_excel_wholedirectory.bat .\run_diff_excel_wholedirectory.bat
@REM COPY ..\run_calling_bundle_spss.bat .\run_diff_spss.bat
ECHO Done



ECHO -
ECHO -
ECHO Make text replacements in BAT scripts
powershell -NoProfile -Command ^
"$runScripts = @{ ^
    'run_calling_bundle_mdd.bat' = 'run_diff_mdd.bat'; ^
    'run_calling_bundle_aligned_diffs_mdd.bat' = 'run_diff_aligned_workflows_mdds.bat'; ^
    'run_calling_bundle_mdd_report.bat' = 'run_mdd_report.bat'; ^
    'run_calling_bundle_mdd_report_in_excel.bat' = 'run_mdd_report_in_excel.bat'; ^
    'run_calling_bundle_textfile.bat' = 'run_diff_textfile.bat'; ^
    'run_calling_bundle_msmarkitdown.bat' = 'run_diff_msmarkitdown.bat'; ^
    'run_calling_bundle_excel.bat' = 'run_diff_excel.bat'; ^
    'run_calling_bundle_excel_wholedirectory.bat' = 'run_diff_excel_wholedirectory.bat'; ^
    'run_calling_bundle_spss.bat' = 'run_diff_spss.bat'; ^
}; ^
$src = '..'; ^
$dest = '.'; ^
ForEach ($pair in $runScripts.GetEnumerator()) { ^
    $file = (Join-Path $dest $pair.Value); ^
    $c = (Get-Content $file -Encoding 'Default'); ^
    $c = $c -replace '(dist[/\\])?mdmtoolsap_bundle.py', 'mdmtoolsap_bundle.py'; ^
    ForEach ($pair2 in $runScripts.GetEnumerator()) { ^
        $c = $c -replace ('\b'+$pair2.Key+'\b'),  $pair2.Value; ^
    }; ^
    Set-Content $file $c; ^
}; "
POPD
ECHO Done

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

ECHO -
ECHO -
ECHO Bring a copy to ./test/ folder
COPY .\dist\mdmtoolsap_bundle.py .\tests\current\ 2>nul
IF errorlevel 1 (
    ECHO Not updated
)

ECHO -
ECHO -
ECHO All done, the end

