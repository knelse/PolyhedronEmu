# PolyhedronEmu Local Build Script
# This script helps set up and build the project locally

param(
    [switch]$Setup,
    [switch]$Build,
    [switch]$Run,
    [switch]$Clean
)

# Configuration
$GODOT_VERSION = "4.4.1-stable"
$GODOT_URL = "https://github.com/godotengine/godot/releases/download/4.4.1-stable/Godot_v4.4.1-stable_win64.exe"
$EXPORT_TEMPLATES_URL = "https://github.com/godotengine/godot/releases/download/4.4.1-stable/Godot_v4.4.1-stable_export_templates.tpz"
$TOOLS_DIR = "D:\Games\Godot"
$GODOT_EXE = "$TOOLS_DIR\Godot_v4.4.1-stable_win64.exe"
$BUILDS_DIR = ".builds"

function Initialize-Environment {
    Write-Host "Setting up build environment..." -ForegroundColor Green
    
    # Create directories
    if (-not (Test-Path $TOOLS_DIR)) {
        New-Item -ItemType Directory -Path $TOOLS_DIR -Force
        Write-Host "Created tools directory"
    }
    
    if (-not (Test-Path $BUILDS_DIR)) {
        New-Item -ItemType Directory -Path $BUILDS_DIR -Force
        Write-Host "Created builds directory"
    }
    
    # Check if Godot exists
    if (-not (Test-Path $GODOT_EXE)) {
        Write-Host "Godot not found. Please download manually:" -ForegroundColor Yellow
        Write-Host "1. Go to: $GODOT_URL"
        Write-Host "2. Save as: $GODOT_EXE"
        Write-Host "3. Go to: $EXPORT_TEMPLATES_URL"
        Write-Host "4. Save export templates to your Godot data folder"
        Write-Host ""
        Write-Host "Godot data folder location:"
        Write-Host "  Windows: %APPDATA%\Godot\export_templates\$GODOT_VERSION\"
        return $false
    }
    
    Write-Host "Environment setup complete!" -ForegroundColor Green
    return $true
}

function Clear-Project {
    Write-Host "Cleaning project..." -ForegroundColor Green
    
    # Remove .godot folder (Godot's cache/import folder)
    if (Test-Path ".godot") {
        Write-Host "Removing .godot cache folder..." -ForegroundColor Yellow
        Remove-Item ".godot" -Recurse -Force
        Write-Host "✅ .godot folder removed" -ForegroundColor Green
    }
    
    # Remove builds
    if (Test-Path $BUILDS_DIR) {
        Write-Host "Removing builds folder..." -ForegroundColor Yellow
        Remove-Item "$BUILDS_DIR\*"  -Recurse -Force
        Write-Host "✅ Builds cleared" -ForegroundColor Green
    }
    
    Write-Host "Clean complete! Run -Build to rebuild." -ForegroundColor Green
}

