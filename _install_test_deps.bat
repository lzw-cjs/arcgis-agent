@echo off
"C:/conda-envs/arcgis-agent/python.exe" -m pip install pytest
"C:/conda-envs/arcgis-agent/python.exe" -m pip install .
"C:/conda-envs/arcgis-agent/python.exe" -c "import pytest; print('pytest', pytest.__version__)"
"C:/conda-envs/arcgis-agent/python.exe" -c "import arcgis_agent; print('arcgis_agent', arcgis_agent.__version__)"
