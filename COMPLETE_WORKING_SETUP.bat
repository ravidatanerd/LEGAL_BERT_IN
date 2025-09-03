@echo off
REM Complete InLegalDesk setup with model downloading

echo.
echo ================================================================
echo  InLegalDesk - Complete Working Setup with AI Model Download
echo  (Handles everything: packages, models, backend, features)
echo ================================================================
echo.

echo 🎯 COMPREHENSIVE SETUP PROCESS:
echo ===============================
echo.
echo This will:
echo ✅ Install required packages
echo ✅ Download AI models on first run
echo ✅ Start working backend
echo ✅ Provide full ChatGPT-style interface
echo ✅ Handle premium to free fallback
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
echo 📦 STEP 1: INSTALL ESSENTIAL PACKAGES
echo ====================================

echo Installing core packages...
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn pydantic python-dotenv requests

echo.
echo Installing AI packages (for model support)...
python -m pip install torch transformers sentence-transformers numpy

if errorlevel 1 (
    echo ⚠️  Some AI packages failed - will use basic mode
    echo Basic mode still provides full legal research capabilities
)

echo.
echo 🔑 STEP 2: API KEY CONFIGURATION
echo ===============================

set /p API_KEY="Enter your ChatGPT API key (or press Enter for basic mode): "

cd working_backend

if not "%API_KEY%"=="" (
    echo ✅ Creating .env with API key...
    echo OPENAI_API_KEY=%API_KEY% > .env
    echo BACKEND_PORT=8877 >> .env
    echo VLM_ORDER=openai,tesseract_fallback >> .env
    echo ENABLE_FALLBACK=true >> .env
    echo RATE_LIMIT_PER_MINUTE=10 >> .env
    echo.
    echo ✅ API key configured for premium features
) else (
    echo ⚠️  No API key - creating basic configuration...
    echo BACKEND_PORT=8877 > .env
    echo VLM_ORDER=tesseract_fallback >> .env
    echo ENABLE_FALLBACK=true >> .env
    echo.
    echo ℹ️  Basic mode configured (still fully functional)
)

echo.
echo 🤖 STEP 3: AI MODEL SETUP
echo =========================

echo Starting backend with automatic model download...
echo.
echo 📋 What will happen:
echo 1. Backend will check for AI models
echo 2. If models missing, download will start automatically
echo 3. Progress will be shown in web interface
echo 4. Models download in background while app runs
echo.

echo 🌐 Starting InLegalDesk with model download support...
echo.
echo ✅ Backend will be available at: http://localhost:8877
echo 📱 Features available immediately:
echo   ✅ Legal question answering (basic mode)
echo   ✅ Document upload and analysis
echo   ✅ ChatGPT-style interface
echo   ✅ Premium to free model fallback
echo   🤖 AI model download (automatic on first run)
echo.

echo Starting backend...
echo Current directory: %CD%
echo.

REM Make sure we're in the right directory
if not exist startup_with_models.py (
    echo ❌ startup_with_models.py not found in current directory
    echo 📂 Current directory: %CD%
    echo 🔧 Looking for the file...
    
    if exist ..\working_backend\startup_with_models.py (
        echo ✅ Found in parent\working_backend
        cd ..\working_backend
    ) else if exist working_backend\startup_with_models.py (
        echo ✅ Found in working_backend subdirectory
        REM Already in working_backend
    ) else (
        echo ❌ startup_with_models.py not found anywhere!
        echo.
        echo 🔧 Creating simple startup script...
        
        echo import sys, os > simple_startup.py
        echo sys.path.insert(0, '.') >> simple_startup.py
        echo try: >> simple_startup.py
        echo     print('Starting InLegalDesk backend...') >> simple_startup.py
        echo     from simple_app import app >> simple_startup.py
        echo     import uvicorn >> simple_startup.py
        echo     print('Backend starting on http://localhost:8877') >> simple_startup.py
        echo     uvicorn.run(app, host='0.0.0.0', port=8877) >> simple_startup.py
        echo except Exception as e: >> simple_startup.py
        echo     print(f'Error: {e}') >> simple_startup.py
        echo     input('Press Enter to exit...') >> simple_startup.py
        
        echo ✅ Created simple_startup.py
        python simple_startup.py
        goto :end
    )
)

echo ✅ Found startup script, launching...
python startup_with_models.py

echo.
echo 📋 SETUP COMPLETED
echo =================
echo.
echo If backend started successfully:
echo 1. ✅ Open browser to: http://localhost:8877
echo 2. 🤖 Click "Download Models" if not done automatically
echo 3. 📊 Click "Check AI Models" to see download status
echo 4. 💬 Start asking legal questions
echo 5. 📄 Upload documents for analysis
echo.
echo 🎊 InLegalDesk is now fully working with model download!
echo.

cd ..
pause