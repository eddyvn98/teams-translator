@echo off
chcp 65001 > nul
title Stop Teams Translator Server
echo ========================================================
echo   Stopping Teams Translator Server & Tunnel
echo ========================================================

powershell -NoProfile -ExecutionPolicy Bypass -Command "
$port8080 = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue;
if ($port8080) {
    $pids = $port8080.OwningProcess | Select-Object -Unique;
    foreach ($p in $pids) {
        Write-Host 'Stopping Web Server (PID:' $p ')...' -ForegroundColor Yellow;
        Stop-Process -Id $p -Force -ErrorAction SilentlyContinue;
    }
}
$tunnels = Get-CimInstance Win32_Process -Filter \"name = 'cloudflared.exe'\" | Where-Object { $_.CommandLine -like '*trans-vivutrade*' };
if ($tunnels) {
    foreach ($t in $tunnels) {
        Write-Host 'Stopping Tunnel trans-vivutrade (PID:' $t.ProcessId ')...' -ForegroundColor Yellow;
        Stop-Process -Id $t.ProcessId -Force -ErrorAction SilentlyContinue;
    }
}
Write-Host 'Successfully stopped.' -ForegroundColor Green;
"
pause
