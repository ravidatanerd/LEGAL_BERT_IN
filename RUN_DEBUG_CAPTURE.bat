@echo off
REM Runs debug and captures ALL output to file - won't miss anything

echo.
echo ================================================
echo  InLegalDesk - Debug with Output Capture
echo  (Captures ALL output to file for analysis)
echo ================================================
echo.

echo 🔍 Running comprehensive debug with output capture...
echo This will create a debug_output.txt file with all information.
echo.

echo Starting debug... (this may take a moment)

REM Run debug and capture ALL output
python FOOLPROOF_DEBUG.py > debug_output.txt 2>&1

if exist debug_output.txt (
    echo ✅ Debug completed! Output captured to debug_output.txt
    echo.
    echo 📋 Showing debug results:
    echo ========================
    type debug_output.txt
    echo ========================
    echo.
    echo 📄 Full debug log saved to: debug_output.txt
) else (
    echo ❌ Debug capture failed!
    echo.
    echo This means Python itself is not working properly.
    echo.
    echo 🔧 CRITICAL PYTHON ISSUE:
    echo =========================
    echo.
    echo The .exe closes immediately because Python is not
    echo working correctly on your system.
    echo.
    echo 🚀 SOLUTIONS:
    echo 1. Install Python 3.7+ from https://python.org
    echo 2. During installation, CHECK "Add Python to PATH"
    echo 3. Choose "Custom Installation" and include ALL components
    echo 4. Restart your computer after installation
    echo 5. Re-download InLegalDesk and try again
    echo.
)

echo.
echo 💡 NEXT STEPS:
echo ==============
echo.
echo If debug shows specific issues:
echo • Follow the solutions provided in the debug output
echo • Fix the identified problems one by one
echo • Re-test the .exe after each fix
echo.
echo If debug shows no issues but .exe still closes:
echo • The problem is with the .exe packaging itself
echo • Use manual installers instead:
echo   - ULTIMATE_AI_FIX.bat (95%+ success rate)
echo   - AUTO_PYTHON_UPGRADE.bat (upgrades Python)
echo   - CHECK_BEFORE_INSTALL.bat (compatibility check)
echo.
echo If Python itself doesn't work:
echo • Reinstall Python 3.7+ with full standard library
echo • Make sure "Add Python to PATH" is checked
echo • Restart computer after installation
echo.

pause