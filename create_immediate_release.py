#!/usr/bin/env python3
"""
Create immediate release package for InLegalDesk
Use this to create a downloadable package right now
"""
import os
import shutil
import zipfile
from pathlib import Path
import hashlib

def create_release_package():
    """Create immediate release package"""
    print("📦 Creating Immediate InLegalDesk Release Package")
    print("=" * 55)
    
    # Clean up any existing release
    if Path("InLegalDesk-Immediate-Release").exists():
        shutil.rmtree("InLegalDesk-Immediate-Release")
    
    release_dir = Path("InLegalDesk-Immediate-Release")
    release_dir.mkdir()
    
    print("\n📋 Step 1: Copying essential files...")
    
    # Files to include in release
    files_to_copy = [
        ("backend/", "backend/"),
        ("desktop/", "desktop/"),
        ("installer/", "installer/"),
        ("README.md", "README.md"),
        ("INSTALLATION.md", "INSTALLATION.md"),
        ("IMMEDIATE_DOWNLOAD.md", "IMMEDIATE_DOWNLOAD.md"),
        ("SECURITY.md", "SECURITY.md"),
        ("HYBRID_AI_GUIDE.md", "HYBRID_AI_GUIDE.md"),
        ("LICENSE", "LICENSE"),
        ("CONTRIBUTING.md", "CONTRIBUTING.md"),
        ("build_windows_installer.bat", "build_windows_installer.bat")
    ]
    
    for src, dst in files_to_copy:
        src_path = Path(src)
        dst_path = release_dir / dst
        
        if src_path.exists():
            if src_path.is_dir():
                # Copy directory, excluding cache and venv
                shutil.copytree(
                    src_path, 
                    dst_path,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'venv', '.env', 'data')
                )
            else:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
            print(f"✅ Copied {src}")
        else:
            print(f"⚠️  Skipped {src} (not found)")
    
    print("\n📋 Step 2: Creating setup instructions...")
    
    # Create comprehensive setup guide
    setup_guide = """# 🚀 InLegalDesk Setup Guide

## 📥 What You Downloaded
Complete InLegalDesk platform with Hybrid BERT+GPT AI architecture for Indian legal research.

## 🎯 Quick Start (Windows)

### Prerequisites:
- Python 3.8+ from https://python.org/downloads/
- Windows 10/11 (64-bit)
- 4GB+ RAM, 2GB+ free disk space

### Option 1: Run from Source (Recommended)
```cmd
REM 1. Open Command Prompt as Administrator
REM 2. Navigate to this extracted folder

REM 3. Setup Backend
cd backend
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.sample .env
REM IMPORTANT: Edit .env file and add your OpenAI API key for full features
python app.py

REM 4. Setup Desktop (NEW Command Prompt window)
cd desktop
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
xcopy /E /I ..\\backend server
python main.py
```

### Option 2: Build Windows Installer
```cmd
REM Run this to create a professional installer:
build_windows_installer.bat
REM Creates: installer\\output\\InLegalDesk_Installer.exe
```

## 🔑 Configure API Key
1. Launch the desktop app
2. Click "🔑 API Credentials"
3. Enter your OpenAI API key from https://platform.openai.com/api-keys
4. Set a master password
5. Test connection and save

## ✨ Features
- 🤖 Hybrid BERT+GPT AI (InLegalBERT + T5 + XLNet + OpenAI)
- ⚖️ Indian legal research (IPC, CrPC, Evidence Act)
- 💬 ChatGPT-style interface
- 🔒 Secure credential management
- 📄 OCR-free PDF processing
- 🌐 English + Hindi support

## 📞 Support
- Repository: https://github.com/ravidatanerd/LEGAL_BERT_IN
- Issues: https://github.com/ravidatanerd/LEGAL_BERT_IN/issues
- Documentation: See README.md and other guides

## ⚠️ Note
This is for research/educational use. Consult legal professionals for official advice.
"""
    
    with open(release_dir / "SETUP_GUIDE.md", "w") as f:
        f.write(setup_guide)
    
    print("✅ Created SETUP_GUIDE.md")
    
    print("\n📋 Step 3: Creating release ZIP...")
    
    # Create ZIP file
    zip_filename = "InLegalDesk-v1.0.3-Complete.zip"
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(release_dir):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'node_modules']]
            
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(release_dir)
                zipf.write(file_path, arc_path)
    
    # Get file size
    zip_size = Path(zip_filename).stat().st_size / (1024 * 1024)  # MB
    print(f"✅ Created {zip_filename} ({zip_size:.1f} MB)")
    
    print("\n📋 Step 4: Generating security checksum...")
    
    # Generate SHA256 checksum
    with open(zip_filename, 'rb') as f:
        content = f.read()
        sha256_hash = hashlib.sha256(content).hexdigest()
    
    checksum_file = f"{zip_filename}.sha256"
    with open(checksum_file, 'w') as f:
        f.write(f"{sha256_hash}  {zip_filename}\n")
    
    print(f"✅ Created checksum: {checksum_file}")
    print(f"   SHA256: {sha256_hash[:32]}...")
    
    # Cleanup
    shutil.rmtree(release_dir)
    
    print(f"\n🎉 IMMEDIATE RELEASE PACKAGE READY!")
    print("=" * 55)
    print(f"📦 File: {zip_filename}")
    print(f"🔐 Checksum: {checksum_file}")
    print(f"📊 Size: {zip_size:.1f} MB")
    print(f"\n🚀 How to Distribute:")
    print("1. Upload both files to GitHub Releases manually")
    print("2. Or share via cloud storage (Google Drive, etc.)")
    print("3. Include SETUP_GUIDE.md instructions")
    print("\n✅ Users can download and use immediately!")
    
    return True

if __name__ == "__main__":
    try:
        create_release_package()
    except Exception as e:
        print(f"\n❌ Error creating release package: {e}")
        exit(1)