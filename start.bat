@echo off
title Teams Translator - Caption Meeting

echo ============================================
echo    Teams Translator - Dịch real-time Anh-Việt
echo ============================================
echo.
echo Dang khoi dong...
echo Neu bi chan boi Windows Defender, chon "More info" - "Run anyway"
echo.

cd /d "D:\teams-translator"

:: Dùng venv của hermes-agent đã cài đủ thư viện
call "D:\hermes\hermes-agent\venv\Scripts\python.exe" run.py

if %errorlevel% neq 0 (
    echo.
    echo === CO LOI XAY RA ===
    echo Thu chay thu cong: python run.py
    pause
)
