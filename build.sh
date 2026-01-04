#!/bin/bash
set -e  # exit immediately on error
set -u  # treat unset variables as error

echo "Clear up dist/..."
if [ ! -d dist ]; then
    mkdir -p dist
fi
# Remove all files inside dist
rm -f dist/*

echo "Calling pinliner..."
# Note: uncomment the line below if you want verbose output
# python src-make/lib/pinliner/pinliner/pinliner.py src -o dist/mdmtoolsap_bundle.py --verbose
python src-make/lib/pinliner/pinliner/pinliner.py src -o dist/mdmtoolsap_bundle.py --embed-code-encoding default_quotes_escape
if [ $? -ne 0 ]; then
    echo "ERROR: Failure"
    exit 1
fi
echo "Done"

echo "Patching mdmtoolsap_bundle.py..."
{
    echo "# ..."
    echo "# print('within mdmtoolsap_bundle')"
    echo "from src import launcher"
    echo "launcher.main()"
    echo "# print('out of mdmtoolsap_bundle')"
} >> dist/mdmtoolsap_bundle.py

# Change into dist directory
pushd dist > /dev/null

# Copy shell/batch scripts (use cp instead of COPY)
cp ../run_calling_bundle_mdd.bat ./run_mdd_diff.bat
cp ../run_calling_bundle_mdd_report.bat ./run_mdd_report.bat
cp ../run_calling_bundle_mdd_report_in_excel.bat ./run_mdd_report_in_excel.bat
cp ../run_calling_bundle_textfile.bat ./run_diff_textfile.bat
cp ../run_calling_bundle_msmarkitdown.bat ./run_diff_msmarkitdown.bat
cp ../run_calling_bundle_excel.bat ./run_diff_excel.bat
cp ../run_calling_bundle_excel_wholedirectory.bat ./run_diff_excel_wholedirectory.bat
cp ../run_calling_bundle_spss.bat ./run_diff_spss.bat

# In BAT you used PowerShell for regex replace.
# In sh, use sed in-place. macOS requires -i '' syntax
for f in run_mdd_diff.bat run_mdd_report.bat run_mdd_report_in_excel.bat \
         run_diff_textfile.bat run_diff_msmarkitdown.bat run_diff_excel.bat \
         run_diff_excel_wholedirectory.bat run_diff_spss.bat; do
    sed -i '' -E "s#(dist/)?mdmtoolsap_bundle.py#mdmtoolsap_bundle.py#g" "$f"
done

popd > /dev/null

# Optional cleanup steps commented in original BAT are skipped
# Uncomment and adapt if needed

echo "End"
