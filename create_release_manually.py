#!/usr/bin/env python3
"""
Manual release creation for InLegalDesk
Use this if GitHub Actions fails
"""
import os
import shutil
import zipfile
import sys
from pathlib import Path

def create_manual_release():
    """Create a manual release package"""
    print("📦 Creating Manual InLegalDesk Release Package")
    print("=" * 50)
    
    # Create release directory
    release_dir = Path("release")
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()
    
    print("📋 Step 1: Copying source files...")
    
    # Copy essential files
    essential_files = [
        "backend/",
        "desktop/", 
        "installer/",
        "README.md",
        "INSTALLATION.md",
        "SECURITY.md",
        "HYBRID_AI_GUIDE.md",
        "LICENSE",
        "CONTRIBUTING.md",
        "build_windows_installer.bat"
    ]
    
    for item in essential_files:
        src = Path(item)
        if src.exists():
            if src.is_dir():
                shutil.copytree(src, release_dir / src.name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'venv', '.env'))
            else:
                shutil.copy2(src, release_dir / src.name)
            print(f"✅ Copied {item}")
        else:
            print(f"⚠️  Skipped {item} (not found)")
    
    print("\n📋 Step 2: Creating user-friendly structure...")
    
    # Create user instructions
    instructions = """# InLegalDesk v1.0.1 - AI-Powered Indian Legal Research

## 🚀 Quick Start (Windows)

### Option 1: Build Installer (Recommended)
1. Ensure you have Python 3.8+ and Inno Setup 6 installed
2. Double-click: build_windows_installer.bat
3. Wait for build to complete
4. Run: installer\\output\\InLegalDesk_Installer.exe

### Option 2: Run from Source
1. Install Python 3.8+ from python.org
2. Open Command Prompt as Administrator
3. Navigate to this folder
4. Run setup commands:

```cmd
REM Setup backend
cd backend
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.sample .env
REM Edit .env file and add your OpenAI API key
python app.py
```

```cmd
REM Setup desktop (new Command Prompt)
cd desktop
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
xcopy /E /I ..\\backend server
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
"""
    
    with open(release_dir / "START_HERE.md", "w") as f:
        f.write(instructions)
    
    print("✅ Created START_HERE.md with user instructions")
    
    print("\n📋 Step 3: Creating release ZIP...")
    
    # Create ZIP file
    zip_path = "InLegalDesk-v1.0.1-Source.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(release_dir):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv']]
            
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(release_dir)
                zipf.write(file_path, arc_path)
    
    # Get file size
    zip_size = Path(zip_path).stat().st_size / (1024 * 1024)  # MB
    
    print(f"✅ Created {zip_path} ({zip_size:.1f} MB)")
    
    print("\n📋 Step 4: Creating verification info...")
    
    # Create checksum
    import hashlib
    with open(zip_path, 'rb') as f:
        content = f.read()
        sha256_hash = hashlib.sha256(content).hexdigest()
    
    with open(f"{zip_path}.sha256", "w") as f:
        f.write(f"{sha256_hash}  {zip_path}\n")
    
    print(f"✅ Created SHA256 checksum: {sha256_hash[:16]}...")
    
    print("\n🎉 MANUAL RELEASE PACKAGE CREATED!")
    print("=" * 50)
    print(f"📦 Release File: {zip_path}")
    print(f"🔐 Checksum: {zip_path}.sha256")
    print(f"📊 Size: {zip_size:.1f} MB")
    print("\n🚀 Upload to GitHub:")
    print("1. Go to: https://github.com/ravidatanerd/LEGAL_BERT_IN/releases")
    print("2. Click 'Create a new release'")
    print("3. Tag: v1.0.1")
    print("4. Upload: " + zip_path)
    print("5. Upload: " + zip_path + ".sha256")
    print("6. Publish release")
    
    return True

if __name__ == "__main__":
    try:
        success = create_manual_release()
        if success:
            print("\n✅ Manual release package ready for upload!")
        else:
            print("\n❌ Manual release creation failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error creating manual release: {e}")
        sys.exit(1)