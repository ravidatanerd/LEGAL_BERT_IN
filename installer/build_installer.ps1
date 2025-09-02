# PowerShell script to build InLegalDesk Windows installer
# This script creates a virtual environment, builds the executable, and creates the installer

param(
    [string]$PythonPath = "python",
    [string]$BuildType = "onedir",  # "onefile" or "onedir"
    [switch]$SkipBuild,
    [switch]$SkipInstaller,
    [switch]$Clean
)

# Configuration
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$DesktopDir = Join-Path $ProjectRoot "desktop"
$InstallerDir = Join-Path $ProjectRoot "installer"
$DistDir = Join-Path $ProjectRoot "dist"
$BuildDir = Join-Path $ProjectRoot "build"
$VenvDir = Join-Path $ProjectRoot "venv"

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Test-InnoSetup {
    # Check if Inno Setup is installed
    $innoPaths = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 5\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 5\ISCC.exe"
    )
    
    foreach ($path in $innoPaths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    return $null
}

function New-VirtualEnvironment {
    Write-ColorOutput "Creating virtual environment..." $Blue
    
    if (Test-Path $VenvDir) {
        Write-ColorOutput "Virtual environment already exists. Removing..." $Yellow
        Remove-Item $VenvDir -Recurse -Force
    }
    
    # Create virtual environment
    & $PythonPath -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create virtual environment"
    }
    
    # Activate virtual environment
    $ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
    if (Test-Path $ActivateScript) {
        & $ActivateScript
    } else {
        throw "Virtual environment activation script not found"
    }
    
    Write-ColorOutput "Virtual environment created successfully" $Green
}

function Install-Dependencies {
    Write-ColorOutput "Installing dependencies..." $Blue
    
    # Upgrade pip
    & python -m pip install --upgrade pip
    
    # Install PyInstaller
    & python -m pip install pyinstaller
    
    # Install desktop dependencies
    $DesktopRequirements = Join-Path $DesktopDir "requirements.txt"
    if (Test-Path $DesktopRequirements) {
        & python -m pip install -r $DesktopRequirements
    }
    
    # Install backend dependencies
    $BackendRequirements = Join-Path $ProjectRoot "requirements.txt"
    if (Test-Path $BackendRequirements) {
        & python -m pip install -r $BackendRequirements
    }
    
    Write-ColorOutput "Dependencies installed successfully" $Green
}

function Build-Executable {
    param([string]$BuildType)
    
    Write-ColorOutput "Building executable ($BuildType)..." $Blue
    
    # Clean previous builds
    if (Test-Path $DistDir) {
        Remove-Item $DistDir -Recurse -Force
    }
    if (Test-Path $BuildDir) {
        Remove-Item $BuildDir -Recurse -Force
    }
    
    # Prepare PyInstaller command
    $MainScript = Join-Path $DesktopDir "main.py"
    $OutputName = "InLegalDesk"
    
    $PyInstallerArgs = @(
        "--noconfirm"
        "--name" $OutputName
        "--distpath" $DistDir
        "--workpath" $BuildDir
    )
    
    if ($BuildType -eq "onefile") {
        $PyInstallerArgs += "--onefile"
    } else {
        $PyInstallerArgs += "--onedir"
    }
    
    # Add data files
    $ServerDir = Join-Path $DesktopDir "server"
    if (Test-Path $ServerDir) {
        $PyInstallerArgs += "--add-data"
        $PyInstallerArgs += "`"$ServerDir;server`""
    }
    
    $EnvSample = Join-Path $DesktopDir ".env.sample"
    if (Test-Path $EnvSample) {
        $PyInstallerArgs += "--add-data"
        $PyInstallerArgs += "`"$EnvSample;.env.sample`""
    }
    
    # Add icon if available
    $IconFile = Join-Path $InstallerDir "icon.ico"
    if (Test-Path $IconFile) {
        $PyInstallerArgs += "--icon"
        $PyInstallerArgs += $IconFile
    }
    
    # Add hidden imports for PySide6
    $HiddenImports = @(
        "PySide6.QtCore",
        "PySide6.QtGui", 
        "PySide6.QtWidgets",
        "markdown",
        "requests",
        "aiohttp",
        "asyncio"
    )
    
    foreach ($Import in $HiddenImports) {
        $PyInstallerArgs += "--hidden-import"
        $PyInstallerArgs += $Import
    }
    
    # Add the main script
    $PyInstallerArgs += $MainScript
    
    # Run PyInstaller
    Write-ColorOutput "Running PyInstaller with args: $($PyInstallerArgs -join ' ')" $Yellow
    & python -m PyInstaller @PyInstallerArgs
    
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed"
    }
    
    Write-ColorOutput "Executable built successfully" $Green
}

