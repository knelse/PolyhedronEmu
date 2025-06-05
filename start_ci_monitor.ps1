# Start CI Monitor for PolyhedronEmu
# This script starts the CI monitor with the appropriate configuration

param(
    [switch]$Background,
    [int]$PollInterval = 60,
    [string]$GodotPath = "D:\Games\Godot\Godot_v4.4.1-stable_win64.exe"
)

Write-Host "Starting PolyhedronEmu CI Monitor..." -ForegroundColor Green
Write-Host "Poll Interval: $PollInterval seconds" -ForegroundColor Cyan
Write-Host "Godot Path: $GodotPath" -ForegroundColor Cyan

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "Error: Python not found. Please install Python 3.7+" -ForegroundColor Red
    exit 1
}

# Check if required packages are installed
$requiredPackages = @("flake8", "pytest")
foreach ($package in $requiredPackages) {
    try {
        python -m $package --version 2>&1 | Out-Null
        Write-Host "✅ $package is installed" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ $package not found. Installing..." -ForegroundColor Yellow
        pip install $package
    }
}

# Check if Godot exists
if (-not (Test-Path $GodotPath)) {
    Write-Host "Warning: Godot not found at $GodotPath" -ForegroundColor Yellow
    Write-Host "You may need to specify the correct path with --godot-exe" -ForegroundColor Yellow
}
else {
    Write-Host "✅ Godot found" -ForegroundColor Green
}

# Build command
$command = "python ci_monitor.py --poll-interval $PollInterval"
if (Test-Path $GodotPath) {
    $command += " --godot-exe `"$GodotPath`""
}

Write-Host ""
Write-Host "Command: $command" -ForegroundColor Gray
Write-Host ""

if ($Background) {
    Write-Host "Starting in background..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-Command", $command -WindowStyle Hidden
    Write-Host "CI Monitor started in background. Check logs/ci_monitor.log for output." -ForegroundColor Green
}
else {
    Write-Host "Starting CI Monitor (Press Ctrl+C to stop)..." -ForegroundColor Yellow
    Write-Host ""
    Invoke-Expression $command
} 