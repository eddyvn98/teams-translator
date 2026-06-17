@echo off
title Teams Translator Minimalist - Caption Meeting
cd /d "%~dp0"

echo ============================================
echo    Teams Translator Minimalist - Real-time
echo ============================================
echo.
echo Dang khoi dong giao dien toi gian...
echo.

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe run_minimal.py
) else (
    echo [ERROR] Khong tim thay moi truong ao .venv!
    pause
)

if %errorlevel% neq 0 (
    echo.
    echo === CO LOI XAY RA ===
    pause
)
