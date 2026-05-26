@echo off
cd /d "C:\Users\李打爷的电脑\Desktop\arcgis-agent"
"C:/conda-envs/arcgis-agent/python.exe" -m pip install pytest 2>nul
"C:/conda-envs/arcgis-agent/python.exe" -m pip install . 2>nul
echo === Running tests ===
"C:/conda-envs/arcgis-agent/python.exe" -m pytest tests/ -v
echo === Done ===
