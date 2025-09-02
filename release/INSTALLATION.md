# 📦 InLegalDesk Installation Guide

## 🚀 **Quick Installation (Recommended)**

### **For End Users:**
1. **Download**: Get `InLegalDesk_Installer.exe` from [GitHub Releases](https://github.com/YOUR_USERNAME/inlegaldesk/releases)
2. **Verify**: Check SHA256 checksum (optional but recommended)
3. **Install**: Run as Administrator → Follow wizard
4. **Launch**: Start from Start Menu or Desktop
5. **Configure**: Click "🔑 API Credentials" to set up OpenAI API key
6. **Enjoy**: Start your AI-powered legal research!

### **System Requirements:**
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 8GB recommended (4GB minimum)
- **Storage**: 2GB free disk space
- **Internet**: Required for AI model downloads and API features

---

## 🔐 **Security Verification (Recommended)**

### **Verify Installer Integrity:**
```cmd
REM Download verify_installer.bat from releases and run:
verify_installer.bat

REM Or verify manually:
certutil -hashfile InLegalDesk_Installer.exe SHA256
REM Compare output with InLegalDesk_Installer.exe.sha256 file
```

### **Safe Installation Practices:**
- ✅ **Download from official GitHub releases only**
- ✅ **Verify checksums before installation**
- ✅ **Run as Administrator for proper installation**
- ✅ **Keep Windows Defender/antivirus enabled**
- ✅ **Use latest version for security updates**

---

## 🎯 **Installation Options**

### **Option 1: Standard Installation (Recommended)**
```cmd
REM Double-click installer or run:
InLegalDesk_Installer.exe

REM Follow installation wizard:
REM 1. Accept license
REM 2. Choose installation directory
REM 3. Select components
REM 4. Create shortcuts (optional)
REM 5. Install
```

### **Option 2: Silent Installation (Enterprise)**
```cmd
REM Silent install to default location:
InLegalDesk_Installer.exe /SILENT

REM Silent install to custom location:
InLegalDesk_Installer.exe /SILENT /DIR="C:\MyApps\InLegalDesk"

REM Very silent (no UI):
InLegalDesk_Installer.exe /VERYSILENT

REM Silent with desktop icon:
InLegalDesk_Installer.exe /SILENT /TASKS="desktopicon"
```

### **Option 3: Development Installation**
```bash
# For developers who want to run from source:

# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/inlegaldesk.git
cd inlegaldesk

# 2. Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.sample .env
# Edit .env with your OpenAI API key

# 3. Setup desktop (new terminal)
cd desktop
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp -r ../backend server/

# 4. Run
# Terminal 1: python backend/app.py
# Terminal 2: python desktop/main.py
```

---

## ⚙️ **Post-Installation Configuration**

### **First Launch Setup:**
1. **Launch InLegalDesk** from Start Menu
2. **Welcome Dialog** appears with setup options
3. **Click "🔑 API Credentials"** to configure OpenAI API key
4. **Enter API Key**: Get from https://platform.openai.com/api-keys
5. **Set Master Password**: Choose strong password for encryption
6. **Test Connection**: Verify credentials work
7. **Save Encrypted**: Credentials stored securely with AES-256

### **Optional Configuration:**
1. **Click "⚙️ Settings"** for advanced options
2. **Security Tab**: Configure file upload limits, validation
3. **Performance Tab**: Adjust AI model settings
4. **Privacy Tab**: Control data handling preferences

### **Initial Setup:**
1. **Click "📚 Ingest Statutes"** to download Indian legal statutes
2. **Wait for Download**: IPC, CrPC, Evidence Act (~50MB total)
3. **Upload Documents**: Drag PDFs for analysis (optional)
4. **Start Researching**: Ask legal questions and generate judgments

---

## 🧪 **Verify Installation**

### **Quick Functionality Test:**
1. **Launch App**: InLegalDesk should open with ChatGPT-style interface
2. **Check Status**: Left panel should show "Backend: Connected ✓"
3. **Test Question**: Ask "What is Section 302 IPC?"
4. **Verify Response**: Should get AI response with citations
5. **Test Upload**: Drag a PDF file to test document processing

### **Expected Behavior:**
- **Startup Time**: 10-30 seconds (first launch downloads AI models)
- **Model Download**: ~2GB total (InLegalBERT, T5, XLNet models)
- **Response Time**: 2-10 seconds per question
- **Memory Usage**: 2-4GB RAM during operation

---

## 🔧 **Troubleshooting**

### **Installation Issues:**

#### **"Windows protected your PC"**
```
This is normal for new applications:
1. Click "More info"
2. Click "Run anyway"
3. Or right-click installer → Properties → Unblock
```

#### **"Installation failed"**
```
Solutions:
1. Run as Administrator
2. Disable antivirus temporarily
3. Free up disk space (need 2GB+)
4. Close other applications
```

#### **"Python not found" (Development mode)**
```
Solutions:
1. Install Python 3.8+ from python.org
2. Check "Add Python to PATH" during installation
3. Restart command prompt
```

### **Runtime Issues:**

#### **"Backend failed to start"**
```
Solutions:
1. Check if port 8877 is available
2. Allow through Windows Firewall
3. Restart application
4. Check antivirus isn't blocking
```

#### **"Model download failed"**
```
Solutions:
1. Check internet connection
2. Ensure 2GB+ free space
3. Allow through firewall
4. Try different network
```

#### **"API key invalid"**
```
Solutions:
1. Get new key from OpenAI platform
2. Check key format (starts with sk-)
3. Verify key is active
4. Test connection in credential dialog
```

---

## 🗑️ **Uninstallation**

### **Standard Uninstall:**
1. **Control Panel**: Apps & Features → InLegalDesk → Uninstall
2. **Or Start Menu**: InLegalDesk → Uninstall InLegalDesk
3. **Follow Wizard**: Confirm removal
4. **Clean Removal**: All files and registry entries removed

### **Manual Cleanup (if needed):**
```cmd
REM Remove remaining files:
rmdir /s "C:\Program Files\InLegalDesk"
rmdir /s "%APPDATA%\InLegalDesk"

REM Remove Start Menu shortcuts:
del "%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\InLegalDesk\*"
```

---

## 🎯 **Installation Success Indicators**

### **✅ Successful Installation:**
- InLegalDesk appears in Start Menu
- Desktop shortcut created (if selected)
- Application launches without errors
- Backend connects automatically
- Credential dialog appears on first run

### **✅ Successful Configuration:**
- API credentials saved successfully
- "Backend: Connected ✓" status shown
- Models download without errors
- Questions get AI responses
- PDF upload works

### **✅ Full Functionality:**
- Legal questions answered with citations
- Judgment generation works
- PDF documents processed
- Export features functional
- Hybrid AI analysis available

---

## 📞 **Getting Help**

### **Support Resources:**
- **📖 Documentation**: Complete guides in GitHub repository
- **🐛 Bug Reports**: [GitHub Issues](https://github.com/YOUR_USERNAME/inlegaldesk/issues)
- **💬 Community**: [GitHub Discussions](https://github.com/YOUR_USERNAME/inlegaldesk/discussions)
- **📧 Contact**: Create GitHub issue for support

### **Before Reporting Issues:**
1. **Check Requirements**: Verify system meets minimum requirements
2. **Try Restart**: Restart application and try again
3. **Check Logs**: Look for error messages in application
4. **Update**: Ensure you have the latest version
5. **Search Issues**: Check if issue already reported

---

## 🎉 **Welcome to InLegalDesk!**

### **You're Ready to:**
- 🔍 **Research Indian Legal Questions** with AI assistance
- ⚖️ **Generate Legal Judgments** with structured analysis
- 📄 **Process Legal Documents** with OCR-free AI extraction
- 🤖 **Experience Hybrid AI** with BERT+GPT architecture
- 🔒 **Work Securely** with encrypted credential management

### **Next Steps:**
1. **Explore Features**: Try different question types and modes
2. **Upload Documents**: Add your legal PDFs for analysis
3. **Configure Settings**: Customize performance and security options
4. **Join Community**: Participate in discussions and feedback
5. **Stay Updated**: Watch repository for new releases

**🎊 Welcome to the future of AI-powered legal research in India!**