#!/usr/bin/env bash
set -e

echo "Prep python"
echo "set venv"
if [ -x ".venv/Scripts/python.exe" ]; then
    pythonexecutable=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then
    pythonexecutable=".venv/bin/python"
else
    python -m venv .venv
    if [ -x ".venv/Scripts/python.exe" ]; then
        pythonexecutable=".venv/Scripts/python.exe"
    elif [ -x ".venv/bin/python" ]; then
        pythonexecutable=".venv/bin/python"
    else
        echo "No Python virtual environment found"
        exit 1
    fi
fi

echo "Upd dependencies"
"$pythonexecutable" -m pip install -r requirements.txt
echo "done"
echo "-"
echo "-"

# Install optional per-reader/per-reporter dependencies (best-effort).
# The distributed copy scans optional_dependencies/ instead.
if [ -d src/lib ]; then
    for requirements in $(find src/lib -type f -name 'requirements.txt' -not -path '*/.git/*' -not -path '*/dist/*' -not -path '*/GENERATED/*' | sort); do
        echo "installing optional dependencies: $requirements"
        if ! "$pythonexecutable" -m pip install -r "$requirements"; then
            echo "WARNING: optional dependencies in $requirements not installed (the corresponding reader/reporter will be unavailable)"
        fi
    done
fi

echo "done"
