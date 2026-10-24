@echo off
chcp 65001 > nul
title Teams Translator Server (trans.vivutrade.io.vn)
echo ========================================================
echo   Starting Teams Translator Server & Cloudflare Tunnel
echo   Public URL: https://trans.vivutrade.io.vn
echo   Local URL:  http://localhost:8080
echo ========================================================

cd /d "%~dp0"

REM 1. Start Python Web Server
echo [1/2] Starting FastAPI Server on port 8080...
if exist .venv\Scripts\python.exe (
    start "Teams Translator Web Server" cmd /k "cd /d "%~dp0" && .venv\Scripts\python.exe run_web.py --port 8080 --no-browser"
) else (
    start "Teams Translator Web Server" cmd /k "cd /d "%~dp0" && python run_web.py --port 8080 --no-browser"
)

REM 2. Start Cloudflare Tunnel
echo [2/2] Starting Cloudflare Tunnel trans-vivutrade...
start "Cloudflare Tunnel trans-vivutrade" cmd /k ""C:\Program Files (x86)\cloudflared\cloudflared.exe" --config "%~dp0blank_config.yml" tunnel run --url http://localhost:8080 trans-vivutrade"

echo.
echo ========================================================
echo Server and Tunnel have been launched!
echo Access from any device at: https://trans.vivutrade.io.vn
echo Keep the opened command windows running.
echo ========================================================
timeout /t 5
