#!/usr/bin/env python3
"""
InLegalDesk Compatibility Setup Script
Automatically detects Python version and uses appropriate requirements
"""
import sys
import subprocess
import os
from pathlib import Path

def get_python_version():
    """Get Python version info"""
    version = sys.version_info
    return version.major, version.minor

def check_python_compatibility():
    """Check if Python version is compatible"""
    major, minor = get_python_version()
    
    print(f"🐍 Detected Python {major}.{minor}")
    
    if major < 3:
        print("❌ Python 2 is not supported")
        print("🔧 Please install Python 3.8+ from https://python.org")
        return False, "unsupported"
    
    if major == 3 and minor < 7:
        print("❌ Python 3.6 and older are not supported")
        print("🔧 Please install Python 3.8+ from https://python.org")
        return False, "too_old"
    
    if major == 3 and minor == 7:
        print("⚠️  Python 3.7 detected - using compatibility mode")
        return True, "python37"
    
    if major == 3 and minor == 8:
        print("⚠️  Python 3.8 detected - using compatibility mode")
        return True, "python38"
    
    if major == 3 and minor >= 9:
        print("✅ Python 3.9+ detected - using standard requirements")
        return True, "modern"
    
    print("✅ Python version compatible")
    return True, "modern"

def setup_backend():
    """Setup backend with appropriate requirements"""
    print("\n📋 Setting up Backend...")
    
    os.chdir("backend")
    
    # Check Python compatibility
    compatible, version_type = check_python_compatibility()
    
    if not compatible:
        return False
    
    # Select appropriate requirements file
    if version_type in ["python37", "python38"]:
        requirements_file = "requirements-python37.txt"
        print(f"📦 Using compatibility requirements: {requirements_file}")
    else:
        requirements_file = "requirements.txt"
        print(f"📦 Using standard requirements: {requirements_file}")
    
    try:
        # Create virtual environment
        print("🔧 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        
        # Activate and install
        if os.name == 'nt':  # Windows
            pip_path = "venv\\Scripts\\pip.exe"
            python_path = "venv\\Scripts\\python.exe"
        else:  # Linux/Mac
            pip_path = "venv/bin/pip"
            python_path = "venv/bin/python"
        
        print("📦 Installing dependencies...")
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        subprocess.run([pip_path, "install", "-r", requirements_file], check=True)
        
        # Copy environment file
        if not Path(".env").exists():
            if Path(".env.sample").exists():
                subprocess.run(["copy" if os.name == 'nt' else "cp", ".env.sample", ".env"], shell=True)
                print("✅ Created .env file from sample")
        
        print("✅ Backend setup complete")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Backend setup failed: {e}")
        return False

def setup_desktop():
    """Setup desktop with appropriate requirements"""
    print("\n📋 Setting up Desktop...")
    
    os.chdir("../desktop")
    
    # Check Python compatibility
    compatible, version_type = check_python_compatibility()
    
    if not compatible:
        return False
    
    # Select appropriate requirements file
    if version_type in ["python37", "python38"]:
        requirements_file = "requirements-python37.txt"
        print(f"📦 Using compatibility requirements: {requirements_file}")
    else:
        requirements_file = "requirements.txt"
        print(f"📦 Using standard requirements: {requirements_file}")
    
    try:
        # Create virtual environment
        print("🔧 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        
        # Activate and install
        if os.name == 'nt':  # Windows
            pip_path = "venv\\Scripts\\pip.exe"
        else:  # Linux/Mac
            pip_path = "venv/bin/pip"
        
        print("📦 Installing dependencies...")
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        subprocess.run([pip_path, "install", "-r", requirements_file], check=True)
        
        # Copy backend files
        backend_src = Path("../backend")
        server_dst = Path("server")
        
        if backend_src.exists():
            if server_dst.exists():
                import shutil
                shutil.rmtree(server_dst)
            
            import shutil
            shutil.copytree(backend_src, server_dst, ignore=shutil.ignore_patterns('venv', '__pycache__', '.env'))
            print("✅ Backend files copied to desktop/server")
        
        print("✅ Desktop setup complete")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Desktop setup failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 InLegalDesk Compatibility Setup")
    print("=" * 40)
    
    major, minor = get_python_version()
    
    # Strong recommendation for modern Python
    if major == 3 and minor < 9:
        print(f"\n🔔 RECOMMENDATION:")
        print(f"For the best experience, consider updating to Python 3.11+")
        print(f"Download from: https://python.org/downloads/")
        print(f"Current: Python {major}.{minor} (will use compatibility mode)")
        
        response = input("\nContinue with compatibility mode? (y/n): ")
        if response.lower() != 'y':
            print("🔧 Please update Python and run setup again")
            return False
    
    # Setup backend
    success_backend = setup_backend()
    
    if not success_backend:
        print("\n❌ Backend setup failed")
        return False
    
    # Setup desktop
    success_desktop = setup_desktop()
    
    if not success_desktop:
        print("\n❌ Desktop setup failed")
        return False
    
    print("\n🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 40)
    print("✅ Backend: Ready to run")
    print("✅ Desktop: Ready to launch")
    print("\n🚀 To start InLegalDesk:")
    print("1. Backend: cd backend && venv\\Scripts\\activate && python app.py")
    print("2. Desktop: cd desktop && venv\\Scripts\\activate && python main.py")
    print("\n🔑 Don't forget to configure your OpenAI API key!")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ Setup failed. Please check errors above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        sys.exit(1)