@echo off
REM Test backend startup and diagnose issues

echo.
echo ================================================
echo  InLegalDesk - Backend Startup Diagnosis
echo  (Find out why backend server fails to start)
echo ================================================
echo.

echo 🔍 STEP 1: BASIC CHECKS
echo ========================

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    goto :end
)

echo ✅ Python found:
python --version

echo.
echo 📂 Checking directories...
if exist backend (
    echo ✅ backend/ directory found
    cd backend
) else (
    echo ❌ backend/ directory not found!
    echo Make sure you're in the InLegalDesk root directory
    goto :end
)

echo.
echo 📄 Checking backend files...
if exist app.py (
    echo ✅ app.py found
) else (
    echo ❌ app.py not found!
)

if exist app_fixed.py (
    echo ✅ app_fixed.py found (backup version)
) else (
    echo ❌ app_fixed.py not found
)

echo.
echo 🔧 STEP 2: TESTING PYTHON PACKAGES
echo ==================================

echo Testing critical packages...

python -c "import fastapi; print('✅ FastAPI available')" 2>nul || echo "❌ FastAPI missing - run: pip install fastapi"

python -c "import uvicorn; print('✅ Uvicorn available')" 2>nul || echo "❌ Uvicorn missing - run: pip install uvicorn"

python -c "import pydantic; print('✅ Pydantic available')" 2>nul || echo "❌ Pydantic missing - run: pip install pydantic"

python -c "from dotenv import load_dotenv; print('✅ python-dotenv available')" 2>nul || echo "❌ python-dotenv missing - run: pip install python-dotenv"

echo.
echo 🚀 STEP 3: TESTING BACKEND STARTUP
echo ==================================

echo Testing if backend can start...

if exist app_fixed.py (
    echo Using app_fixed.py (robust version)...
    echo Starting backend with detailed error reporting...
    echo.
    python app_fixed.py
) else if exist app.py (
    echo Using app.py (original version)...
    echo Starting backend...
    echo.
    python app.py
) else (
    echo ❌ No backend app file found!
    echo.
    echo 🔧 Creating emergency backend...
    
    echo import uvicorn > emergency_backend.py
    echo from fastapi import FastAPI >> emergency_backend.py
    echo. >> emergency_backend.py
    echo app = FastAPI() >> emergency_backend.py
    echo. >> emergency_backend.py
    echo @app.get("/") >> emergency_backend.py
    echo def root(): >> emergency_backend.py
    echo     return {"message": "InLegalDesk Emergency Backend Running"} >> emergency_backend.py
    echo. >> emergency_backend.py
    echo @app.get("/health") >> emergency_backend.py
    echo def health(): >> emergency_backend.py
    echo     return {"status": "healthy"} >> emergency_backend.py
    echo. >> emergency_backend.py
    echo if __name__ == "__main__": >> emergency_backend.py
    echo     uvicorn.run(app, host="0.0.0.0", port=8877) >> emergency_backend.py
    
    echo ✅ Emergency backend created
    echo Starting emergency backend...
    python emergency_backend.py
)

:end
echo.
echo 📋 DIAGNOSIS COMPLETED
echo =====================
echo.
echo If backend still fails to start:
echo 1. Install missing packages shown above
echo 2. Check Python version (3.7+ recommended)
echo 3. Verify you're in the correct directory
echo 4. Check for port conflicts (8877)
echo.

pause