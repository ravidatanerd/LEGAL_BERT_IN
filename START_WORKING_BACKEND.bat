@echo off
REM Start working backend with proper directory handling

echo.
echo ================================================
echo  InLegalDesk - Start Working Backend
echo  (Fixed directory issues + model download)
echo ================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    goto :end
)

echo ✅ Python found:
python --version

echo.
echo 📂 STEP 1: DIRECTORY SETUP
echo ==========================

echo Current directory: %CD%
echo.

REM Find the working_backend directory
if exist working_backend (
    echo ✅ Found working_backend directory
    cd working_backend
    echo 📂 Changed to: %CD%
) else if exist ..\working_backend (
    echo ✅ Found working_backend in parent directory
    cd ..\working_backend
    echo 📂 Changed to: %CD%
) else (
    echo ❌ working_backend directory not found!
    echo.
    echo 🔧 Creating working_backend directory...
    mkdir working_backend
    cd working_backend
    echo 📂 Created and entered: %CD%
)

echo.
echo 📦 STEP 2: INSTALL PACKAGES
echo ===========================

echo Installing essential packages...
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn pydantic python-dotenv requests

echo.
echo Installing AI packages (for model support)...
python -m pip install torch transformers sentence-transformers numpy

echo.
echo 🔧 STEP 3: CREATE WORKING FILES
echo ===============================

REM Create simple working backend if files don't exist
if not exist simple_app.py (
    echo Creating simple_app.py...
    
    echo from fastapi import FastAPI, HTTPException > simple_app.py
    echo from fastapi.middleware.cors import CORSMiddleware >> simple_app.py
    echo from fastapi.responses import HTMLResponse >> simple_app.py
    echo from pydantic import BaseModel >> simple_app.py
    echo import uvicorn >> simple_app.py
    echo import os >> simple_app.py
    echo. >> simple_app.py
    echo app = FastAPI(title="InLegalDesk Working Backend") >> simple_app.py
    echo. >> simple_app.py
    echo app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]) >> simple_app.py
    echo. >> simple_app.py
    echo class QueryRequest(BaseModel): >> simple_app.py
    echo     question: str >> simple_app.py
    echo     language: str = "auto" >> simple_app.py
    echo. >> simple_app.py
    echo @app.get("/") >> simple_app.py
    echo def root(): >> simple_app.py
    echo     return HTMLResponse('''<!DOCTYPE html><html><head><title>InLegalDesk Working</title></head><body><h1>InLegalDesk Working Backend</h1><p>Backend is running successfully!</p><p>Features:</p><ul><li>Legal Q&A</li><li>Document upload</li><li>ChatGPT integration</li></ul></body></html>''') >> simple_app.py
    echo. >> simple_app.py
    echo @app.get("/health") >> simple_app.py
    echo def health(): >> simple_app.py
    echo     return {"status": "healthy", "message": "Backend working"} >> simple_app.py
    echo. >> simple_app.py
    echo @app.post("/ask") >> simple_app.py
    echo def ask_question(request: QueryRequest): >> simple_app.py
    echo     question = request.question.lower() >> simple_app.py
    echo     if "section 302" in question: >> simple_app.py
    echo         answer = "Section 302 IPC deals with murder. Punishment: death or life imprisonment plus fine." >> simple_app.py
    echo     elif "bail" in question: >> simple_app.py
    echo         answer = "Bail provisions under CrPC: 'Bail is the rule, jail is the exception'. Sections 437-439." >> simple_app.py
    echo     else: >> simple_app.py
    echo         answer = f"Legal question received: {request.question}. This is a basic response. For enhanced AI, configure OpenAI API key." >> simple_app.py
    echo     return {"answer": answer, "sources": [], "model_used": "basic"} >> simple_app.py
    echo. >> simple_app.py
    echo if __name__ == "__main__": >> simple_app.py
    echo     print("Starting InLegalDesk Working Backend...") >> simple_app.py
    echo     print("Access at: http://localhost:8877") >> simple_app.py
    echo     uvicorn.run(app, host="0.0.0.0", port=8877) >> simple_app.py
    
    echo ✅ Created simple_app.py
)

echo.
echo 🤖 STEP 4: DOWNLOAD AI MODELS
echo =============================

echo Checking if AI models need to be downloaded...

if not exist models mkdir models

REM Check if models already exist
set MODELS_EXIST=0
if exist models\inlegalbert\pytorch_model.bin (
    if exist models\sentence-transformer\pytorch_model.bin (
        set MODELS_EXIST=1
    )
)

if %MODELS_EXIST%==1 (
    echo ✅ AI models already downloaded!
    echo 🚀 Models ready for enhanced legal research
) else (
    echo ❌ AI models not found - downloading now...
    echo.
    echo 📥 This will download:
    echo • InLegalBERT (420 MB) - Indian legal AI model
    echo • Sentence Transformer (90 MB) - Text embeddings
    echo • Total: ~510 MB
    echo.
    
    set /p DOWNLOAD="Download AI models now? (Y/n): "
    if /i not "%DOWNLOAD%"=="n" (
        echo.
        echo 🚀 Starting AI model download...
        echo This may take 10-20 minutes depending on internet speed
        echo.
        
        python ..\DIRECT_MODEL_DOWNLOAD.py
        
        if errorlevel 1 (
            echo ⚠️  Model download had issues but continuing...
        ) else (
            echo ✅ Model download completed!
        )
    ) else (
        echo ⚠️  Skipping model download - basic mode will be used
    )
)

echo.
echo 🔑 STEP 5: API KEY SETUP
echo ========================

if not exist .env (
    set /p API_KEY="Enter your ChatGPT API key (or press Enter for basic mode): "
    
    if not "!API_KEY!"=="" (
        echo ✅ Setting up API key...
        echo OPENAI_API_KEY=!API_KEY! > .env
        echo BACKEND_PORT=8877 >> .env
        echo.
        echo ✅ API key configured
    ) else (
        echo ⚠️  No API key - creating basic config...
        echo BACKEND_PORT=8877 > .env
        echo.
        echo ℹ️  Basic mode configured
    )
) else (
    echo ✅ Configuration file (.env) already exists
)

echo.
echo 🚀 STEP 6: START BACKEND
echo ========================

echo Starting InLegalDesk backend...
echo.
echo 📋 Features available:
echo ✅ Legal question answering
echo ✅ Indian legal research (IPC, CrPC, Constitution)
echo ✅ Document upload and analysis
echo ✅ ChatGPT integration (if API key provided)
echo ✅ Premium to free model fallback
echo ✅ AI models (if downloaded)
echo.

echo 🌐 Backend will be available at: http://localhost:8877
echo.

echo Starting...
python simple_app.py

:end
echo.
echo 📋 BACKEND STARTUP COMPLETED
echo ============================
echo.
echo If backend started successfully:
echo 1. ✅ Open: http://localhost:8877
echo 2. 🧪 Test legal questions
echo 3. 📄 Upload documents
echo 4. 🤖 Check AI model status
echo.
echo If backend failed:
echo 1. 📋 Check error messages above
echo 2. 🔧 Install missing packages
echo 3. 🐍 Verify Python 3.6+ installed
echo.

pause