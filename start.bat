@echo off
title Teams Translator - Caption Meeting
cd /d "%~dp0"

echo ============================================
echo    Teams Translator - Dich real-time Anh-Viet
echo ============================================
echo.
echo Dang khoi dong bang .venv local...
echo.

REM Dung python tu thu muc ao .venv vua tao
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe run.py
) else (
    echo ❌ Khong tim thay moi truong ao .venv!
    echo Vui long chay lai file setup truoc.
    pause
)

if %errorlevel% neq 0 (
    echo.
    echo === CO LOI XAY RA ===
    pause
)
