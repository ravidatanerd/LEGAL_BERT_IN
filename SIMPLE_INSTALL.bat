@echo off
REM InLegalDesk Ultra-Simple Installation
REM Uses only the most widely available package versions

echo.
echo ==========================================
echo  InLegalDesk Ultra-Simple Installation
echo  (Maximum Compatibility Mode)
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found:
python --version
echo.

echo 🔧 Installing with maximum compatibility...
echo This uses only widely available package versions
echo.

REM Backend setup with minimal packages
echo 📋 Setting up Backend (Core functionality)...
cd backend

REM Clean any existing venv
if exist venv rmdir /s /q venv

REM Create fresh venv
python -m venv venv
if errorlevel 1 (
    echo ❌ Virtual environment creation failed
    pause
    exit /b 1
)

REM Activate and install minimal packages
call venv\Scripts\activate.bat

REM Install packages one by one with maximum compatibility
echo 📦 Installing core packages...
pip install --upgrade pip
pip install "fastapi>=0.60.0,<0.80.0"
pip install "uvicorn>=0.12.0,<0.18.0"
pip install "pydantic>=1.7.0,<2.0.0"
pip install "python-dotenv>=0.10.0"
pip install "requests>=2.20.0"
pip install "httpx>=0.18.0"

echo 🤖 Installing AI packages...
pip install "numpy>=1.18.0,<1.22.0"
pip install "torch>=1.6.0,<1.12.0"
pip install "transformers>=4.5.0,<=4.18.0"

echo 📄 Installing document processing...
pip install "PyMuPDF>=1.16.0,<=1.19.6"
pip install "Pillow>=7.0.0,<9.0.0"

echo 📝 Installing text processing...
pip install "markdown>=3.0.0,<3.4.0"

echo 🔒 Installing security...
pip install "cryptography>=2.8.0,<4.0.0"

echo ⚡ Installing optional packages...
pip install "sentence-transformers>=2.0.0,<2.3.0" 2>nul || echo "⚠️  sentence-transformers skipped"
pip install "rank-bm25>=0.2.0" 2>nul || echo "⚠️  rank-bm25 skipped"
pip install "aiofiles>=0.6.0" 2>nul || echo "⚠️  aiofiles skipped"

REM Copy environment file
if not exist .env copy .env.sample .env

echo ✅ Backend setup complete
cd ..

REM Desktop setup
echo.
echo 📋 Setting up Desktop...
cd desktop

REM Clean any existing venv
if exist venv rmdir /s /q venv

REM Create fresh venv
python -m venv venv
call venv\Scripts\activate.bat

echo 📦 Installing desktop packages...
pip install --upgrade pip
pip install "PySide6>=6.0.0,<6.4.0"
pip install "httpx>=0.18.0"
pip install "python-dotenv>=0.10.0"
pip install "markdown>=3.0.0"
pip install "requests>=2.20.0"

REM Copy backend files
echo 📋 Copying backend files...
if exist server rmdir /s /q server
xcopy /E /I ..\backend server
if exist server\venv rmdir /s /q server\venv

echo ✅ Desktop setup complete
cd ..

echo.
echo 🎉 INSTALLATION COMPLETED!
echo ==========================================
echo.
echo ✅ Backend: Ready to run
echo ✅ Desktop: Ready to launch
echo.
echo 🚀 To start InLegalDesk:
echo.
echo 1. Start Backend:
echo    cd backend
echo    venv\Scripts\activate
echo    python app.py
echo.
echo 2. Start Desktop (new Command Prompt):
echo    cd desktop
echo    venv\Scripts\activate
echo    python main.py
echo.
echo 🔑 Configure OpenAI API key in desktop app for full AI features!
echo 📖 See README.md for detailed usage instructions
echo.
echo 🎊 Enjoy your AI-powered legal research platform!
echo.
pause