#!/bin/bash
cd "C:/Users/李打爷的电脑/Desktop/arcgis-agent"
export PATH="/c/Users/李打爷的电脑/Desktop:/c/Users/李打爷的电脑/Desktop/Scripts:$PATH"
python.exe -m pip install pytest 2>&1 | tail -2
python.exe -m pip install . 2>&1 | tail -2
echo "=== Running tests ==="
python.exe -m pytest tests/ -v 2>&1
echo "=== Exit code: $? ==="
