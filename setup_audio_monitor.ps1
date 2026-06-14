param(
    [switch]$Restore
)

$ErrorActionPreference = "Stop"

$toolDir = Join-Path $env:TEMP "soundvolumeview"
$exe = Join-Path $toolDir "SoundVolumeView.exe"
$zip = Join-Path $toolDir "soundvolumeview-x64.zip"
$stateDir = Join-Path $env:LOCALAPPDATA "TeamsTranslator"
$profilePath = Join-Path $stateDir "audio-setup-profile.svp"

function Invoke-SoundVolumeView {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $exe @Arguments | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "SoundVolumeView failed: $($Arguments -join ' ')"
    }
}

function Get-PythonCommand {
    $python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (Test-Path $python) {
        return $python
    }
    return "python"
}

function Ensure-SoundVolumeView {
    if (-not (Test-Path $exe)) {
        New-Item -ItemType Directory -Force -Path $toolDir | Out-Null
        Invoke-WebRequest -Uri "https://www.nirsoft.net/utils/soundvolumeview-x64.zip" -OutFile $zip
        Expand-Archive -LiteralPath $zip -DestinationPath $toolDir -Force
    }
}

function Get-AudioDeviceSnapshot {
    $python = Get-PythonCommand
    $probe = Join-Path $PSScriptRoot "audio_device_probe.py"
    return & $python $probe | ConvertFrom-Json
}

function Get-SoundVolumeViewDevices {
    $csvPath = Join-Path $env:TEMP "soundvolumeview-devices.csv"
    & $exe /scomma $csvPath | Out-Null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $csvPath)) {
        throw "Failed to enumerate audio devices with SoundVolumeView."
    }

    try {
        return Import-Csv -LiteralPath $csvPath
    } finally {
        Remove-Item -LiteralPath $csvPath -Force -ErrorAction SilentlyContinue
    }
}

function Get-BestSpeakerNameFromSoundVolumeView {
    $devices = Get-SoundVolumeViewDevices
    $renderDevices = $devices | Where-Object {
        $_.Type -eq "Device" -and
        $_.Direction -eq "Render" -and
        $_.Name -and
        $_.Name -notmatch "(?i)cable"
    }

    if (-not $renderDevices) {
        return $null
    }

    $preferredNames = @(
        "Speakers/Headphones",
        "FxSound Speakers",
        "Speakers"
    )
    foreach ($preferred in $preferredNames) {
        $match = $renderDevices | Where-Object { $_.Name -eq $preferred } | Select-Object -First 1
        if ($match) {
            return [string]$match.Name
        }
    }

    $active = $renderDevices | Where-Object { $_.Default -eq "Render" -or $_."Default Multimedia" -eq "Render" } | Select-Object -First 1
    if ($active) {
        return [string]$active.Name
    }

    return [string]($renderDevices | Select-Object -First 1).Name
}

function Get-CurrentRenderSpeakerNameFromSoundVolumeView {
    $devices = Get-SoundVolumeViewDevices
    $active = $devices | Where-Object {
        $_.Type -eq "Device" -and
        $_.Direction -eq "Render" -and
        $_.Default -eq "Render"
    } | Select-Object -First 1

    if ($active -and $active.Name -and $active.Name -notmatch "(?i)cable") {
        return [string]$active.Name
    }

    return $null
}

function Get-PreferredOutputDevice {
    $deviceInfo = Get-AudioDeviceSnapshot
    if ($deviceInfo.current -and $deviceInfo.current -notmatch "(?i)cable") {
        return [string]$deviceInfo.current
    }
    if ($deviceInfo.best) {
        return [string]$deviceInfo.best
    }
    return $null
}

function Normalize-DeviceName {
    param([string]$Name)

    if (-not $Name) {
        return $null
    }

    $trimmed = $Name.Trim()
    $idx = $trimmed.IndexOf(" (")
    if ($idx -gt 0) {
        return $trimmed.Substring(0, $idx).Trim()
    }
    return $trimmed
}

function Clear-AppAudioOverrides {
    $targetPattern = '(?i)(chrome\.exe|msedge\.exe|ms-teams\.exe|msteams\.exe|teams\.exe|msedgewebview2\.exe|python\.exe|firefox\.exe)'
    $baseKey = 'HKCU:\Software\Microsoft\Multimedia\Audio\DefaultEndpoint'
    if (-not (Test-Path $baseKey)) {
        return
    }

    Get-ChildItem -LiteralPath $baseKey -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $defaultValue = $_.GetValue('')
            if ($defaultValue -and $defaultValue -match $targetPattern) {
                Remove-Item -LiteralPath $_.PSPath -Recurse -Force -ErrorAction Stop
            }
        } catch {
            continue
        }
    }
}

function Stop-CableMonitor {
    Get-CimInstance Win32_Process |
        Where-Object { $_.CommandLine -like "*cable_monitor.py*" } |
        ForEach-Object {
            try {
                Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop
            } catch {
                continue
            }
        }
}

function Get-TeamsTranslatorPythonProcessIds {
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -match '(?i)^python(w)?\.exe$' -and
            $_.CommandLine -match [regex]::Escape($PSScriptRoot)
        } |
        Select-Object -ExpandProperty ProcessId -ErrorAction SilentlyContinue
}

function Start-CableMonitor {
    param(
        [Parameter(Mandatory = $true)]
        [string]$OutputDevice
    )

    $python = Get-PythonCommand
    Start-Process -FilePath $python -ArgumentList @(
        "cable_monitor.py",
        "--output-device",
        $OutputDevice
    ) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden | Out-Null
}

