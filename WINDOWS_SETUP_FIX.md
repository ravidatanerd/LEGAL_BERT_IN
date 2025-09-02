# 🔧 Windows Setup Error Fix

## 🚨 **Virtual Environment Error Fixed!**

The error occurs because you're already in a virtual environment or there's a naming conflict.

---

## ✅ **Quick Fix (Windows)**

### **Step 1: Exit Any Existing Virtual Environment**
```cmd
REM If you see (venv) in your prompt, deactivate first:
deactivate

REM Or close Command Prompt and open a new one
```

### **Step 2: Clean Setup (Fresh Start)**
```cmd
REM Open NEW Command Prompt as Administrator
REM Navigate to the extracted folder
cd H:\Downloads\LEGAL_BERT_IN-main\LEGAL_BERT_IN-main

REM Remove any existing venv directories
rmdir /s backend\venv 2>nul
rmdir /s desktop\venv 2>nul

REM Setup Backend
cd backend
python -m venv backend_env
backend_env\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
copy .env.sample .env
REM Edit .env file and add your OpenAI API key
python app.py
```

### **Step 3: Setup Desktop (NEW Command Prompt)**
```cmd
REM Open ANOTHER NEW Command Prompt as Administrator
cd H:\Downloads\LEGAL_BERT_IN-main\LEGAL_BERT_IN-main\desktop

python -m venv desktop_env
desktop_env\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
xcopy /E /I ..\backend server
python main.py
```

---

## 🎯 **Alternative: Simple Setup**

### **Even Simpler Method:**
```cmd
REM Don't use virtual environments at all (simpler but less clean)
cd H:\Downloads\LEGAL_BERT_IN-main\LEGAL_BERT_IN-main\backend

REM Install directly to system Python
pip install --upgrade pip
pip install -r requirements.txt
copy .env.sample .env
python app.py

REM New Command Prompt for desktop:
cd H:\Downloads\LEGAL_BERT_IN-main\LEGAL_BERT_IN-main\desktop
pip install -r requirements.txt
xcopy /E /I ..\backend server
python main.py
```

---

## 🛠️ **Troubleshooting Common Issues**

### **Issue 1: "python not found"**
```cmd
REM Solution: Add Python to PATH or use full path
"C:\Python39\python.exe" -m venv backend_env
```

### **Issue 2: "Permission denied"**
```cmd
REM Solution: Run Command Prompt as Administrator
REM Right-click Command Prompt → "Run as administrator"
```

### **Issue 3: "venv already exists"**
```cmd
REM Solution: Use different names or remove existing
rmdir /s venv
python -m venv new_env
new_env\Scripts\activate
```

### **Issue 4: "Scripts\activate not found"**
```cmd
REM Solution: Check if venv was created properly
dir backend_env\Scripts\
REM Should see activate.bat file
```

---

## ⚡ **Ultra-Quick Setup (Minimal)**

### **If you just want to test the platform:**
```cmd
REM Minimal installation (fastest)
cd backend
pip install fastapi uvicorn pydantic python-dotenv transformers torch
copy .env.sample .env
python app.py

REM New Command Prompt:
cd desktop  
pip install PySide6 httpx python-dotenv markdown
python main.py
```

---

## 🎯 **Expected Success Indicators:**

### **✅ Backend Working:**
```
INFO: Started server process
INFO: Uvicorn running on http://0.0.0.0:8877
INFO: InLegalBERT model downloading...
INFO: Hybrid AI system initialized
```

### **✅ Desktop Working:**
- GUI window opens with ChatGPT-style interface
- Left panel shows "Backend: Connected ✓"
- Can click "🔑 API Credentials" button

---

## 📞 **Still Having Issues?**

### **Create GitHub Issue:**
1. **Go to**: https://github.com/ravidatanerd/LEGAL_BERT_IN/issues
2. **Click**: "New issue"
3. **Include**:
   - Your Python version: `python --version`
   - Your Windows version
   - Full error message
   - Steps you tried

### **Quick Test:**
```cmd
REM Test if Python is working:
python --version
pip --version

REM Should show Python 3.8+ and pip version
```

---

## 🎊 **Your Platform Will Work!**

The virtual environment error is a common Windows setup issue. The fixes above will resolve it and get your **InLegalDesk hybrid BERT+GPT AI platform** running successfully!

**🚀 Once fixed, you'll have access to:**
- 🤖 **Hybrid AI**: InLegalBERT + T5 + XLNet + OpenAI integration
- ⚖️ **Legal Research**: Indian law specialization
- 💬 **ChatGPT Interface**: Modern legal research experience
- 🔒 **Secure Credentials**: AES-256 encryption
- 📄 **PDF Processing**: OCR-free document analysis

**The platform is ready - just need to get past this Windows setup hurdle!** 🎉