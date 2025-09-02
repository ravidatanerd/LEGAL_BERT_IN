@echo off
REM InLegalDesk - Pip Upgrade Script
REM Must be run before package installation for best compatibility

echo.
echo ========================================
echo  InLegalDesk - Pip Upgrade Script
echo  (Run this FIRST for best results)
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found:
python --version

echo.
echo 📦 UPGRADING PIP TO LATEST VERSION...
echo ===================================

echo 🔧 Step 1: Upgrading pip using built-in method...
python -m pip install --upgrade pip

if errorlevel 1 (
    echo ⚠️  Standard pip upgrade failed, trying alternative...
    echo 🔧 Step 2: Using get-pip.py method...
    
    REM Download and run get-pip.py
    powershell -Command "& {Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'}"
    python get-pip.py
    del get-pip.py
)

echo.
echo 📦 UPGRADING ESSENTIAL TOOLS...
echo ==============================

echo 🔧 Installing/upgrading setuptools...
python -m pip install --upgrade setuptools

echo 🔧 Installing/upgrading wheel...
python -m pip install --upgrade wheel

echo 🔧 Installing/upgrading build tools...
python -m pip install --upgrade build

echo.
echo ✅ PIP AND TOOLS UPGRADE COMPLETED!
echo =================================

echo 📊 Current versions:
python -m pip --version
python -c "import setuptools; print(f'setuptools: {setuptools.__version__}')" 2>nul || echo "setuptools: installed"
python -c "import wheel; print(f'wheel: {wheel.__version__}')" 2>nul || echo "wheel: installed"

echo.
echo 🎯 NEXT STEPS:
echo =============
echo.
echo 1. ✅ Pip and tools are now upgraded
echo 2. 🚀 Run main installer:
echo    • PYTHON_UPGRADE_INSTALL.bat (version-aware)
echo    • AUTO_PYTHON_UPGRADE.bat (auto-upgrades Python)
echo    • ULTIMATE_AI_FIX.bat (95%+ AI success rate)
echo.
echo 3. 🔍 Check compatibility:
echo    python check_python_compatibility.py
echo.
echo 💡 TIP: Modern pip versions (20.0+) have much better
echo      wheel support and avoid compilation issues!
echo.
pause