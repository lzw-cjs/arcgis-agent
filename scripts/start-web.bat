@echo off
REM ============================================================
REM arcgis-agent Web UI 统一启动脚本 (Phase 7, D-15)
REM
REM 启动 FastAPI 后端（后台）+ Vite 前端（前台）
REM ============================================================

setlocal enabledelayedexpansion

echo ============================================================
echo   arcgis-agent Web UI Launcher
echo ============================================================
echo.

REM ── Check conda environment ──
echo [1/4] 检查 conda 环境...
conda activate arcgis-agent 2>nul
if errorlevel 1 (
    echo [错误] 无法激活 arcgis-agent conda 环境
    echo 请确保已创建 arcgis-agent 环境：conda create --name arcgis-agent ...
    pause
    exit /b 1
)
echo 已激活 arcgis-agent 环境

REM ── Start FastAPI backend ──
echo [2/4] 启动 FastAPI 后端 (127.0.0.1:8000)...
start "arcgis-agent API" cmd /c "conda activate arcgis-agent && python -m arcgis_agent.api.main"
echo FastAPI 后端已在新窗口启动

REM ── Wait for FastAPI to be ready ──
echo [3/4] 等待 FastAPI 启动...
set TRIES=0
:wait_loop
timeout /t 2 /nobreak >nul
curl -s http://127.0.0.1:8000/api/v1/health >nul 2>&1
if not errorlevel 1 goto :backend_ready
set /a TRIES+=1
if %TRIES% lss 15 goto :wait_loop
echo [警告] FastAPI 启动超时，仍继续启动前端...
goto :start_frontend

:backend_ready
echo FastAPI 后端已就绪

REM ── Start Vite frontend ──
:start_frontend
echo [4/4] 启动 Vite 前端 (localhost:5173)...
cd /d "%~dp0..\web"
if not exist "package.json" (
    echo [错误] web/package.json 不存在，请先创建 web/ 前端项目
    cd /d "%~dp0.."
    pause
    exit /b 1
)
if not exist "node_modules" (
    echo 初次运行，安装前端依赖...
    call npm install
)
echo.
echo ============================================================
echo   FastAPI 后端: http://127.0.0.1:8000
echo   Swagger 文档: http://127.0.0.1:8000/docs
echo   Vite 前端:    http://localhost:5173
echo ============================================================
echo.
echo 按 Ctrl+C 停止前端，关闭 FastAPI 窗口停止后端
echo.

call npx vite --host

echo 前端已停止
cd /d "%~dp0.."
pause
