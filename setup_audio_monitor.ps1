$ErrorActionPreference = "Stop"

$toolDir = Join-Path $env:TEMP "soundvolumeview"
$exe = Join-Path $toolDir "SoundVolumeView.exe"
$zip = Join-Path $toolDir "soundvolumeview-x64.zip"
$speaker = "Wuying ASP Audio"

if (-not (Test-Path $exe)) {
    New-Item -ItemType Directory -Force -Path $toolDir | Out-Null
    Invoke-WebRequest -Uri "https://www.nirsoft.net/utils/soundvolumeview-x64.zip" -OutFile $zip
    Expand-Archive -LiteralPath $zip -DestinationPath $toolDir -Force
}

# Keep default system audio on the real speaker.
& $exe /SetDefault $speaker all

# Route source audio into VB-CABLE so Teams Translator can capture it.
# The CABLE Output monitor below sends the same audio back to the real speaker.
& $exe /SetAppDefault "CABLE Input" all "chrome.exe"
& $exe /SetAppDefault "CABLE Input" all "msedge.exe"
& $exe /SetAppDefault "CABLE Input" all "ms-teams.exe"
& $exe /SetAppDefault "CABLE Input" all "MSTeams.exe"
& $exe /SetAppDefault "CABLE Input" all "Teams.exe"
& $exe /SetAppDefault "CABLE Input" all "msedgewebview2.exe"
Get-Process chrome,msedge,ms-teams,MSTeams,Teams,msedgewebview2 -ErrorAction SilentlyContinue | ForEach-Object {
    & $exe /SetAppDefault "CABLE Input" all $_.Id
}

# Disable Windows' flaky monitor path. cable_monitor.py does the stable copy.
& $exe /SetListenToThisDevice "CABLE Output" 0

# Route the translator TTS into Teams, and keep levels high enough for STT.
& $exe /SetAppDefault "CABLE Input" all "python.exe"
& $exe /SetVolume "CABLE Input" 95
& $exe /SetVolume "CABLE Output" 100
& $exe /SetVolume $speaker 85

Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like "*cable_monitor.py*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}
Start-Process -FilePath $python -ArgumentList "cable_monitor.py" -WorkingDirectory $PSScriptRoot -WindowStyle Hidden | Out-Null

Write-Host "Audio configured:"
Write-Host "- Windows default output: $speaker"
Write-Host "- Chrome/Edge/Teams/WebView output: CABLE Input"
Write-Host "- Teams Translator/Python output: CABLE Input"
Write-Host "- Monitor: cable_monitor.py copies CABLE Output -> $speaker"
Write-Host "- Teams microphone should be: CABLE Output"
