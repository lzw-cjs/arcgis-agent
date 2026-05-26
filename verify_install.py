"""Temporary script to verify arcgis-agent installation."""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, '-c', 'import arcgis_agent; print("Version:", arcgis_agent.__version__)'],
    capture_output=True, text=True,
    cwd=r'C:\Users\李打爷的电脑\Desktop\arcgis-agent'
)
print('stdout:', result.stdout.strip())
print('stderr:', result.stderr.strip())
print('rc:', result.returncode)
