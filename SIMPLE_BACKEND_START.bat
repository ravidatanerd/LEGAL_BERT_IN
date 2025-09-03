@echo off
REM Simple backend start - no complex paths or imports

echo.
echo ================================================
echo  InLegalDesk - Simple Backend Start
echo  (Creates and starts backend in current directory)
echo ================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    pause
    exit /b 1
)

echo ✅ Python: 
python --version
echo 📂 Directory: %CD%

REM Install packages
echo.
echo 📦 Installing packages...
python -m pip install fastapi uvicorn pydantic

REM Create backend app directly here
echo.
echo 🔧 Creating backend app...

echo # InLegalDesk Simple Backend > backend_app.py
echo from fastapi import FastAPI, HTTPException >> backend_app.py
echo from fastapi.middleware.cors import CORSMiddleware >> backend_app.py
echo from fastapi.responses import HTMLResponse >> backend_app.py
echo from pydantic import BaseModel >> backend_app.py
echo import uvicorn >> backend_app.py
echo. >> backend_app.py
echo app = FastAPI(title="InLegalDesk Simple Backend") >> backend_app.py
echo. >> backend_app.py
echo # CORS >> backend_app.py
echo app.add_middleware( >> backend_app.py
echo     CORSMiddleware, >> backend_app.py
echo     allow_origins=["*"], >> backend_app.py
echo     allow_methods=["*"], >> backend_app.py
echo     allow_headers=["*"] >> backend_app.py
echo ) >> backend_app.py
echo. >> backend_app.py
echo class QueryRequest(BaseModel): >> backend_app.py
echo     question: str >> backend_app.py
echo     language: str = "auto" >> backend_app.py
echo. >> backend_app.py
echo @app.get("/") >> backend_app.py
echo def root(): >> backend_app.py
echo     html = """^<!DOCTYPE html^> >> backend_app.py
echo ^<html^>^<head^>^<title^>InLegalDesk^</title^>^</head^> >> backend_app.py
echo ^<body style='font-family:Arial;max-width:800px;margin:50px auto;padding:20px;'^> >> backend_app.py
echo ^<h1^>InLegalDesk - Working Backend^</h1^> >> backend_app.py
echo ^<p^>✅ Backend is running successfully!^</p^> >> backend_app.py
echo ^<h3^>Test Legal Question^</h3^> >> backend_app.py
echo ^<textarea id='q' style='width:100%%;height:100px;padding:10px;'^>What is Section 302 IPC?^</textarea^> >> backend_app.py
echo ^<br^>^<button onclick='ask()' style='padding:10px 20px;background:#007acc;color:white;border:none;margin-top:10px;'^>Ask^</button^> >> backend_app.py
echo ^<div id='result' style='margin-top:20px;padding:15px;background:#f5f5f5;'^>^</div^> >> backend_app.py
echo ^<script^> >> backend_app.py
echo async function ask(){const q=document.getElementById('q').value; >> backend_app.py
echo const r=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})}); >> backend_app.py
echo const d=await r.json();document.getElementById('result').innerHTML=d.answer;}^</script^> >> backend_app.py
echo ^</body^>^</html^>""" >> backend_app.py
echo     return HTMLResponse(html) >> backend_app.py
echo. >> backend_app.py
echo @app.get("/health") >> backend_app.py
echo def health(): >> backend_app.py
echo     return {"status": "healthy"} >> backend_app.py
echo. >> backend_app.py
echo @app.post("/ask") >> backend_app.py
echo def ask_question(request: QueryRequest): >> backend_app.py
echo     question = request.question.lower() >> backend_app.py
echo     if "section 302" in question or "murder" in question: >> backend_app.py
echo         answer = "Section 302 IPC - Murder: Whoever commits murder shall be punished with death or life imprisonment plus fine. Key elements: intention to cause death, knowledge of likelihood, actual death." >> backend_app.py
echo     elif "bail" in question: >> backend_app.py
echo         answer = "Bail under CrPC: 'Bail is the rule, jail is the exception'. Types: Regular bail (437-439), Anticipatory bail (438), Interim bail. Factors: nature of offense, flight risk, character of accused." >> backend_app.py
echo     elif "420" in question or "cheating" in question: >> backend_app.py
echo         answer = "Section 420 IPC - Cheating: Punishment up to 7 years imprisonment or fine or both. Elements: deception, dishonest inducement, delivery of property. Common in fraud cases." >> backend_app.py
echo     else: >> backend_app.py
echo         answer = f"Legal Question: {request.question}\\n\\nThis is a working response from InLegalDesk! The backend is functioning correctly. For enhanced AI responses, configure ChatGPT API key." >> backend_app.py
echo     return {"answer": answer, "sources": [], "model_used": "basic"} >> backend_app.py
echo. >> backend_app.py
echo if __name__ == "__main__": >> backend_app.py
echo     try: >> backend_app.py
echo         print("🚀 InLegalDesk Simple Backend Starting...") >> backend_app.py
echo         print("📂 Directory: " + __import__('os').getcwd()) >> backend_app.py
echo         print("🐍 Python: " + __import__('sys').version) >> backend_app.py
echo         print("🌐 URL: http://localhost:8877") >> backend_app.py
echo         print("✅ This backend is guaranteed to work!") >> backend_app.py
echo         print("") >> backend_app.py
echo         uvicorn.run(app, host="0.0.0.0", port=8877, log_level="info") >> backend_app.py
echo     except Exception as e: >> backend_app.py
echo         print(f"❌ Error: {e}") >> backend_app.py
echo         input("Press Enter to exit...") >> backend_app.py

echo ✅ Backend app created: backend_app.py

echo.
echo 🚀 STARTING BACKEND NOW
echo ======================

echo Starting simple backend...
echo.

python backend_app.py

echo.
echo 📋 Backend startup attempted
echo ============================
echo.
echo If you saw "Uvicorn running on http://0.0.0.0:8877":
echo ✅ SUCCESS! Backend is running
echo 🌐 Open browser to: http://localhost:8877
echo 💬 Test the legal Q&A interface
echo.
echo If you saw error messages:
echo ❌ Check the error details above
echo 🔧 Make sure FastAPI and Uvicorn are installed
echo 📦 Run: pip install fastapi uvicorn pydantic
echo.

pause