@echo off
REM InLegalDesk One-Click Installer
REM Handles all compatibility issues automatically

echo.
echo ==========================================
echo  InLegalDesk One-Click Installer
echo  (Handles all compatibility issues)
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo.
    echo 🔧 SOLUTION:
    echo 1. Download Python 3.8+ from: https://python.org/downloads/
    echo 2. During installation, check "Add Python to PATH"
    echo 3. Restart Command Prompt and try again
    echo.
    pause
    exit /b 1
)

echo ✅ Python found:
python --version

echo.
echo 🚀 Starting automatic installation...
echo This will install InLegalDesk with maximum compatibility
echo.

REM Run the fixed installation script
python install_fixed.py

if errorlevel 1 (
    echo.
    echo ❌ Installation failed. Trying alternative method...
    echo.
    echo 🔧 MANUAL STEPS:
    echo.
    echo Backend Setup:
    echo cd backend
    echo python -m venv venv
    echo venv\Scripts\activate
    echo pip install fastapi uvicorn pydantic python-dotenv
    echo pip install transformers==4.18.0 torch
    echo pip install numpy pillow requests httpx
    echo copy .env.sample .env
    echo python app.py
    echo.
    echo Desktop Setup (new Command Prompt):
    echo cd desktop
    echo python -m venv venv
    echo venv\Scripts\activate
    echo pip install PySide6 httpx python-dotenv markdown
    echo python main.py
    echo.
    pause
    exit /b 1
)

echo.
echo 🎉 Installation completed successfully!
echo.
echo 🚀 To start InLegalDesk:
echo 1. Open Command Prompt in backend folder
echo 2. Run: venv\Scripts\activate
echo 3. Run: python app.py
echo 4. Open another Command Prompt in desktop folder  
echo 5. Run: venv\Scripts\activate
echo 6. Run: python main.py
echo.
echo 🔑 Don't forget to configure your OpenAI API key!
echo.
pause