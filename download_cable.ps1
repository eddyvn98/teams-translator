$url = "https://download.vb-audio.com/Download_Files/VBCABLE_Driver_Pack43.zip"
$downloadDir = [System.IO.Path]::Combine($env:USERPROFILE, "Downloads")
$zipFile = [System.IO.Path]::Combine($downloadDir, "VBCABLE_Driver_Pack43.zip")
$extractDir = [System.IO.Path]::Combine($downloadDir, "VB_Cable_Installer")

Write-Host "-------------------------------------------------------"
Write-Host "Dang tai VB-CABLE Virtual Audio Driver..."
Write-Host "URL: $url"
Write-Host "-------------------------------------------------------"

try {
    if (Test-Path $extractDir) {
        Remove-Item -Path $extractDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    New-Item -ItemType Directory -Path $extractDir -Force | Out-Null

    # Download using Invoke-WebRequest
    Write-Host "Dang download zip file vao: $zipFile"
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $url -OutFile $zipFile -TimeoutSec 60 -ErrorAction Stop
    
    Write-Host "Dang giai nen vao thu muc: $extractDir"
    Expand-Archive -Path $zipFile -DestinationPath $extractDir -Force
    
    Write-Host "-------------------------------------------------------"
    Write-Host "DOWNLOAD VA GIAI NEN THANH CONG!"
    
    # Clean up the zip file
    Remove-Item -Path $zipFile -Force
    
    # Open the folder in Explorer so user can install
    Invoke-Item $extractDir
    Write-Host "Da tu dong mo thu muc chua bo cai dat cho ban."
} catch {
    Write-Error "Xay ra loi: $_"
}