function Build-Project {
    Write-Host "Building project..." -ForegroundColor Green
    
    if (-not (Test-Path $GODOT_EXE)) {
        Write-Host "Error: Godot executable not found at $GODOT_EXE" -ForegroundColor Red
        Write-Host "Run with -Setup flag first"
        return $false
    }
    
    # Verify py4godot files
    Write-Host "Verifying py4godot files..." -ForegroundColor Yellow
    $pythonDll = "addons\py4godot\cpython-3.12.4-windows64\python\pythonscript.dll"
    if (-not (Test-Path $pythonDll)) {
        Write-Host "Error: pythonscript.dll not found at $pythonDll" -ForegroundColor Red
        return $false
    }
    
    # Clean up any backup files that might cause issues
    $backupDll = "addons\py4godot\cpython-3.12.4-windows64\python\~pythonscript.dll"
    if (Test-Path $backupDll) {
        Write-Host "Removing backup file: $backupDll" -ForegroundColor Yellow
        Remove-Item $backupDll -Force
    }
    
    # Import resources first (headless)
    Write-Host "Importing project resources..." -ForegroundColor Yellow
    & $GODOT_EXE --headless --import 2>&1 | Tee-Object -Variable importOutput
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: Resource import had issues (exit code: $LASTEXITCODE)" -ForegroundColor Yellow
        # Check for specific py4godot errors
        if ($importOutput -match "python\.gdextension") {
            Write-Host "py4godot extension error detected. Attempting to fix..." -ForegroundColor Yellow
            # Force reimport of the extension
            & $GODOT_EXE --headless --quit 2>&1 | Out-Null
        }
    }
    
    # Export the project
    Write-Host "Exporting project..." -ForegroundColor Yellow
    & $GODOT_EXE --headless --export-release "Win64" "$BUILDS_DIR\PolyhedronEmu_win64.exe" 2>&1 | Tee-Object -Variable exportOutput
    
    # Copy required py4godot addon and runtime files for non-embedded PCK
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Copying py4godot addon and runtime files..." -ForegroundColor Yellow
        
        # Helper function to check if file needs copying
        function Should-CopyFile($srcFile, $destFile) {
            if (-not (Test-Path $destFile)) {
                return $true
            }
            $srcTime = (Get-Item $srcFile).LastWriteTime
            $destTime = (Get-Item $destFile).LastWriteTime
            return $srcTime -gt $destTime
        }
        
        # Helper function to copy file if needed
        function Copy-IfNewer($srcPath, $destPath, $itemName) {
            $copied = $false
            if (Test-Path $srcPath -PathType Leaf) {
                # Single file
                if (Should-CopyFile $srcPath $destPath) {
                    $destDir = Split-Path $destPath -Parent
                    if (-not (Test-Path $destDir)) {
                        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                    }
                    Copy-Item $srcPath $destPath -Force
                    Write-Host "  ✅ Updated $itemName" -ForegroundColor Green
                    $copied = $true
                } else {
                    Write-Host "  ⏭️  Skipped $itemName (up to date)" -ForegroundColor Gray
                }
            } elseif (Test-Path $srcPath -PathType Container) {
                # Directory - check each file recursively
                $anyFilesCopied = $false
                Get-ChildItem $srcPath -Recurse -File | ForEach-Object {
                    $relativePath = $_.FullName.Substring($srcPath.Length + 1)
                    $destFilePath = Join-Path $destPath $relativePath
                    if (Should-CopyFile $_.FullName $destFilePath) {
                        $destFileDir = Split-Path $destFilePath -Parent
                        if (-not (Test-Path $destFileDir)) {
                            New-Item -ItemType Directory -Path $destFileDir -Force | Out-Null
                        }
                        Copy-Item $_.FullName $destFilePath -Force
                        $anyFilesCopied = $true
                    }
                }
                if ($anyFilesCopied) {
                    Write-Host "  ✅ Updated $itemName" -ForegroundColor Green
                    $copied = $true
                } else {
                    Write-Host "  ⏭️  Skipped $itemName (up to date)" -ForegroundColor Gray
                }
            }
            return $copied
        }
        
        # Copy py4godot addon with Windows64 runtime only
        $py4godotSrc = "addons\py4godot"
        $py4godotDest = "$BUILDS_DIR\addons\py4godot"
        
        if (Test-Path $py4godotSrc) {
            if (-not (Test-Path "$BUILDS_DIR\addons")) {
                New-Item -ItemType Directory -Path "$BUILDS_DIR\addons" -Force | Out-Null
            }
            if (-not (Test-Path $py4godotDest)) {
                New-Item -ItemType Directory -Path $py4godotDest -Force | Out-Null
            }
            
            # Copy all py4godot files except platform runtime directories and .tmp/.TMP files
            $py4godotUpdated = $false
            Get-ChildItem $py4godotSrc | ForEach-Object {
                if ($_.Name -notin @("cpython-3.12.4-linux64", "cpython-3.12.4-linuxarm64", "cpython-3.12.4-darwin64") -and $_.Extension -notin @(".tmp", ".TMP")) {
                    $itemDest = Join-Path $py4godotDest $_.Name
                    if (Copy-IfNewer $_.FullName $itemDest $_.Name) {
                        $py4godotUpdated = $true
                    }
                }
            }
            
            if ($py4godotUpdated) {
                Write-Host "  ✅ py4godot addon updated (Windows64 runtime only)" -ForegroundColor Green
            } else {
                Write-Host "  ⏭️  py4godot addon up to date" -ForegroundColor Gray
            }
        }
        
        # Copy server modules for Python imports
        $serverSrc = "server"
        $serverDest = "$BUILDS_DIR\server"
        
        if (Test-Path $serverSrc) {
            if (-not (Test-Path $serverDest)) {
                New-Item -ItemType Directory -Path $serverDest -Force | Out-Null
            }
            $serverUpdated = $false
            Get-ChildItem "$serverSrc\*.py" | Where-Object { $_.Extension -notin @(".tmp", ".TMP") } | ForEach-Object {
                $destFile = Join-Path $serverDest $_.Name
                if (Should-CopyFile $_.FullName $destFile) {
                    Copy-Item $_.FullName $destFile -Force
                    $serverUpdated = $true
                    Write-Host "  ✅ Updated $($_.Name)" -ForegroundColor Green
                } else {
                    Write-Host "  ⏭️  Skipped $($_.Name) (up to date)" -ForegroundColor Gray
                }
            }
            if (-not $serverUpdated) {
                Write-Host "  ⏭️  All server modules up to date" -ForegroundColor Gray
            }
        }
        
        # Copy all Python files from root (excluding test files, ci_monitor.py, and .tmp/.TMP files)
        $pythonFiles = Get-ChildItem -Filter "*.py" -File | Where-Object { $_.Name -notlike "*test*" -and $_.Name -ne "ci_monitor.py" -and $_.Extension -notin @(".tmp", ".TMP") }
        $rootPyUpdated = $false
        foreach ($pyFile in $pythonFiles) {
            $destFile = Join-Path $BUILDS_DIR $pyFile.Name
            if (Should-CopyFile $pyFile.FullName $destFile) {
                Copy-Item $pyFile.FullName $destFile -Force
                Write-Host "  ✅ Updated $($pyFile.Name)" -ForegroundColor Green
                $rootPyUpdated = $true
            } else {
                Write-Host "  ⏭️  Skipped $($pyFile.Name) (up to date)" -ForegroundColor Gray
            }
        }
        if (-not $rootPyUpdated -and $pythonFiles.Count -gt 0) {
            Write-Host "  ⏭️  All root Python files up to date" -ForegroundColor Gray
        }
        
        # Copy server_config.json
        if (Test-Path "server_config.json") {
            $destConfigFile = Join-Path $BUILDS_DIR "server_config.json"
            if (Should-CopyFile "server_config.json" $destConfigFile) {
                Copy-Item "server_config.json" $destConfigFile -Force
                Write-Host "  ✅ Updated server_config.json" -ForegroundColor Green
            } else {
                Write-Host "  ⏭️  Skipped server_config.json (up to date)" -ForegroundColor Gray
            }
        }
        
        # Copy .godot/imported folder for processed assets
        if (Test-Path ".godot/imported") {
            $importedDest = "$BUILDS_DIR\.godot\imported"
            if (-not (Test-Path "$BUILDS_DIR\.godot")) {
                New-Item -ItemType Directory -Path "$BUILDS_DIR\.godot" -Force | Out-Null
            }
            if (-not (Test-Path $importedDest)) {
                New-Item -ItemType Directory -Path $importedDest -Force | Out-Null
            }
            Copy-Item ".godot\imported\*" $importedDest -Force -Recurse
            Write-Host "  ✅ Copied .godot/imported assets" -ForegroundColor Green
        }
        
        # Copy project configuration files
        $configFiles = @("project.godot", "export_presets.cfg")
        $configUpdated = $false
        foreach ($config in $configFiles) {
            if (Test-Path $config) {
                $destConfigFile = Join-Path $BUILDS_DIR $config
                if (Should-CopyFile $config $destConfigFile) {
                    Copy-Item $config $destConfigFile -Force
                    Write-Host "  ✅ Updated $config" -ForegroundColor Green
                    $configUpdated = $true
                } else {
                    Write-Host "  ⏭️  Skipped $config (up to date)" -ForegroundColor Gray
                }
            }
        }
        if (-not $configUpdated) {
            Write-Host "  ⏭️  All config files up to date" -ForegroundColor Gray
        }
        
        # Copy any Python packages/subdirectories (excluding tests and .tmp/.TMP files)
        $pythonDirs = Get-ChildItem -Directory | Where-Object { $_.Name -notlike "*test*" -and $_.Name -notin @("addons", "server", "logs", ".builds", ".godot") }
        foreach ($pyDir in $pythonDirs) {
            if ((Get-ChildItem "$($pyDir.FullName)\*.py" -ErrorAction SilentlyContinue).Count -gt 0) {
                $destDir = "$BUILDS_DIR\$($pyDir.Name)"
                if (-not (Test-Path $destDir)) {
                    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                }
                
                $packageUpdated = $false
                # Copy files excluding .tmp/.TMP files, only if newer
                Get-ChildItem "$($pyDir.FullName)" -Recurse -File | Where-Object { $_.Extension -notin @(".tmp", ".TMP") } | ForEach-Object {
                    $relativePath = $_.FullName.Substring($pyDir.FullName.Length + 1)
                    $destFilePath = Join-Path $destDir $relativePath
                    if (Should-CopyFile $_.FullName $destFilePath) {
                        $destFileDir = Split-Path $destFilePath -Parent
                        if (-not (Test-Path $destFileDir)) {
                            New-Item -ItemType Directory -Path $destFileDir -Force | Out-Null
                        }
                        Copy-Item $_.FullName $destFilePath -Force
                        $packageUpdated = $true
                    }
                }
                
                if ($packageUpdated) {
                    Write-Host "  ✅ Updated Python package: $($pyDir.Name)" -ForegroundColor Green
                } else {
                    Write-Host "  ⏭️  Skipped Python package: $($pyDir.Name) (up to date)" -ForegroundColor Gray
                }
            }
        }
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Build successful!" -ForegroundColor Green
        
        # Show info for main executable
        if (Test-Path "$BUILDS_DIR\PolyhedronEmu_win64.exe") {
            $fileInfo = Get-Item "$BUILDS_DIR\PolyhedronEmu_win64.exe"
            Write-Host "  ✅ Main: PolyhedronEmu_win64.exe ($([math]::Round($fileInfo.Length / 1MB, 2)) MB)" -ForegroundColor Green
        }
        
        # Show info for console version (auto-generated when console wrapper is enabled)
        if (Test-Path "$BUILDS_DIR\PolyhedronEmu_win64.console.exe") {
            $consoleInfo = Get-Item "$BUILDS_DIR\PolyhedronEmu_win64.console.exe"
            Write-Host "  ✅ Console: PolyhedronEmu_win64.console.exe ($([math]::Round($consoleInfo.Length / 1KB, 2)) KB)" -ForegroundColor Green
        }
        
        return $true
    } else {
        Write-Host "Build failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        
        # Show specific error information
        if ($exportOutput -match "ERROR.*python\.gdextension") {
            Write-Host "py4godot GDExtension error during export!" -ForegroundColor Red
            Write-Host "Try: Delete .godot folder and rebuild" -ForegroundColor Yellow
        }
        
        # Show last few lines of output for debugging
        Write-Host "Last build output:" -ForegroundColor Yellow
        $exportOutput | Select-Object -Last 5 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        
        return $false
    }
}

