@echo off
REM arcgis-agent.bat - Wrapper script for ArcGIS Pro Python environment
REM Usage: arcgis-agent.bat [args...]

REM Step 1: Activate proenv to set ARCGISHOME and DLL paths
call "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\proenv.bat"

REM Step 2: Switch to arcgis-agent conda env (where the package is installed)
call conda activate arcgis-agent

REM Set UTF-8 encoding for Chinese path support
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

REM Run the CLI
python -m arcgis_agent %*
