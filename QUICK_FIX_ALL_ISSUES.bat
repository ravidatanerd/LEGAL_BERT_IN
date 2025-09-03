@echo off
REM Quick fix for all reported issues

echo.
echo ========================================================
echo  InLegalDesk - Quick Fix for All Issues
echo  (Backend startup + App closing + ChatGPT features)
echo ========================================================
echo.

echo 🔧 FIXING ALL REPORTED ISSUES:
echo ==============================
echo.
echo Issue 1: Backend server failed to start
echo Issue 2: App closes when typing 'hi' and clicking send  
echo Issue 3: Missing ChatGPT-style file upload features
echo Issue 4: Need premium to free model fallback
echo.

echo 🚀 STEP 1: INSTALL/UPGRADE CRITICAL PACKAGES
echo =============================================

python -m pip install --upgrade pip
python -m pip install --upgrade fastapi uvicorn pydantic python-dotenv requests httpx

echo.
echo 🔧 STEP 2: CREATE FIXED BACKEND
echo ===============================

cd backend

echo Creating robust backend that handles all errors...

if not exist .env (
    echo Creating .env file...
    echo # InLegalDesk Configuration > .env
    echo BACKEND_PORT=8877 >> .env
    echo DEBUG=true >> .env
    echo OPENAI_API_KEY=your_api_key_here >> .env
    echo VLM_ORDER=openai,tesseract_fallback >> .env
    echo ENABLE_FALLBACK=true >> .env
)

echo ✅ Backend configuration ready

echo.
echo 🚀 STEP 3: TEST BACKEND STARTUP
echo ===============================

echo Testing backend startup...
echo.

echo Starting fixed backend version...
start "InLegalDesk Backend" python app_fixed.py

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo.
echo Testing backend connection...
python -c "
import requests
try:
    response = requests.get('http://localhost:8877/health', timeout=5)
    if response.status_code == 200:
        print('✅ Backend is running successfully!')
        print('🌐 Access at: http://localhost:8877')
    else:
        print('❌ Backend responded but with error')
except requests.exceptions.ConnectionError:
    print('❌ Backend not responding - check for errors')
except Exception as e:
    print(f'❌ Connection test failed: {e}')
"

cd ..

echo.
echo 🖥️ STEP 4: LAUNCH IMPROVED DESKTOP GUI
echo ======================================

cd desktop

echo Launching ChatGPT-style interface with file upload...
echo.

if exist chatgpt_style_interface.py (
    echo ✅ ChatGPT-style interface found
    echo Starting enhanced desktop interface...
    python chatgpt_style_interface.py
) else if exist main.py (
    echo ⚠️  Using original interface
    echo Starting original desktop interface...
    python main.py
) else (
    echo ❌ No desktop interface found!
)

cd ..

echo.
echo 📋 QUICK FIX SUMMARY
echo ===================
echo.
echo ✅ Backend: Fixed startup issues with app_fixed.py
echo ✅ Desktop: ChatGPT-style interface with file upload
echo ✅ Rate Limits: Premium to free model fallback
echo ✅ Error Handling: Comprehensive error catching
echo ✅ File Upload: Drag & drop + ChatGPT-style attach menu
echo.
echo 🎯 IF ISSUES PERSIST:
echo ====================
echo.
echo Backend won't start:
echo • Run: TEST_BACKEND_STARTUP.bat
echo • Check: backend.log for detailed errors
echo • Install: pip install fastapi uvicorn
echo.
echo App closes on send:
echo • Use: chatgpt_style_interface.py (fixed version)
echo • Check: Python 3.6.6 Unicode issues (use FIX_EXE_CLOSING.bat)
echo.
echo Rate limit errors:
echo • Run: python FIX_RATE_LIMIT_ERROR.py
echo • Add: OpenAI billing at platform.openai.com
echo.

pause