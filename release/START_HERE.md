# InLegalDesk v1.0.1 - AI-Powered Indian Legal Research

## 🚀 Quick Start (Windows)

### Option 1: Build Installer (Recommended)
1. Ensure you have Python 3.8+ and Inno Setup 6 installed
2. Double-click: build_windows_installer.bat
3. Wait for build to complete
4. Run: installer\output\InLegalDesk_Installer.exe

### Option 2: Run from Source
1. Install Python 3.8+ from python.org
2. Open Command Prompt as Administrator
3. Navigate to this folder
4. Run setup commands:

```cmd
REM Setup backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.sample .env
REM Edit .env file and add your OpenAI API key
python app.py
```

```cmd
REM Setup desktop (new Command Prompt)
cd desktop
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
xcopy /E /I ..\backend server
python main.py
```

## ✨ Features
- 🤖 Hybrid BERT+GPT AI architecture
- ⚖️ Indian legal research specialization  
- 💬 ChatGPT-style interface
- 🔒 Secure credential management
- 📄 OCR-free PDF processing
- 🌐 Bilingual support (English + Hindi)

## 📞 Support
- GitHub: https://github.com/ravidatanerd/LEGAL_BERT_IN
- Issues: https://github.com/ravidatanerd/LEGAL_BERT_IN/issues
- Documentation: See README.md and other guides

## ⚠️ Important
- OpenAI API key required for full features
- First run downloads AI models (~2GB)
- Windows 10/11 (64-bit) required
