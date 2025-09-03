@echo off
REM Diagnose why InLegalDesk .exe closes immediately

echo.
echo ================================================
echo  InLegalDesk - Diagnose .exe Closing Issue
echo  (Find out why the .exe closes in milliseconds)
echo ================================================
echo.

echo 🔍 DIAGNOSING .EXE ISSUE...
echo ===========================

echo.
echo 📊 System Information:
echo OS: %OS%
echo Processor: %PROCESSOR_ARCHITECTURE%
echo User: %USERNAME%
echo.

echo 🐍 Python Check:
python --version 2>nul
if errorlevel 1 (
    echo ❌ Python not found in PATH
    echo This is likely why the .exe fails!
    echo.
    echo 🔧 SOLUTION:
    echo 1. Install Python from https://python.org
    echo 2. Make sure "Add Python to PATH" is checked
    echo 3. Restart Command Prompt
    echo 4. Re-run the .exe
    echo.
    goto :end
) else (
    echo ✅ Python found:
    python --version
)

echo.
echo 📦 Pip Check:
python -m pip --version 2>nul
if errorlevel 1 (
    echo ❌ Pip not working
    echo This could cause the .exe to fail!
    echo.
    echo 🔧 SOLUTION:
    echo python -m ensurepip --upgrade
    echo python -m pip install --upgrade pip
    echo.
) else (
    echo ✅ Pip working:
    python -m pip --version
)

echo.
echo 🔍 Directory Check:
echo Current directory: %CD%
echo.
echo 📋 Looking for InLegalDesk files:
if exist backend (
    echo ✅ backend/ directory found
) else (
    echo ❌ backend/ directory missing
    echo This is likely why the .exe fails!
)

if exist desktop (
    echo ✅ desktop/ directory found  
) else (
    echo ❌ desktop/ directory missing
    echo This could cause GUI issues
)

if exist backend\app.py (
    echo ✅ backend\app.py found
) else (
    echo ❌ backend\app.py missing
    echo This is why the backend won't start!
)

if exist desktop\main.py (
    echo ✅ desktop\main.py found
) else (
    echo ❌ desktop\main.py missing
    echo This is why the desktop won't start!
)

echo.
echo 🔧 Testing Python Packages:
echo ===========================

echo Testing critical packages...

python -c "import sys; print(f'✅ sys module: {sys.version_info}')" 2>nul || echo "❌ sys module issue"

python -c "import os; print('✅ os module working')" 2>nul || echo "❌ os module issue"

python -c "import tkinter; print('✅ tkinter available')" 2>nul || echo "❌ tkinter missing - GUI won't work!"

python -c "import subprocess; print('✅ subprocess available')" 2>nul || echo "❌ subprocess missing"

python -c "import pathlib; print('✅ pathlib available')" 2>nul || echo "❌ pathlib missing"

echo.
echo 🧪 RUNNING DEBUG LAUNCHER...
echo ============================

echo Running debug version that shows detailed errors...
echo This will help identify why the .exe closes immediately.
echo.

if exist InLegalDesk_Debug_Launcher.py (
    echo ✅ Debug launcher found - running...
    python InLegalDesk_Debug_Launcher.py
) else if exist InLegalDesk_Console.py (
    echo ✅ Console launcher found - running...
    python InLegalDesk_Console.py
) else (
    echo ❌ No debug launcher found!
    echo.
    echo 🔧 MANUAL DIAGNOSIS:
    echo ===================
    echo.
    echo The .exe is likely failing because:
    echo 1. ❌ Python not in PATH
    echo 2. ❌ Missing required files (backend/, desktop/)
    echo 3. ❌ Missing Python packages (tkinter, etc.)
    echo 4. ❌ Incompatible Python version
    echo 5. ❌ .exe packaging issues
    echo.
    echo 💡 SOLUTIONS:
    echo 1. 🐍 Install/upgrade Python 3.7+ with "Add to PATH"
    echo 2. 📥 Re-download InLegalDesk and extract properly
    echo 3. 📦 Run: UPGRADE_PIP_FIRST.bat
    echo 4. 🚀 Run: ULTIMATE_AI_FIX.bat
    echo 5. 🔧 Use manual installers instead of .exe
    echo.
)

:end
echo.
echo 📋 DIAGNOSIS COMPLETED
echo =====================
echo.
echo If the issue persists:
echo 1. 📧 Report the error output above
echo 2. 🔧 Use manual installers as backup
echo 3. 🐍 Ensure Python 3.7+ is properly installed
echo 4. 📦 Verify all files are extracted correctly
echo.

pause