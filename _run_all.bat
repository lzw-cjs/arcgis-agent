@echo off
cd /d "C:\Users\李打爷的电脑\Desktop\arcgis-agent"
echo Installing pytest...
"C:\conda-envs\arcgis-agent\python.exe" -m pip install pytest
echo.
echo Installing arcgis-agent...
"C:\conda-envs\arcgis-agent\python.exe" -m pip install .
echo.
echo Running tests...
"C:\conda-envs\arcgis-agent\python.exe" -m pytest tests/ -v
echo.
echo Done. Exit code: %ERRORLEVEL%