function Start-Project {
    $exePath = "$BUILDS_DIR\PolyhedronEmu_win64.exe"
    
    if (-not (Test-Path $exePath)) {
        Write-Host "Error: Built executable not found at $exePath" -ForegroundColor Red
        Write-Host "Run with -Build flag first"
        return
    }
    
    Write-Host "Running project..." -ForegroundColor Green
    
    # Change to builds directory so the executable can find its runtime dependencies
    $currentDir = Get-Location
    try {
        Set-Location $BUILDS_DIR
        & ".\PolyhedronEmu_win64.exe"
    }
    finally {
        Set-Location $currentDir
    }
}

# Main execution
if ($Setup) {
    Initialize-Environment
}
elseif ($Build) {
    if (Initialize-Environment) {
        Build-Project
    }
}
elseif ($Run) {
    Start-Project
}
elseif ($Clean) {
    Clear-Project
}
else {
    Write-Host "PolyhedronEmu Build Script" -ForegroundColor Cyan
    Write-Host "Usage:"
    Write-Host "  .\build_local.ps1 -Setup    # Set up build environment"
    Write-Host "  .\build_local.ps1 -Build    # Clean cache and builds and build the project"
    Write-Host "  .\build_local.ps1 -Run      # Run the built executable"
    Write-Host "  .\build_local.ps1 -Clean    # Clean cache and builds"
    Write-Host ""
    Write-Host "Current Status:"
    
    if (Test-Path $GODOT_EXE) {
        Write-Host "  ✅ Godot: Found at $GODOT_EXE" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Godot: Not found" -ForegroundColor Red
    }
    
    if (Test-Path "$BUILDS_DIR\PolyhedronEmu_win64.exe") {
        $fileInfo = Get-Item "$BUILDS_DIR\PolyhedronEmu_win64.exe"
        Write-Host "  ✅ Main Build: Found ($([math]::Round($fileInfo.Length / 1MB, 2)) MB, $($fileInfo.CreationTime))" -ForegroundColor Green
        
        if (Test-Path "$BUILDS_DIR\PolyhedronEmu_win64.console.exe") {
            $consoleInfo = Get-Item "$BUILDS_DIR\PolyhedronEmu_win64.console.exe"
            Write-Host "  ✅ Console Build: Found ($([math]::Round($consoleInfo.Length / 1KB, 2)) KB)" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  Console Build: Not found" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ❌ Build: Not found" -ForegroundColor Red
    }
}
