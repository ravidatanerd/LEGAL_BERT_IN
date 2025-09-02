# PowerShell script to build InLegal Desktop installer
# This script creates a virtual environment, installs dependencies, builds the executable, and creates the installer

param(
    [string]$PythonPath = "python",
    [string]$OutputDir = "output",
    [switch]$Clean = $false,
    [switch]$SkipBuild = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "InLegal Desktop Build Script" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Yellow
Write-Host "Script Dir: $ScriptDir" -ForegroundColor Yellow

# Check if Python is available
try {
    $PythonVersion = & $PythonPath --version 2>&1
    Write-Host "Python Version: $PythonVersion" -ForegroundColor Green
} catch {
    Write-Error "Python not found. Please install Python 3.9+ and ensure it's in PATH, or specify the path with -PythonPath parameter."
    exit 1
}

# Check if Inno Setup is available
$InnoSetupPath = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $InnoSetupPath)) {
    $InnoSetupPath = "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
}

if (-not (Test-Path $InnoSetupPath)) {
    Write-Error "Inno Setup not found. Please install Inno Setup 6 from https://jrsoftware.org/isinfo.php"
    exit 1
}

Write-Host "Inno Setup found: $InnoSetupPath" -ForegroundColor Green

# Clean previous builds if requested
if ($Clean) {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    
    $CleanPaths = @(
        "$ProjectRoot\desktop\dist",
        "$ProjectRoot\desktop\build",
        "$ProjectRoot\desktop\__pycache__",
        "$ScriptDir\output"
    )
    
    foreach ($Path in $CleanPaths) {
        if (Test-Path $Path) {
            Remove-Item -Recurse -Force $Path
            Write-Host "Cleaned: $Path" -ForegroundColor Yellow
        }
    }
}

# Create virtual environment
$VenvPath = "$ProjectRoot\venv"
if (-not (Test-Path $VenvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    & $PythonPath -m venv $VenvPath
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
$ActivateScript = "$VenvPath\Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    & $ActivateScript
} else {
    Write-Error "Failed to activate virtual environment"
    exit 1
}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
& python -m pip install --upgrade pip

# Install PyInstaller
Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
& python -m pip install pyinstaller

# Install desktop dependencies
Write-Host "Installing desktop dependencies..." -ForegroundColor Yellow
$DesktopRequirements = "$ProjectRoot\desktop\requirements.txt"
if (Test-Path $DesktopRequirements) {
    & python -m pip install -r $DesktopRequirements
} else {
    Write-Error "Desktop requirements file not found: $DesktopRequirements"
    exit 1
}

# Install backend dependencies
Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
$BackendRequirements = "$ProjectRoot\backend\requirements.txt"
if (Test-Path $BackendRequirements) {
    & python -m pip install -r $BackendRequirements
} else {
    Write-Error "Backend requirements file not found: $BackendRequirements"
    exit 1
}

# Copy server files to desktop directory
Write-Host "Copying server files..." -ForegroundColor Yellow
$ServerDir = "$ProjectRoot\desktop\server"
$BackendDir = "$ProjectRoot\backend"

# Remove existing server directory
if (Test-Path $ServerDir) {
    Remove-Item -Recurse -Force $ServerDir
}

# Create server directory
New-Item -ItemType Directory -Path $ServerDir -Force

# Copy backend files
$BackendFiles = @(
    "app.py",
    "ingest.py", 
    "retriever.py",
    "llm.py",
    "chunking.py",
    "requirements.txt",
    ".env.sample"
)

foreach ($File in $BackendFiles) {
    $SourcePath = "$BackendDir\$File"
    $DestPath = "$ServerDir\$File"
    if (Test-Path $SourcePath) {
        Copy-Item $SourcePath $DestPath
        Write-Host "Copied: $File" -ForegroundColor Yellow
    }
}

# Copy backend directories
$BackendDirs = @("utils", "extractors", "sources")
foreach ($Dir in $BackendDirs) {
    $SourcePath = "$BackendDir\$Dir"
    $DestPath = "$ServerDir\$Dir"
    if (Test-Path $SourcePath) {
        Copy-Item -Recurse $SourcePath $DestPath
        Write-Host "Copied directory: $Dir" -ForegroundColor Yellow
    }
}

# Build executable with PyInstaller
if (-not $SkipBuild) {
    Write-Host "Building executable with PyInstaller..." -ForegroundColor Yellow
    
    $DesktopMain = "$ProjectRoot\desktop\main.py"
    $DistDir = "$ProjectRoot\desktop\dist"
    
    # PyInstaller command
    $PyInstallerArgs = @(
        "--noconfirm",
        "--onedir",
        "--name", "InLegalDesk",
        "--add-data", "server;server",
        "--add-data", ".env.sample;.env.sample",
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtWidgets", 
        "--hidden-import", "PySide6.QtGui",
        "--hidden-import", "aiohttp",
        "--hidden-import", "markdown",
        "--hidden-import", "Pygments",
        "--hidden-import", "transformers",
        "--hidden-import", "torch",
        "--hidden-import", "faiss",
        "--hidden-import", "rank_bm25",
        "--hidden-import", "pymupdf",
        "--hidden-import", "openai",
        "--hidden-import", "pytesseract",
        "--hidden-import", "playwright",
        "--collect-all", "transformers",
        "--collect-all", "torch",
        "--collect-all", "faiss",
        "--collect-all", "rank_bm25",
        "--collect-all", "pymupdf",
        "--collect-all", "openai",
        "--collect-all", "pytesseract",
        "--collect-all", "playwright",
        $DesktopMain
    )
    
    # Change to desktop directory
    Push-Location "$ProjectRoot\desktop"
    
    try {
        & pyinstaller @PyInstallerArgs
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "PyInstaller failed with exit code $LASTEXITCODE"
            exit 1
        }
        
        Write-Host "PyInstaller build completed successfully" -ForegroundColor Green
    } finally {
        Pop-Location
    }
}

# Create installer with Inno Setup
Write-Host "Creating installer with Inno Setup..." -ForegroundColor Yellow

$InnoScript = "$ScriptDir\InLegalDesk.iss"
$OutputDir = "$ScriptDir\output"

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force
}

# Run Inno Setup
$InnoArgs = @(
    "/O$OutputDir",
    $InnoScript
)

try {
    & $InnoSetupPath @InnoArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Inno Setup failed with exit code $LASTEXITCODE"
        exit 1
    }
    
    Write-Host "Installer created successfully!" -ForegroundColor Green
    
    # List output files
    $OutputFiles = Get-ChildItem $OutputDir -Filter "*.exe"
    foreach ($File in $OutputFiles) {
        $FileSize = [math]::Round($File.Length / 1MB, 2)
        Write-Host "Installer: $($File.Name) ($FileSize MB)" -ForegroundColor Green
    }
    
} catch {
    Write-Error "Failed to create installer: $_"
    exit 1
}

Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "Installer location: $OutputDir" -ForegroundColor Yellow