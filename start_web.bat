@echo off
chcp 65001 > nul
title Teams Translator - Google AI Studio Live Web
echo ========================================================
echo   Khoi dong Teams Translator (Google AI Studio Live Web)
echo ========================================================

cd /d "%~dp0"

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe run_web.py
) else (
    python run_web.py
)
pause
