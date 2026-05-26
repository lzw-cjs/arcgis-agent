@echo off
cd /d "C:\Users\李打爷的电脑\Desktop\arcgis-agent"
"C:\conda-envs\arcgis-agent\python.exe" -m pip uninstall arcgis-agent -y
"C:\conda-envs\arcgis-agent\python.exe" -m pip install -e . --no-cache-dir
"C:\conda-envs\arcgis-agent\python.exe" -c "import arcgis_agent; print('Version:', arcgis_agent.__version__)"
"C:\conda-envs\arcgis-agent\python.exe" -c "from arcgis_agent.cli import cli; from click.testing import CliRunner; r = CliRunner().invoke(cli, ['--version']); print(r.output.strip())"