function Restore-AudioState {
    Stop-CableMonitor
    
    # 1. Load saved profile if exists
    if (Test-Path $profilePath) {
        try {
            Invoke-SoundVolumeView -Arguments @("/LoadProfile", $profilePath)
            Remove-Item -LiteralPath $profilePath -Force -ErrorAction SilentlyContinue
            Write-Host "Restored previous audio profile."
        } catch {
            Write-Host "Failed to load profile, falling back to auto-detection: $_"
        }
    }

    # 2. Re-detect and set fallback speaker globally just in case
    $deviceInfo = Get-AudioDeviceSnapshot
    $currentSpeaker = Get-CurrentRenderSpeakerNameFromSoundVolumeView
    $fallbackSpeaker = Get-BestSpeakerNameFromSoundVolumeView
    if (-not $fallbackSpeaker -and $currentSpeaker) {
        $fallbackSpeaker = $currentSpeaker
    } elseif (-not $fallbackSpeaker -and $deviceInfo.current -and $deviceInfo.current -notmatch "(?i)cable") {
        $fallbackSpeaker = [string]$deviceInfo.current
    } elseif (-not $fallbackSpeaker -and $deviceInfo.best) {
        $fallbackSpeaker = [string]$deviceInfo.best
    }

    if ($fallbackSpeaker) {
        Invoke-SoundVolumeView -Arguments @("/SetDefault", $fallbackSpeaker, "all")
    }

    # 3. Explicitly reset app defaults to system default ("")
    $appTargets = @(
        "chrome.exe",
        "msedge.exe",
        "ms-teams.exe",
        "MSTeams.exe",
        "Teams.exe",
        "msedgewebview2.exe",
        "python.exe"
    )
    foreach ($target in $appTargets) {
        try {
            Invoke-SoundVolumeView -Arguments @("/SetAppDefault", "DefaultRenderDevice", "all", $target)
        } catch {}
    }

    foreach ($processId in @(Get-TeamsTranslatorPythonProcessIds)) {
        try {
            Invoke-SoundVolumeView -Arguments @("/SetAppDefault", "DefaultRenderDevice", "all", [string]$processId)
        } catch {}
    }

    Invoke-SoundVolumeView -Arguments @("/SetListenToThisDevice", "CABLE Output", "0")
    Clear-AppAudioOverrides
    Write-Host "Audio restored to the previous Windows profile."
}

function Apply-AudioState {
    New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
    $deviceInfo = Get-AudioDeviceSnapshot
    $currentSpeaker = Get-CurrentRenderSpeakerNameFromSoundVolumeView
    if (-not (Test-Path $profilePath) -and $currentSpeaker) {
        Invoke-SoundVolumeView -Arguments @("/SaveProfile", $profilePath)
    }

    $speaker = $currentSpeaker
    if (-not $speaker) {
        $speaker = Get-BestSpeakerNameFromSoundVolumeView
    }
    if (-not $speaker -and $deviceInfo.current -and $deviceInfo.current -notmatch "(?i)cable") {
        $speaker = [string]$deviceInfo.current
    } elseif (-not $speaker -and $deviceInfo.best) {
        $speaker = [string]$deviceInfo.best
    }
    if (-not $speaker) {
        throw "No usable output device found. Check your Windows sound devices."
    }

    Invoke-SoundVolumeView -Arguments @("/SetDefault", $speaker, "all")

    $appTargets = @(
        "chrome.exe",
        "msedge.exe",
        "ms-teams.exe",
        "MSTeams.exe",
        "Teams.exe",
        "msedgewebview2.exe"
    )
    foreach ($target in $appTargets) {
        Invoke-SoundVolumeView -Arguments @("/SetAppDefault", "CABLE Input", "all", $target)
    }

    Get-Process chrome,msedge,ms-teams,MSTeams,Teams,msedgewebview2 -ErrorAction SilentlyContinue | ForEach-Object {
        Invoke-SoundVolumeView -Arguments @("/SetAppDefault", "CABLE Input", "all", $_.Id)
    }

    foreach ($processId in @(Get-TeamsTranslatorPythonProcessIds)) {
        try {
            Invoke-SoundVolumeView -Arguments @("/SetAppDefault", "CABLE Input", "all", [string]$processId)
        } catch {}
    }

    Invoke-SoundVolumeView -Arguments @("/SetListenToThisDevice", "CABLE Output", "0")
    Invoke-SoundVolumeView -Arguments @("/SetAppDefault", "CABLE Input", "all", "python.exe")
    Invoke-SoundVolumeView -Arguments @("/SetVolume", "CABLE Input", "95")
    Invoke-SoundVolumeView -Arguments @("/SetVolume", "CABLE Output", "100")
    Invoke-SoundVolumeView -Arguments @("/SetVolume", $speaker, "85")

    Stop-CableMonitor
    Start-CableMonitor -OutputDevice $speaker

    Write-Host "Audio configured:"
    Write-Host "- Windows default output: $speaker"
    Write-Host "- Chrome/Edge/Teams/WebView output: CABLE Input"
    Write-Host "- Teams Translator/Python output: CABLE Input"
    Write-Host "- Monitor: cable_monitor.py copies CABLE Output -> $speaker"
    Write-Host "- Teams microphone should be: CABLE Output"
}

Ensure-SoundVolumeView

if ($Restore) {
    Restore-AudioState
    return
}

Apply-AudioState
