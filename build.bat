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
ECHO Update program version
ECHO '''For auto-generated files''' > src\GENERATED\__init__.py
ECHO # THIS IS AUTO-GENERATED > src\GENERATED\_VERSION.py
python -c "from datetime import datetime; print(f'# {datetime.now()}')" >> src\GENERATED\_VERSION.py
ECHO _VERSION = ''' >> src\GENERATED\_VERSION.py
git describe --tags --dirty >> src\GENERATED\_VERSION.py
ECHO ''' >> src\GENERATED\_VERSION.py
ECHO Done

ECHO -
ECHO -
ECHO Re-building mdd_read program...
PUSHD src\lib\mdmreadpy
CALL build.bat
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )
POPD
ECHO Done

ECHO -
ECHO -
ECHO Re-building html template...
PUSHD src\lib\mdmreadpy\src\lib\mdmreportpy
CALL build.bat
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )
python build_compiled_template.py
if %ERRORLEVEL% NEQ 0 ( echo ERROR: Failure && pause && exit /b %errorlevel% )
POPD
ECHO Done

ECHO -
ECHO -
ECHO Produce distributable .py bundle - calling pinliner...
REM REM :: comment: please delete .pyc files before every call of the mdmtoolsap_bundle - this is implemented in my fork of the pinliner
@REM python src_dev_build\lib\pinliner\pinliner\pinliner.py src -o dist/mdmtoolsap_bundle.py --verbose
python src_dev_build\lib\pinliner\pinliner\pinliner.py src -o dist/mdmtoolsap_bundle.py
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
$src = '..\src_bat_scripts'; ^
$dest = '.'; ^
ForEach ($pair in $runScripts.GetEnumerator()) { ^
    Copy-Item (Join-Path $src $pair.Key) (Join-Path $dest $pair.Value) ^
}; "
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
    $c = $c.Replace('..\.venv\Scripts\python.exe', '.venv\Scripts\python.exe'); ^
    $c = $c.Replace('..\run_init.bat', 'run_init.bat'); ^
    $c = $c -replace '((?:..[\\/])?dist[/\\])?mdmtoolsap_bundle.py', 'mdmtoolsap_bundle.py'; ^
    ForEach ($pair2 in $runScripts.GetEnumerator()) { ^
        $c = $c -replace ('\b'+$pair2.Key+'\b'),  $pair2.Value; ^
    }; ^
    Set-Content $file $c; ^
}; "
POPD
ECHO Done

@REM DEL *.pyc
@REM IF EXIST __pycache__ (
@REM DEL /F /Q __pycache__\*
@REM )
@REM IF EXIST __pycache__ (
@REM RMDIR /Q /S __pycache__
@REM )

@REM ECHO Out

ECHO -
ECHO -
ECHO Bring a copy to ./tests-real-sensitive-data/ folder
COPY .\dist\mdmtoolsap_bundle.py .\tests-real-sensitive-data\current\ 2>nul
IF errorlevel 1 (
    REM :: That's ok to continue, just need to print a message that "not copied"
    ECHO Not updated
)

ECHO -
ECHO -
ECHO Bring LICENSE, README.md and requirements.txt to dist...
IF NOT EXIST requirements.txt (
    ECHO # Runtime dependencies, one per line. > requirements.txt
)
COPY /Y LICENSE dist\LICENSE
COPY /Y README.md dist\README.md
COPY /Y requirements.txt dist\requirements.txt
ECHO Done

ECHO -
ECHO -
ECHO Collect optional per-reader/per-reporter requirements into dist\optional_dependencies...
powershell -NoProfile -Command ^
"$srcRoot = (Resolve-Path 'src').Path; ^
$destRoot = 'dist\optional_dependencies'; ^
Get-ChildItem -Path (Join-Path $srcRoot 'lib') -Recurse -Filter 'requirements.txt' -File | Where-Object { ^
    $_.FullName -notmatch '\\dist\\' -and $_.FullName -notmatch '\\.git\\' -and $_.FullName -notmatch '\\GENERATED\\' ^
} | ForEach-Object { ^
    $rel = $_.FullName.Substring($srcRoot.Length + 1); ^
    $dest = Join-Path $destRoot $rel; ^
    $destDir = Split-Path -Parent $dest; ^
    if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }; ^
    Copy-Item $_.FullName $dest -Force; ^
    Write-Host ('copying optional requirements: ' + $rel) ^
}; "
ECHO Done

ECHO -
ECHO -
ECHO Copy and adapt run_init scripts to dist...
powershell -NoProfile -Command ^
"$c = Get-Content 'run_init.bat' -Encoding 'Default'; ^
$c = $c -replace 'src\\lib', 'optional_dependencies'; ^
Set-Content 'dist\run_init.bat' $c -Encoding 'Default'; ^
$c = Get-Content 'run_init.sh' -Encoding 'Default'; ^
$c = $c -replace 'src/lib', 'optional_dependencies'; ^
Set-Content 'dist\run_init.sh' $c -Encoding 'Default'; "
ECHO Done

ECHO -
ECHO -
ECHO All done, the end

