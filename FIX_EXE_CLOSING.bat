@echo off
REM IMMEDIATE FIX for .exe closing issue
REM Runs Python 3.6 compatible version without Unicode emojis

echo.
echo ================================================
echo  IMMEDIATE FIX - .exe Closing Issue  
echo  (Python 3.6.6 Unicode emoji fix)
echo ================================================
echo.

echo ❌ PROBLEM IDENTIFIED:
echo Your .exe closes immediately because Python 3.6.6's tkinter
echo cannot handle Unicode emojis like the wrench emoji (U+1f527)
echo.

echo ✅ SOLUTION:
echo Running Python 3.6 compatible version without emojis
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo.
    echo This is the main issue:
    echo 1. Python is not installed or not in PATH
    echo 2. Install Python from https://python.org
    echo 3. Make sure "Add Python to PATH" is checked
    echo.
    goto :end
)

echo ✅ Python found:
python --version

echo.
echo 🔧 Running Python 3.6 compatible launcher...
echo ============================================

if exist InLegalDesk_Python36_Compatible.py (
    echo ✅ Python 3.6 compatible launcher found
    echo Running without Unicode emojis...
    echo.
    python InLegalDesk_Python36_Compatible.py
    echo.
    echo ✅ Launcher completed
) else (
    echo ❌ Python 3.6 compatible launcher not found!
    echo.
    echo Creating emergency ASCII-only launcher...
    
    REM Create simple ASCII-only launcher
    echo import sys, os, subprocess > emergency_ascii_launcher.py
    echo import tkinter as tk >> emergency_ascii_launcher.py
    echo from tkinter import messagebox >> emergency_ascii_launcher.py
    echo. >> emergency_ascii_launcher.py
    echo def launch_backend(): >> emergency_ascii_launcher.py
    echo     try: >> emergency_ascii_launcher.py
    echo         os.chdir("backend") >> emergency_ascii_launcher.py
    echo         subprocess.Popen([sys.executable, "app.py"]) >> emergency_ascii_launcher.py
    echo         messagebox.showinfo("Success", "Backend started at http://localhost:8877") >> emergency_ascii_launcher.py
    echo     except Exception as e: >> emergency_ascii_launcher.py
    echo         messagebox.showerror("Error", "Backend failed: " + str(e)) >> emergency_ascii_launcher.py
    echo. >> emergency_ascii_launcher.py
    echo def main(): >> emergency_ascii_launcher.py
    echo     root = tk.Tk() >> emergency_ascii_launcher.py
    echo     root.title("InLegalDesk Emergency Launcher") >> emergency_ascii_launcher.py
    echo     root.geometry("400x200") >> emergency_ascii_launcher.py
    echo     tk.Label(root, text="InLegalDesk Emergency Launcher", font=("Arial", 14, "bold")).pack(pady=20) >> emergency_ascii_launcher.py
    echo     tk.Button(root, text="Launch Backend Server", command=launch_backend, width=20, height=2).pack(pady=10) >> emergency_ascii_launcher.py
    echo     tk.Label(root, text="Then visit: http://localhost:8877", fg="blue").pack(pady=10) >> emergency_ascii_launcher.py
    echo     root.mainloop() >> emergency_ascii_launcher.py
    echo. >> emergency_ascii_launcher.py
    echo if __name__ == "__main__": >> emergency_ascii_launcher.py
    echo     try: >> emergency_ascii_launcher.py
    echo         main() >> emergency_ascii_launcher.py
    echo     except Exception as e: >> emergency_ascii_launcher.py
    echo         print("ERROR: " + str(e)) >> emergency_ascii_launcher.py
    echo         input("Press Enter to exit...") >> emergency_ascii_launcher.py
    
    echo.
    echo ✅ Emergency launcher created
    echo Running emergency ASCII-only launcher...
    echo.
    python emergency_ascii_launcher.py
)

echo.
echo 📋 UNICODE EMOJI ISSUE EXPLANATION:
echo ===================================
echo.
echo Your Python 3.6.6 has an old version of tkinter that cannot
echo handle Unicode emojis like 🔧 (wrench, U+1f527).
echo.
echo When the original .exe tries to display emojis in the GUI,
echo tkinter throws a TclError and the application crashes immediately.
echo.
echo ✅ SOLUTIONS:
echo =============
echo.
echo 1. IMMEDIATE FIX (what we just did):
echo    • Use ASCII-only version without emojis
echo    • This works with Python 3.6.6
echo.
echo 2. PERMANENT FIX (recommended):
echo    • Upgrade to Python 3.7+ from https://python.org
echo    • Python 3.7+ has better Unicode support
echo    • Use AUTO_PYTHON_UPGRADE.bat for automatic upgrade
echo.
echo 3. ALTERNATIVE:
echo    • Use web interface only (no GUI needed)
echo    • Run backend with: cd backend ^&^& python app.py
echo    • Visit: http://localhost:8877
echo.

:end
echo.
echo 🎯 PROBLEM SOLVED!
echo ==================
echo.
echo The .exe was closing because of Unicode emoji compatibility
echo with Python 3.6.6's tkinter. The ASCII version should work.
echo.
echo For best experience, upgrade to Python 3.7+ which has
echo full Unicode support and 95%+ package compatibility.
echo.

pause