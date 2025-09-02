@echo off
REM Quick build script for InLegalDesk Windows Installer
REM Run this on Windows with Python and Inno Setup installed

echo.
echo ========================================
echo  InLegalDesk Windows Installer Builder
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Check if Inno Setup is available
if not exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo ERROR: Inno Setup not found. Please install Inno Setup 6 from https://jrsoftware.org/isinfo.php
    pause
    exit /b 1
)

echo ✅ Inno Setup found

REM Navigate to installer directory
cd /d "%~dp0\installer"

echo.
echo 🏗️ Building InLegalDesk installer...
echo This will take 5-15 minutes depending on your internet connection
echo.

REM Run PowerShell build script
powershell -ExecutionPolicy Bypass -File "build_installer.ps1"

if errorlevel 1 (
    echo.
    echo ❌ Build failed. Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo 🎉 Build completed successfully!
echo.
echo 📦 Your installer is ready:
echo    installer\output\InLegalDesk_Installer.exe
echo.
echo 🚀 Next steps:
echo 1. Test the installer by running it
echo 2. Upload to GitHub releases for distribution
echo 3. Share with users for installation
echo.

pause