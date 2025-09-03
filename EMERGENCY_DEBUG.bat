@echo off
REM Emergency debug script - captures ALL errors and doesn't close

echo.
echo ================================================
echo  EMERGENCY DEBUG - .exe Closing Issue
echo  (Captures ALL errors and stays open)
echo ================================================
echo.

echo 🔍 STEP 1: BASIC SYSTEM CHECK
echo ==============================

echo Current directory: %CD%
echo Current user: %USERNAME%
echo Windows version: %OS%
echo.

echo 🐍 STEP 2: PYTHON CHECK
echo ========================

echo Testing if Python is accessible...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ CRITICAL: Python not found in PATH!
    echo.
    echo This is almost certainly why your .exe closes immediately!
    echo.
    echo 🔧 SOLUTIONS:
    echo 1. Install Python from https://python.org
    echo 2. During installation, CHECK "Add Python to PATH"
    echo 3. Or manually add Python to PATH
    echo 4. Restart Command Prompt after installation
    echo.
    echo 📋 To manually add Python to PATH:
    echo 1. Find your Python installation (usually C:\Python39 or C:\Users\%USERNAME%\AppData\Local\Programs\Python)
    echo 2. Add that directory to your PATH environment variable
    echo 3. Also add the Scripts subdirectory
    echo.
    goto :end_with_pause
)

echo ✅ Python found:
python --version

echo.
echo 🔧 STEP 3: DETAILED PYTHON INFO
echo ===============================

echo Python executable location:
where python

echo Python version details:
python -c "import sys; print(f'Version: {sys.version}'); print(f'Executable: {sys.executable}'); print(f'Platform: {sys.platform}')"

echo.
echo 📦 STEP 4: PIP CHECK
echo ====================

echo Testing pip...
python -m pip --version 2>nul
if errorlevel 1 (
    echo ❌ Pip not working!
    echo This could cause the .exe to fail.
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
echo 📂 STEP 5: FILE STRUCTURE CHECK
echo ===============================

echo Checking for InLegalDesk files...
echo.

if exist backend (
    echo ✅ backend/ directory found
    if exist backend\app.py (
        echo ✅ backend\app.py found
    ) else (
        echo ❌ backend\app.py MISSING - this will cause failures!
    )
) else (
    echo ❌ backend/ directory MISSING - this will cause failures!
)

if exist desktop (
    echo ✅ desktop/ directory found
    if exist desktop\main.py (
        echo ✅ desktop\main.py found
    ) else (
        echo ❌ desktop\main.py MISSING - desktop won't work!
    )
) else (
    echo ❌ desktop/ directory MISSING - desktop won't work!
)

echo.
echo 🧪 STEP 6: PYTHON PACKAGE TEST
echo ==============================

echo Testing critical Python packages...
echo.

python -c "import sys; print('✅ sys module working')" 2>nul || echo "❌ sys module issue"

python -c "import os; print('✅ os module working')" 2>nul || echo "❌ os module issue"

python -c "import tkinter; print('✅ tkinter available - GUI should work')" 2>nul || echo "❌ tkinter MISSING - this is why GUI .exe fails!"

python -c "import subprocess; print('✅ subprocess available')" 2>nul || echo "❌ subprocess missing"

python -c "import pathlib; print('✅ pathlib available')" 2>nul || echo "❌ pathlib missing"

python -c "import threading; print('✅ threading available')" 2>nul || echo "❌ threading missing"

echo.
echo 🔧 STEP 7: TESTING ACTUAL LAUNCHER
echo ==================================

echo Testing if our Python launcher works...
echo.

if exist InLegalDesk_Console.py (
    echo ✅ Console launcher found - testing...
    echo.
    echo Running console version that shows errors:
    echo ==========================================
    python InLegalDesk_Console.py
    echo ==========================================
    echo Console launcher finished.
) else (
    echo ❌ Console launcher not found
    echo.
    echo 🔧 CREATING EMERGENCY LAUNCHER:
    echo ===============================
    
    echo Creating emergency Python launcher...
    
    echo import sys, os, traceback > emergency_launcher.py
    echo try: >> emergency_launcher.py
    echo     print("🚀 Emergency InLegalDesk Launcher") >> emergency_launcher.py
    echo     print("=" * 40) >> emergency_launcher.py
    echo     print(f"Python: {sys.version}") >> emergency_launcher.py
    echo     print(f"Directory: {os.getcwd()}") >> emergency_launcher.py
    echo     print("") >> emergency_launcher.py
    echo     print("Testing basic functionality...") >> emergency_launcher.py
    echo     import tkinter >> emergency_launcher.py
    echo     print("✅ tkinter works") >> emergency_launcher.py
    echo     print("") >> emergency_launcher.py
    echo     print("InLegalDesk should work. If .exe still fails,") >> emergency_launcher.py
    echo     print("it's a packaging issue with the .exe itself.") >> emergency_launcher.py
    echo     print("") >> emergency_launcher.py
    echo     input("Press Enter to exit...") >> emergency_launcher.py
    echo except Exception as e: >> emergency_launcher.py
    echo     print(f"❌ Error: {e}") >> emergency_launcher.py
    echo     print(f"Traceback: {traceback.format_exc()}") >> emergency_launcher.py
    echo     print("This error explains why the .exe closes!") >> emergency_launcher.py
    echo     input("Press Enter to exit...") >> emergency_launcher.py
    
    echo.
    echo Running emergency launcher:
    echo ==========================
    python emergency_launcher.py
    echo ==========================
    echo Emergency launcher finished.
)

echo.
echo 📊 STEP 8: DIAGNOSIS SUMMARY
echo ============================

echo.
echo Based on the tests above, the .exe is likely failing because:
echo.

if not exist backend (
    echo ❌ CRITICAL: backend/ directory missing
    echo    Solution: Re-download and extract InLegalDesk properly
)

if not exist desktop (
    echo ❌ CRITICAL: desktop/ directory missing  
    echo    Solution: Re-download and extract InLegalDesk properly
)

python -c "import tkinter" 2>nul || (
    echo ❌ CRITICAL: tkinter missing
    echo    Solution: Reinstall Python with full standard library
)

echo.
echo 🔧 IMMEDIATE FIXES:
echo ==================

echo 1. If Python not found:
echo    • Install Python 3.7+ from https://python.org
echo    • CHECK "Add Python to PATH" during installation
echo    • Restart Command Prompt

echo.
echo 2. If directories missing:
echo    • Re-download InLegalDesk ZIP
echo    • Extract ALL files properly
echo    • Make sure backend/ and desktop/ folders exist

echo.
echo 3. If tkinter missing:
echo    • Reinstall Python with "Include tcl/tk and IDLE" checked
echo    • Or install tkinter separately

echo.
echo 4. If all above OK but .exe still fails:
echo    • Use manual installers: ULTIMATE_AI_FIX.bat
echo    • Or run Python scripts directly: python InLegalDesk_Console.py

:end_with_pause
echo.
echo 📋 DIAGNOSIS COMPLETE
echo ====================
echo.
echo The information above shows exactly why your .exe closes.
echo Follow the specific solutions for your issue.
echo.
echo 💡 TIP: The manual .bat installers work even when .exe fails!
echo.

pause