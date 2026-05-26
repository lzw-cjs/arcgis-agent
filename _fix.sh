#!/bin/bash
cd "C:/Users/李打爷的电脑/Desktop/arcgis-agent"
"C:/conda-envs/arcgis-agent/python.exe" -m pip uninstall arcgis-agent -y
"C:/conda-envs/arcgis-agent/python.exe" -m pip install -e . --no-cache-dir
"C:/conda-envs/arcgis-agent/python.exe" -c "import arcgis_agent; print('Version:', arcgis_agent.__version__)"
