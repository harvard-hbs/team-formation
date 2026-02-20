# Build the Python backend into a standalone bundle using PyInstaller.
#
# Usage:
#   cd desktop
#   .\scripts\build-python.ps1
#
# Prerequisites:
#   pip install pyinstaller
#   pip install -e ..   (or ensure team_formation is importable)
#
# Output:
#   desktop\python-dist\  (the bundled backend ready for Electron packaging)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DesktopDir = Split-Path -Parent $ScriptDir
$ProjectDir = Split-Path -Parent $DesktopDir

Write-Host "=== Building Python backend ==="
Write-Host "Project root: $ProjectDir"
Write-Host "Desktop dir:  $DesktopDir"

# Ensure we're in the desktop directory for spec file paths
Set-Location $DesktopDir

# Clean previous build
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "python-dist") { Remove-Item -Recurse -Force "python-dist" }

# Run PyInstaller with the spec file
Write-Host "Running PyInstaller..."
pyinstaller team_formation_api.spec --noconfirm

# Move the output to the expected location
Write-Host "Moving bundle to python-dist..."
Move-Item "dist\team_formation_api" "python-dist"

# Verify the bundle
if (Test-Path "python-dist\team_formation_api.exe") {
    Write-Host "Bundle created successfully: python-dist\team_formation_api.exe"
} else {
    Write-Host "ERROR: Bundle executable not found!"
    exit 1
}

# Quick smoke test
Write-Host "Running smoke test..."
$backendProcess = Start-Process -FilePath "python-dist\team_formation_api.exe" -PassThru -NoNewWindow

Start-Sleep -Seconds 5

try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "Smoke test PASSED: backend responds to /health"
    }
} catch {
    Write-Host "WARNING: Smoke test failed (backend may need more startup time)"
}

# Clean up
Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue

# Clean up PyInstaller artifacts
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

Write-Host "=== Python backend build complete ==="
Write-Host "Output: $DesktopDir\python-dist\"
