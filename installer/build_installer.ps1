# PowerShell script to build InLegalDesk installer
# Requires: Python 3.8+, Inno Setup 6+

param(
    [string]$BuildType = "onedir",  # onefile or onedir
    [string]$PythonPath = "python",
    [string]$InnoSetupPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    [switch]$IncludeModels = $false  # Include AI models in installer
)

Write-Host "Building InLegalDesk Installer..." -ForegroundColor Green
Write-Host "Build Type: $BuildType" -ForegroundColor Yellow

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Blue

# Check Python
try {
    $pythonVersion = & $PythonPath --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python not found at $PythonPath" -ForegroundColor Red
    exit 1
}

# Check Inno Setup
if (-not (Test-Path $InnoSetupPath)) {
    Write-Host "Error: Inno Setup not found at $InnoSetupPath" -ForegroundColor Red
    Write-Host "Please install Inno Setup 6 or update the path" -ForegroundColor Yellow
    exit 1
}
Write-Host "Found Inno Setup at $InnoSetupPath" -ForegroundColor Green

# Set up paths
$rootDir = Split-Path -Parent $PSScriptRoot
$desktopDir = Join-Path $rootDir "desktop"
$backendDir = Join-Path $rootDir "backend"
$installerDir = $PSScriptRoot
$buildDir = Join-Path $installerDir "build"
$distDir = Join-Path $installerDir "dist"
$outputDir = Join-Path $installerDir "output"

# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Blue
if (Test-Path $buildDir) { Remove-Item $buildDir -Recurse -Force }
if (Test-Path $distDir) { Remove-Item $distDir -Recurse -Force }
if (Test-Path $outputDir) { Remove-Item $outputDir -Recurse -Force }

# Create directories
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
New-Item -ItemType Directory -Force -Path $distDir | Out-Null
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

# Copy backend to desktop/server
Write-Host "Copying backend files to desktop/server..." -ForegroundColor Blue
$serverDir = Join-Path $desktopDir "server"
if (Test-Path $serverDir) { Remove-Item $serverDir -Recurse -Force }
Copy-Item $backendDir $serverDir -Recurse

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Blue
$venvDir = Join-Path $buildDir "venv"
& $PythonPath -m venv $venvDir
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$venvPip = Join-Path $venvDir "Scripts\pip.exe"

# Install requirements
Write-Host "Installing desktop requirements..." -ForegroundColor Blue
$requirementsPath = Join-Path $desktopDir "requirements.txt"
& $venvPip install -r $requirementsPath

# Install PyInstaller
Write-Host "Installing PyInstaller..." -ForegroundColor Blue
& $venvPip install pyinstaller

# Download AI models for offline installer (if requested)
if ($IncludeModels) {
    Write-Host "Preparing AI models for offline installer..." -ForegroundColor Blue
    Write-Host "This will download ~2GB of AI models..." -ForegroundColor Yellow
    
    Push-Location $backendDir
    & $venvPython model_manager.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Model download failed" -ForegroundColor Red
        exit 1
    }
    Pop-Location
    
    Write-Host "✅ AI models prepared for bundling" -ForegroundColor Green
} else {
    Write-Host "Skipping AI model bundling (models will download on first run)" -ForegroundColor Yellow
}

# Build executable
Write-Host "Building executable with PyInstaller..." -ForegroundColor Blue
Push-Location $desktopDir

$pyinstallerArgs = @(
    "--noconfirm"
    "--name", "InLegalDesk"
    "--add-data", "server;server"
    "--add-data", ".env.sample;.env.sample"
    "--icon", "..\installer\assets\icon.ico"
    "--distpath", $distDir
    "--workpath", $buildDir
)

# Add AI models if requested
if ($IncludeModels -and (Test-Path "..\installer\models_package")) {
    $pyinstallerArgs += "--add-data", "..\installer\models_package;models"
    Write-Host "Including AI models in installer..." -ForegroundColor Green
}

if ($BuildType -eq "onefile") {
    $pyinstallerArgs += "--onefile"
} else {
    $pyinstallerArgs += "--onedir"
}

$pyinstallerArgs += "main.py"

& $venvPython -m PyInstaller @pyinstallerArgs

Pop-Location

# Check if build succeeded
$exePath = if ($BuildType -eq "onefile") {
    Join-Path $distDir "InLegalDesk.exe"
} else {
    Join-Path $distDir "InLegalDesk\InLegalDesk.exe"
}

if (-not (Test-Path $exePath)) {
    Write-Host "Error: PyInstaller build failed" -ForegroundColor Red
    exit 1
}

Write-Host "Executable built successfully: $exePath" -ForegroundColor Green

# Build installer with Inno Setup
Write-Host "Building installer with Inno Setup..." -ForegroundColor Blue
$issScript = Join-Path $installerDir "InLegalDesk.iss"

# Update ISS script with build type
$issContent = Get-Content $issScript -Raw
$issContent = $issContent -replace "#define BuildType .*", "#define BuildType `"$BuildType`""
$issContent = $issContent -replace "#define DistDir .*", "#define DistDir `"$distDir`""
Set-Content $issScript $issContent

# Compile installer
& $InnoSetupPath $issScript

# Check if installer was created
$installerPath = Join-Path $outputDir "InLegalDesk_Installer.exe"
if (Test-Path $installerPath) {
    Write-Host "Installer created successfully: $installerPath" -ForegroundColor Green
    
    # Show file size
    $size = (Get-Item $installerPath).Length / 1MB
    Write-Host "Installer size: $([math]::Round($size, 2)) MB" -ForegroundColor Yellow
    
} else {
    Write-Host "Error: Installer creation failed" -ForegroundColor Red
    exit 1
}

Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "Installer location: $installerPath" -ForegroundColor Yellow