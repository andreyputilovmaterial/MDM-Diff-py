#!/usr/bin/env bash
# POSIX (macOS / Linux) counterpart of build.bat.

set -u

fail() {
    echo "ERROR: Failure" >&2
    exit 1
}

RUN_SCRIPT_PAIRS="
run_calling_bundle_mdd.bat:run_diff_mdd.bat
run_calling_bundle_aligned_diffs_mdd.bat:run_diff_aligned_workflows_mdds.bat
run_calling_bundle_mdd_report.bat:run_mdd_report.bat
run_calling_bundle_mdd_report_in_excel.bat:run_mdd_report_in_excel.bat
run_calling_bundle_textfile.bat:run_diff_textfile.bat
run_calling_bundle_msmarkitdown.bat:run_diff_msmarkitdown.bat
run_calling_bundle_excel.bat:run_diff_excel.bat
run_calling_bundle_excel_wholedirectory.bat:run_diff_excel_wholedirectory.bat
run_calling_bundle_spss.bat:run_diff_spss.bat
"

echo "Clear up dist/..."
rm -rf dist
mkdir -p dist

echo "-"
echo "-"
echo "Update program version"
mkdir -p src/GENERATED
printf "%s\n" "'''For auto-generated files'''" > src/GENERATED/__init__.py
printf "%s\n" "# THIS IS AUTO-GENERATED" > src/GENERATED/_VERSION.py
python -c "from datetime import datetime; print(f'# {datetime.now()}')" >> src/GENERATED/_VERSION.py
printf "%s\n" "_VERSION = '''" >> src/GENERATED/_VERSION.py
git describe --tags --dirty >> src/GENERATED/_VERSION.py
printf "%s\n" "'''" >> src/GENERATED/_VERSION.py
echo "Done"

echo "-"
echo "-"
echo "Re-building mdd_read program..."
(
    set -e
    cd src/lib/mdmreadpy
    bash build.sh
) || fail
echo "Done"

echo "-"
echo "-"
echo "Re-building html template..."
(
    set -e
    cd src/lib/mdmreadpy/src/lib/mdmreportpy
    bash build.sh
    python build_compiled_template.py
) || fail
echo "Done"

echo "-"
echo "-"
echo "Produce distributable .py bundle - calling pinliner..."
python src_dev_build/lib/pinliner/pinliner/pinliner.py src -o dist/mdmtoolsap_bundle.py || fail
echo "Done"

echo "-"
echo "-"
echo "Patching mdmtoolsap_bundle.py..."
cat >> dist/mdmtoolsap_bundle.py <<'EOF'
# ...
# print('within mdmtoolsap_bundle')
from src import launcher
launcher.main()
# print('out of mdmtoolsap_bundle')
EOF
echo "Done"

echo "-"
echo "-"
echo "Copy BAT run scripts"
for pair in $RUN_SCRIPT_PAIRS; do
    src="${pair%%:*}"
    dst="${pair##*:}"
    cp "src_bat_scripts/$src" "dist/$dst"
done
echo "Done"

echo "-"
echo "-"
echo "Make text replacements in BAT scripts"
for pair in $RUN_SCRIPT_PAIRS; do
    dst="${pair##*:}"
    file="dist/$dst"
    sed -i.bak \
        -e 's#\.\.\\\.venv\\Scripts\\python\.exe#.venv\\Scripts\\python.exe#g' \
        -e 's#\.\./dist/mdmtoolsap_bundle\.py#mdmtoolsap_bundle.py#g' \
        -e 's#dist/mdmtoolsap_bundle\.py#mdmtoolsap_bundle.py#g' \
        "$file"
    rm -f "$file.bak"
done
# rewrite cross-references between the renamed scripts
for dstfile in dist/*.bat; do
    for pair in $RUN_SCRIPT_PAIRS; do
        src="${pair%%:*}"
        dst="${pair##*:}"
        sed -i.bak "s#$src#$dst#g" "$dstfile"
        rm -f "$dstfile.bak"
    done
done
echo "Done"

echo "-"
echo "-"
echo "Bring a copy to ./tests-real-sensitive-data/ folder"
cp dist/mdmtoolsap_bundle.py tests-real-sensitive-data/current/ 2>/dev/null || echo "Not updated"

echo "-"
echo "-"
echo "Bring LICENSE and README.md to dist..."
cp LICENSE dist/LICENSE
cp README.md dist/README.md
echo "Done"

echo "-"
echo "-"
echo "Inline run_init (venv setup + explicit pip installs) into dist launchers..."
python src_dev_build/inline_run_init.py || fail
echo "Done"

echo "-"
echo "-"
echo "Verify the bundle: run --program done..."
python dist/mdmtoolsap_bundle.py --program done || fail
echo "Done"

echo "-"
echo "-"
echo "All done, the end"
