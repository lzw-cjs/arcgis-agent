"""Fix the editable install by uninstalling and reinstalling with no cache."""
import subprocess
import sys

PYTHON = r"C:\conda-envs\arcgis-agent\python.exe"
PROJECT = r"C:\Users\李打爷的电脑\Desktop\arcgis-agent"

# Uninstall
print("Uninstalling arcgis-agent...")
r1 = subprocess.run([PYTHON, "-m", "pip", "uninstall", "arcgis-agent", "-y"],
                     capture_output=True, text=True)
print(r1.stdout[-200:] if r1.stdout else "")
print(r1.stderr[-200:] if r1.stderr else "")

# Reinstall with no cache
print("Reinstalling arcgis-agent with --no-cache-dir...")
r2 = subprocess.run([PYTHON, "-m", "pip", "install", "-e", PROJECT, "--no-cache-dir"],
                     capture_output=True, text=True)
print(r2.stdout[-500:] if r2.stdout else "")
print(r2.stderr[-500:] if r2.stderr else "")

# Verify
print("Verifying import...")
r3 = subprocess.run([PYTHON, "-c", "import arcgis_agent; print('Version:', arcgis_agent.__version__)"],
                     capture_output=True, text=True, cwd=PROJECT)
print("stdout:", r3.stdout.strip())
print("stderr:", r3.stderr.strip())
print("rc:", r3.returncode)

# Verify CLI
print("Verifying CLI...")
r4 = subprocess.run([PYTHON, "-c",
    "from arcgis_agent.cli import cli; from click.testing import CliRunner; r = CliRunner().invoke(cli, ['--version']); print(r.output.strip())"],
    capture_output=True, text=True, cwd=PROJECT)
print("stdout:", r4.stdout.strip())
print("stderr:", r4.stderr.strip())
print("rc:", r4.returncode)
