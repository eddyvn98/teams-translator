@echo off
title Thiet lap am thanh: Nghe loa & Dich
echo Dang cau hinh thiet bi am thanh de nghe loa va dich dong thoi...
powershell -ExecutionPolicy Bypass -File "%~dp0setup_audio_monitor.ps1"
echo.
echo === Da cau hinh xong! Ban co the nghe loa va app co the dich. ===
echo.
pause
