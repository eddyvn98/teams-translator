@echo off
REM ============================================
REM Teams Translator - Install Script cho Windows
REM ============================================
title Cài đặt Teams Translator
echo ============================================
echo   Teams Translator - Real-time Dịch Anh-Viet
echo ============================================
echo.
echo Buoc 1: Cai dat Python dependencies...
echo.

cd /d "%~dp0"

REM Kiem tra Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python chua duoc cai dat!
    echo Download tu: https://www.python.org/downloads/
    echo Nho tick "Add Python to PATH" khi cai dat.
    pause
    exit /b 1
)

echo Python OK.

REM Cai dat pip packages
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [!] Loi khi cai dat packages.
    pause
    exit /b 1
)

echo.
echo Buoc 2: Cai dat PyAudio (can thiet cho microphone)...
echo.

REM Kiem tra PyAudio da duoc cai chua
python -c "import pyaudio" 2>nul
if %errorlevel% neq 0 (
    echo Dang cai PyAudio...
    pip install pipwin
    pipwin install pyaudio
)

echo.
echo Buoc 3: Tao shortcut tren Desktop...
echo.

set SCRIPT_DIR=%~dp0
set SHORTCUT_PATH=%USERPROFILE%\Desktop\Teams Translator.lnk

REM Tao VBScript de tao shortcut
echo Set WshShell = WScript.CreateObject("WScript.Shell") > "%TEMP%\shortcut.vbs"
echo Set Shortcut = WshShell.CreateShortcut("%SHORTCUT_PATH%") >> "%TEMP%\shortcut.vbs"
echo Shortcut.TargetPath = "pythonw" >> "%TEMP%\shortcut.vbs"
echo Shortcut.Arguments = """%SCRIPT_DIR%run.py""" >> "%TEMP%\shortcut.vbs"
echo Shortcut.WorkingDirectory = "%SCRIPT_DIR%" >> "%TEMP%\shortcut.vbs"
echo Shortcut.Description = "Teams Translator - Dich Anh Viet real-time" >> "%TEMP%\shortcut.vbs"
echo Shortcut.IconLocation = "%SCRIPT_DIR%resources\icon.png" >> "%TEMP%\shortcut.vbs"
echo Shortcut.Save >> "%TEMP%\shortcut.vbs"
cscript /nologo "%TEMP%\shortcut.vbs"
del "%TEMP%\shortcut.vbs"

echo.
echo ============================================
echo   Cai dat hoan tat!
echo ============================================
echo.
echo De chay:
echo   1. Nhay vao shortcut "Teams Translator" tren Desktop
echo     (hoac: python run.py)
echo.
echo Hotkeys:
echo   Ctrl+Shift+T : Bat/Tat dich thuat
echo   Ctrl+Shift+M : Push-to-Talk (nhan giu de noi)
echo   Ctrl+Shift+C : Bat/Tat caption overlay
echo.
echo Ung dung chay trong system tray (gan dong ho).
echo Nhap chuot phai vao icon de mo menu.
echo.
pause