function Build-Installer {
    Write-ColorOutput "Building Windows installer..." $Blue
    
    # Check if Inno Setup is available
    $InnoSetupPath = Test-InnoSetup
    if (-not $InnoSetupPath) {
        throw "Inno Setup not found. Please install Inno Setup from https://jrsoftware.org/isinfo.php"
    }
    
    # Prepare installer script
    $InstallerScript = Join-Path $InstallerDir "InLegalDesk.iss"
    if (-not (Test-Path $InstallerScript)) {
        throw "Installer script not found: $InstallerScript"
    }
    
    # Create output directory
    $OutputDir = Join-Path $InstallerDir "output"
    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force
    }
    
    # Run Inno Setup
    Write-ColorOutput "Running Inno Setup..." $Yellow
    & $InnoSetupPath $InstallerScript
    
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup compilation failed"
    }
    
    # Check if installer was created
    $InstallerFile = Join-Path $OutputDir "InLegalDesk_Installer.exe"
    if (Test-Path $InstallerFile) {
        $FileSize = (Get-Item $InstallerFile).Length / 1MB
        Write-ColorOutput "Installer created successfully: $InstallerFile ($([math]::Round($FileSize, 2)) MB)" $Green
    } else {
        throw "Installer file not found after compilation"
    }
}

function Show-Summary {
    Write-ColorOutput "`n=== Build Summary ===" $Blue
    Write-ColorOutput "Project Root: $ProjectRoot" $White
    Write-ColorOutput "Build Type: $BuildType" $White
    Write-ColorOutput "Python Path: $PythonPath" $White
    
    if (-not $SkipBuild) {
        $ExePath = if ($BuildType -eq "onefile") {
            Join-Path $DistDir "InLegalDesk.exe"
        } else {
            Join-Path $DistDir "InLegalDesk\InLegalDesk.exe"
        }
        
        if (Test-Path $ExePath) {
            Write-ColorOutput "Executable: $ExePath" $Green
        } else {
            Write-ColorOutput "Executable: Not found" $Red
        }
    }
    
    if (-not $SkipInstaller) {
        $InstallerPath = Join-Path $InstallerDir "output\InLegalDesk_Installer.exe"
        if (Test-Path $InstallerPath) {
            Write-ColorOutput "Installer: $InstallerPath" $Green
        } else {
            Write-ColorOutput "Installer: Not found" $Red
        }
    }
    
    Write-ColorOutput "`nBuild completed!" $Green
}

# Main execution
try {
    Write-ColorOutput "=== InLegalDesk Windows Installer Builder ===" $Blue
    Write-ColorOutput "Project Root: $ProjectRoot" $White
    
    # Check prerequisites
    if (-not (Test-Command $PythonPath)) {
        throw "Python not found at: $PythonPath"
    }
    
    # Clean if requested
    if ($Clean) {
        Write-ColorOutput "Cleaning previous builds..." $Yellow
        if (Test-Path $DistDir) { Remove-Item $DistDir -Recurse -Force }
        if (Test-Path $BuildDir) { Remove-Item $BuildDir -Recurse -Force }
        if (Test-Path $VenvDir) { Remove-Item $VenvDir -Recurse -Force }
    }
    
    # Build executable
    if (-not $SkipBuild) {
        New-VirtualEnvironment
        Install-Dependencies
        Build-Executable -BuildType $BuildType
    }
    
    # Build installer
    if (-not $SkipInstaller) {
        Build-Installer
    }
    
    Show-Summary
    
} catch {
    Write-ColorOutput "`nError: $($_.Exception.Message)" $Red
    Write-ColorOutput "Build failed!" $Red
    exit 1
}