@echo off
title Khoi phuc am thanh: Loa mac dinh
echo Dang khoi phuc am thanh ve loa ngoai mac dinh...
powershell -ExecutionPolicy Bypass -File "%~dp0setup_audio_monitor.ps1" -Restore
echo.
echo === Da khoi phuc loa mac dinh thanh cong! ===
echo.
pause
