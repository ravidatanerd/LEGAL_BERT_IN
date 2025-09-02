# 🏗️ Build InLegalDesk Installer - Complete Guide

## 📦 **Create Your Own Installer**

Since I cannot upload binary files to GitHub, here's how to build the installer yourself on Windows.

---

## 🎯 **Quick Build (5 minutes)**

### **Prerequisites (One-time setup):**
1. **Windows 10/11** (64-bit)
2. **Python 3.8+**: Download from [python.org](https://www.python.org/downloads/)
3. **Inno Setup 6**: Download from [jrsoftware.org](https://jrsoftware.org/isinfo.php)
4. **Git** (optional): For cloning the repository

### **Build Steps:**
```powershell
# 1. Clone or download the project
git clone <your-repo-url>
cd inlegaldesk

# 2. Build the installer
cd installer
.\build_installer.ps1

# 3. Your installer is ready!
# Location: installer\output\InLegalDesk_Installer.exe
```

**That's it!** The installer will be created automatically.

---

## 🔧 **Detailed Build Instructions**

### **Step 1: Install Prerequisites**

#### **Python 3.8+**
1. Download from [python.org](https://www.python.org/downloads/)
2. **Important**: Check "Add Python to PATH" during installation
3. Verify: Open PowerShell and run `python --version`

#### **Inno Setup 6**
1. Download from [jrsoftware.org](https://jrsoftware.org/isinfo.php)
2. Install with default settings
3. Default location: `C:\Program Files (x86)\Inno Setup 6\`

### **Step 2: Prepare Project**
```powershell
# Download the project files
# Either clone with git or download ZIP from GitHub

# Navigate to project
cd inlegaldesk
```

### **Step 3: Build Installer**
```powershell
# Navigate to installer directory
cd installer

# Run the build script
.\build_installer.ps1

# For advanced options:
.\build_installer.ps1 -BuildType onefile  # Single executable
.\build_installer.ps1 -BuildType onedir   # Folder with dependencies
```

### **Step 4: Locate Your Installer**
```
📁 installer/
  📁 output/
    📄 InLegalDesk_Installer.exe  ← Your installer!
```

---

## 🎯 **Alternative: Manual Build**

If the PowerShell script doesn't work, build manually:

### **Step 1: Setup Environment**
```cmd
cd desktop
python -m venv build_env
build_env\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
```

### **Step 2: Copy Backend**
```cmd
xcopy /E /I ..\backend server
```

### **Step 3: Build Executable**
```cmd
pyinstaller --noconfirm --onedir --name InLegalDesk ^
  --add-data "server;server" ^
  --add-data ".env.sample;.env.sample" ^
  --icon "..\installer\assets\icon.ico" ^
  main.py
```

### **Step 4: Build Installer**
```cmd
cd ..\installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" InLegalDesk.iss
```

---

## 📋 **Build Verification**

### **Check Build Success:**
1. **Executable Created**: `desktop\dist\InLegalDesk\InLegalDesk.exe`
2. **Installer Created**: `installer\output\InLegalDesk_Installer.exe`
3. **Size Check**: Installer should be 200-500MB
4. **Test Run**: Double-click installer to test

### **Build Troubleshooting:**

#### **Python Not Found**
```powershell
# Check Python installation
python --version
# If not found, reinstall Python with "Add to PATH" checked
```

#### **Inno Setup Not Found**
```powershell
# Check Inno Setup installation
dir "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
# If not found, reinstall Inno Setup
```

#### **PyInstaller Fails**
```powershell
# Clean and retry
rmdir /s dist build
pip install --upgrade pyinstaller
# Retry build
```

---

## 🎮 **Test Your Installer**

### **Installation Test:**
1. **Run Installer**: Double-click `InLegalDesk_Installer.exe`
2. **Follow Wizard**: Accept defaults or customize
3. **Launch App**: Start from Start Menu or Desktop
4. **Configure**: Click "🔑 API Credentials" to set up OpenAI key
5. **Test Features**: Upload PDFs, ask legal questions

### **Uninstall Test:**
1. **Control Panel**: Apps & Features → InLegalDesk → Uninstall
2. **Verify Cleanup**: Check that all files are removed

---

## 📤 **Distribute Your Installer**

### **Sharing Options:**

#### **GitHub Releases:**
1. Create a release on your GitHub repository
2. Upload `InLegalDesk_Installer.exe` as a release asset
3. Users can download directly from GitHub

#### **Direct Distribution:**
1. Upload to your website/cloud storage
2. Share download link with users
3. Include installation instructions

#### **Enterprise Distribution:**
```cmd
# Silent installation for IT departments
InLegalDesk_Installer.exe /SILENT /DIR="C:\Program Files\InLegalDesk"
```

---

## 🔧 **Customization Options**

### **Branding Customization:**
Edit `installer\InLegalDesk.iss`:
```ini
#define AppName "YourCompany Legal Research"
#define AppPublisher "Your Company Name"
#define AppURL "https://yourwebsite.com"
```

### **Icon Customization:**
Replace `installer\assets\icon.ico` with your custom icon:
- **Format**: ICO file
- **Sizes**: 16x16, 32x32, 48x48, 256x256
- **Tools**: Use online ICO converters

### **Build Configuration:**
Edit `installer\build_installer.ps1`:
```powershell
# Change default build type
$BuildType = "onefile"  # or "onedir"

# Custom Python path
$PythonPath = "C:\Python39\python.exe"
```

---

## 📊 **Expected Build Results**

### **Build Outputs:**
- **Executable**: 200-300MB (includes all dependencies)
- **Installer**: 250-400MB (compressed)
- **Build Time**: 5-15 minutes (depending on hardware)

### **Installer Features:**
- **Professional UI**: Modern installation wizard
- **Start Menu**: Automatic shortcuts
- **Desktop Icon**: Optional desktop shortcut
- **Uninstaller**: Complete removal capability
- **File Association**: Optional PDF association
- **Silent Install**: Enterprise deployment support

---

## 🎯 **GitHub Repository Setup**

### **Repository Structure for Distribution:**
```
your-repo/
├── README.md                    # Main documentation
├── backend/                     # FastAPI backend
├── desktop/                     # PySide6 desktop app
├── installer/                   # Build scripts
├── docs/                        # Documentation
└── releases/                    # For installer uploads
    └── v1.0.0/
        └── InLegalDesk_Installer.exe
```

### **GitHub Release Process:**
1. **Create Release**: Go to your repo → Releases → Create Release
2. **Upload Installer**: Attach `InLegalDesk_Installer.exe`
3. **Add Description**: Include installation and usage instructions
4. **Publish**: Make available for download

### **Release Notes Template:**
```markdown
# InLegalDesk v1.0.0 - AI-Powered Indian Legal Research

## 📥 Download
- **Windows Installer**: [InLegalDesk_Installer.exe](link-to-file)
- **Size**: ~300MB
- **Requirements**: Windows 10/11 (64-bit)

## 🚀 Quick Start
1. Download and run the installer
2. Launch InLegalDesk from Start Menu
3. Click "🔑 API Credentials" to configure OpenAI API key
4. Start researching Indian legal questions!

## ✨ Features
- ChatGPT-style legal research interface
- OCR-free PDF processing with vision-language models
- InLegalBERT embeddings for Indian law
- Secure credential management with AES-256 encryption
- Bilingual support (English/Hindi)
```

---

## 🎊 **Ready to Build!**

### **Your Next Steps:**
1. **Set up Windows machine** with Python and Inno Setup
2. **Download project files** from your repository
3. **Run build script**: `installer\build_installer.ps1`
4. **Test installer**: Install and verify functionality
5. **Upload to GitHub**: Create release with installer
6. **Share with users**: Distribute download link

### **Build Time Estimate:**
- **First build**: 15-20 minutes (downloads dependencies)
- **Subsequent builds**: 5-10 minutes (cached dependencies)

**🎉 You now have everything needed to create a professional Windows installer for your InLegalDesk platform!**

The installer will include:
- ✅ Complete application with all dependencies
- ✅ Professional installation wizard
- ✅ Start Menu and desktop shortcuts
- ✅ Secure credential management
- ✅ All AI and security features
- ✅ Complete uninstall capability

**Ready to build your installer and share your AI-powered legal research platform with the world!** 🚀