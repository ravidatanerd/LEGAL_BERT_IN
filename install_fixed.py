#!/usr/bin/env python3
"""
Fixed installation script for InLegalDesk
Uses maximum available package versions based on user's environment
"""
import sys
import subprocess
import os
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def install_with_fallback(package_specs, pip_path):
    """Install packages with version fallback"""
    for package_spec in package_specs:
        print(f"📦 Installing {package_spec}...")
        
        # Try exact version first
        success, output = run_command(f'"{pip_path}" install "{package_spec}"')
        
        if success:
            print(f"✅ {package_spec} installed successfully")
            continue
        
        # If exact version fails, try without version constraint
        package_name = package_spec.split(">=")[0].split("==")[0].split("<=")[0]
        print(f"⚠️  Exact version failed, trying latest available {package_name}...")
        
        success, output = run_command(f'"{pip_path}" install "{package_name}"')
        
        if success:
            print(f"✅ {package_name} installed (latest available version)")
        else:
            print(f"❌ {package_name} failed: {output}")

def setup_backend():
    """Setup backend with version compatibility"""
    print("\n🔧 Setting up Backend...")
    
    os.chdir("backend")
    
    # Create virtual environment
    print("📋 Creating virtual environment...")
    success, output = run_command(f"{sys.executable} -m venv venv")
    if not success:
        print(f"❌ Virtual environment creation failed: {output}")
        return False
    
    # Get pip path
    if os.name == 'nt':
        pip_path = "venv\\Scripts\\pip.exe"
        python_path = "venv\\Scripts\\python.exe"
    else:
        pip_path = "venv/bin/pip"
        python_path = "venv/bin/python"
    
    # Upgrade pip
    print("📋 Upgrading pip...")
    run_command(f'"{pip_path}" install --upgrade pip')
    
    # Try minimal requirements first for maximum compatibility
    print("📦 Trying minimal requirements for maximum compatibility...")
    
    success, output = run_command(f'"{pip_path}" install -r requirements-minimal.txt')
    
    if success:
        print("✅ Minimal requirements installed successfully")
        
        # Try to install optional advanced packages
        advanced_packages = [
            "sentence-transformers>=2.0.0",
            "faiss-cpu>=1.6.0", 
            "protobuf>=3.15.0",
            "sentencepiece>=0.1.85"
        ]
        
        print("🔧 Installing advanced packages (optional)...")
        for package in advanced_packages:
            success, _ = run_command(f'"{pip_path}" install "{package}"')
            if success:
                print(f"✅ {package} installed")
            else:
                print(f"⚠️  {package} skipped (not available)")
        
    else:
        print("⚠️  Minimal requirements failed, trying individual packages...")
        
        # Fallback to individual essential packages
        essential_packages = [
            "fastapi>=0.60.0",
            "uvicorn>=0.12.0", 
            "pydantic>=1.7.0",
            "transformers<=4.18.0",
            "torch>=1.6.0",
            "numpy>=1.18.0",
            "PyMuPDF<=1.19.6",
            "Pillow>=7.0.0",
            "httpx>=0.18.0",
            "requests>=2.20.0",
            "python-dotenv>=0.10.0",
            "markdown>=3.0.0"
        ]
        
        print("📋 Installing essential packages individually...")
        install_with_fallback(essential_packages, pip_path)
    
    # Copy environment file
    if not Path(".env").exists() and Path(".env.sample").exists():
        if os.name == 'nt':
            run_command("copy .env.sample .env")
        else:
            run_command("cp .env.sample .env")
        print("✅ Created .env file")
    
    print("✅ Backend setup complete")
    return True

def setup_desktop():
    """Setup desktop with compatibility"""
    print("\n🖥️ Setting up Desktop...")
    
    os.chdir("../desktop")
    
    # Create virtual environment
    print("📋 Creating virtual environment...")
    success, output = run_command(f"{sys.executable} -m venv venv")
    if not success:
        print(f"❌ Virtual environment creation failed: {output}")
        return False
    
    # Get pip path
    if os.name == 'nt':
        pip_path = "venv\\Scripts\\pip.exe"
    else:
        pip_path = "venv/bin/pip"
    
    # Upgrade pip
    run_command(f'"{pip_path}" install --upgrade pip')
    
    # Desktop packages
    desktop_packages = [
        "PySide6>=6.2.0",
        "httpx>=0.20.0",
        "python-dotenv>=0.15.0",
        "markdown>=3.2.0",
        "requests>=2.25.0",
        "cryptography>=3.0.0"
    ]
    
    print("📦 Installing desktop packages...")
    install_with_fallback(desktop_packages, pip_path)
    
    # Copy backend files
    backend_src = Path("../backend")
    server_dst = Path("server")
    
    if backend_src.exists():
        if server_dst.exists():
            import shutil
            shutil.rmtree(server_dst)
        
        import shutil
        shutil.copytree(backend_src, server_dst, ignore=shutil.ignore_patterns('venv', '__pycache__', '.env'))
        print("✅ Backend files copied")
    
    print("✅ Desktop setup complete")
    return True

def main():
    """Main installation function"""
    print("🚀 InLegalDesk Fixed Installation")
    print("=" * 40)
    
    # Check Python version
    major, minor = sys.version_info[:2]
    print(f"🐍 Python {major}.{minor} detected")
    
    if major < 3 or (major == 3 and minor < 7):
        print("❌ Python 3.7+ required")
        print("🔧 Please update Python from https://python.org")
        return False
    
    if major == 3 and minor < 9:
        print("⚠️  Using compatibility mode for older Python")
    
    # Setup backend
    if not setup_backend():
        print("❌ Backend setup failed")
        return False
    
    # Setup desktop
    if not setup_desktop():
        print("❌ Desktop setup failed")
        return False
    
    print("\n🎉 INSTALLATION COMPLETED!")
    print("=" * 40)
    print("✅ Backend: Ready to run")
    print("✅ Desktop: Ready to launch")
    print("\n🚀 To start InLegalDesk:")
    
    if os.name == 'nt':
        print("1. Backend: cd backend && venv\\Scripts\\activate && python app.py")
        print("2. Desktop: cd desktop && venv\\Scripts\\activate && python main.py")
    else:
        print("1. Backend: cd backend && source venv/bin/activate && python app.py")
        print("2. Desktop: cd desktop && source venv/bin/activate && python main.py")
    
    print("\n🔑 Configure OpenAI API key in the desktop app for full features!")
    print("📖 See README.md for detailed usage instructions")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ Installation failed")
            input("Press Enter to exit...")
            sys.exit(1)
        else:
            print("\n✅ Installation successful!")
            input("Press Enter to exit...")
    except KeyboardInterrupt:
        print("\n⚠️  Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)