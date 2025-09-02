@echo off
REM Enhanced InLegalDesk Installer Builder with AI Models
REM This version includes AI models in the installer for offline use

echo.
echo ========================================
echo  InLegalDesk Enhanced Installer Builder
echo  (Includes AI Models for Offline Use)
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Check Inno Setup
if not exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo ERROR: Inno Setup not found. Please install from https://jrsoftware.org/isinfo.php
    pause
    exit /b 1
)

echo ✅ Inno Setup found

echo.
echo 🤖 ENHANCED INSTALLER OPTIONS:
echo 1. Standard Installer (models download on first run)
echo 2. Full Installer (includes AI models - larger but offline)
echo.

set /p choice="Choose option (1 or 2): "

if "%choice%"=="2" (
    echo.
    echo 📦 Creating FULL installer with AI models...
    echo This will download ~2GB of AI models and include them in the installer
    echo The installer will be larger (~2.5GB) but will work completely offline
    echo.
    set /p confirm="Continue with full installer? (y/n): "
    
    if not "%confirm%"=="y" (
        echo Cancelled by user
        pause
        exit /b 0
    )
    
    echo.
    echo 🔄 Downloading AI models for bundling...
    cd backend
    python model_manager.py
    if errorlevel 1 (
        echo ❌ Model download failed
        pause
        exit /b 1
    )
    cd ..
    echo ✅ AI models ready for bundling
)

echo.
echo 🏗️ Building InLegalDesk installer...
echo This will take 10-20 minutes depending on your system and internet connection
echo.

REM Navigate to installer directory
cd /d "%~dp0\installer"

REM Run PowerShell build script
if "%choice%"=="2" (
    powershell -ExecutionPolicy Bypass -File "build_installer.ps1" -BuildType onedir -IncludeModels
) else (
    powershell -ExecutionPolicy Bypass -File "build_installer.ps1" -BuildType onedir
)

if errorlevel 1 (
    echo.
    echo ❌ Build failed. Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo 🎉 Build completed successfully!
echo.

if "%choice%"=="2" (
    echo 📦 FULL INSTALLER CREATED:
    echo • File: installer\output\InLegalDesk_Installer.exe (~2.5GB)
    echo • Includes: All AI models for offline use
    echo • Features: Complete platform, no internet required for AI
) else (
    echo 📦 STANDARD INSTALLER CREATED:
    echo • File: installer\output\InLegalDesk_Installer.exe (~300MB)
    echo • Features: Downloads AI models on first run
    echo • Requires: Internet connection for initial model download
)

echo.
echo 🚀 Next steps:
echo 1. Test the installer on a clean Windows system
echo 2. Upload to GitHub releases or distribute as needed
echo 3. Share with users for installation
echo.

pause