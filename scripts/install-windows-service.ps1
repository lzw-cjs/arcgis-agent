# ArcGIS Agent — Windows 服务安装脚本
# 使用 NSSM (Non-Sucking Service Manager) 注册为 Windows 服务
#
# 前提: choco install nssm
# 用法: 以管理员身份运行 PowerShell

param(
    [string]$CondaEnv = "arcgis-agent",
    [string]$InstallDir = (Get-Location).Path,
    [string]$Port = "8000"
)

$ErrorActionPreference = "Stop"

# 检查 NSSM
if (-not (Get-Command nssm -ErrorAction SilentlyContinue)) {
    Write-Error "NSSM not found. Install with: choco install nssm"
    exit 1
}

# 查找 Python 路径
$CondaPrefix = conda info --base 2>$null
if (-not $CondaPrefix) {
    Write-Error "Conda not found. Please install Miniconda or ArcGIS Pro."
    exit 1
}

$PythonPath = Join-Path $CondaPrefix "envs" $CondaEnv "python.exe"
if (-not (Test-Path $PythonPath)) {
    Write-Error "Python not found at $PythonPath. Create env first: conda create -n $CondaEnv --clone arcgispro-py3"
    exit 1
}

$ServiceName = "arcgis-agent"

# 注册服务
nssm install $ServiceName $PythonPath "-m" "arcgis_agent.api.main"
nssm set $ServiceName AppDirectory $InstallDir
nssm set $ServiceName AppEnvironment "PYTHONUTF8=1" "APP_ENV=production" "API_PORT=$Port"
nssm set $ServiceName AppStdout (Join-Path $InstallDir "logs" "stdout.log")
nssm set $ServiceName AppStderr (Join-Path $InstallDir "logs" "stderr.log")
nssm set $ServiceName Start SERVICE_AUTO_START

Write-Host "Service '$ServiceName' installed successfully."
Write-Host "Start with: nssm start $ServiceName"
Write-Host "Status:     nssm status $ServiceName"
Write-Host "Stop:       nssm stop $ServiceName"
Write-Host "Remove:     nssm remove $ServiceName confirm"