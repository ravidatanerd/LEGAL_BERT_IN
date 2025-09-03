#!/usr/bin/env python3
"""
InLegalDesk Console Launcher
Simple console version that shows errors and waits for user input
Helps diagnose why the GUI .exe might be closing immediately
"""
import sys
import os
import subprocess
import traceback
from pathlib import Path
import time

def log(message):
    """Print message with timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def wait_for_user():
    """Wait for user input before closing"""
    print("\n" + "="*50)
    input("Press Enter to continue...")

def check_python():
    """Check Python version and compatibility"""
    log("🔍 CHECKING PYTHON VERSION...")
    log("=" * 30)
    
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    
    log(f"Python version: {version_str}")
    log(f"Python executable: {sys.executable}")
    log(f"Python path: {sys.path[0]}")
    
    if version_info.major == 3 and version_info.minor >= 7:
        log("✅ Python version is compatible")
        return True, "compatible"
    elif version_info.major == 3 and version_info.minor == 6:
        log("⚠️  Python 3.6 - limited compatibility")
        return True, "limited"
    else:
        log("❌ Python version incompatible")
        return False, "incompatible"

def check_pip():
    """Check pip availability and version"""
    log("\n🔍 CHECKING PIP...")
    log("=" * 20)
    
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            log(f"✅ Pip available: {result.stdout.strip()}")
            return True
        else:
            log(f"❌ Pip error: {result.stderr}")
            return False
    except Exception as e:
        log(f"❌ Pip check failed: {e}")
        return False

def check_files():
    """Check for required files"""
    log("\n🔍 CHECKING FILES...")
    log("=" * 20)
    
    cwd = Path.cwd()
    log(f"Working directory: {cwd}")
    
    required_files = {
        "backend": "Backend directory",
        "desktop": "Desktop directory", 
        "README.md": "Documentation",
        "backend/app.py": "Backend application",
        "desktop/main.py": "Desktop application"
    }
    
    missing_files = []
    for file_path, description in required_files.items():
        full_path = cwd / file_path
        if full_path.exists():
            log(f"✅ {description}: {file_path}")
        else:
            log(f"❌ Missing {description}: {file_path}")
            missing_files.append(file_path)
    
    return len(missing_files) == 0, missing_files

def check_packages():
    """Check Python packages"""
    log("\n🔍 CHECKING PYTHON PACKAGES...")
    log("=" * 30)
    
    packages = {
        "fastapi": "Web framework",
        "uvicorn": "ASGI server",
        "pydantic": "Data validation",
        "requests": "HTTP client",
        "numpy": "Numerical computing",
        "torch": "PyTorch (AI)",
        "transformers": "Transformers (AI)",
        "PySide6": "Desktop GUI",
        "PyMuPDF": "PDF processing",
        "opencv-python-headless": "Computer vision",
        "pytesseract": "OCR"
    }
    
    available = 0
    missing = []
    
    for package, description in packages.items():
        try:
            __import__(package.replace("-", "_"))
            log(f"✅ {description}: {package}")
            available += 1
        except ImportError:
            log(f"❌ {description}: {package}")
            missing.append(package)
    
    success_rate = (available / len(packages)) * 100
    log(f"\n📊 Package availability: {available}/{len(packages)} ({success_rate:.0f}%)")
    
    return success_rate, missing

def launch_backend():
    """Launch backend server"""
    log("\n🚀 LAUNCHING BACKEND...")
    log("=" * 25)
    
    try:
        backend_dir = Path.cwd() / "backend"
        app_file = backend_dir / "app.py"
        
        if not app_file.exists():
            log(f"❌ Backend app.py not found at: {app_file}")
            return False
        
        log(f"📂 Backend directory: {backend_dir}")
        log(f"📄 App file: {app_file}")
        
        # Try virtual environment first
        venv_python = backend_dir / "venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            log("✅ Using virtual environment")
            cmd = [str(venv_python), "app.py"]
        else:
            log("⚠️  No virtual environment, using system Python")
            cmd = [sys.executable, "app.py"]
        
        log(f"🔧 Command: {' '.join(cmd)}")
        log("🚀 Starting backend server...")
        
        # Launch backend
        process = subprocess.Popen(cmd, cwd=backend_dir)
        log(f"✅ Backend started with PID: {process.pid}")
        log("🌐 Backend should be available at: http://localhost:8877")
        
        return True
        
    except Exception as e:
        log(f"❌ Backend launch failed: {e}")
        log(f"📋 Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main console launcher"""
    try:
        print("🏛️ InLegalDesk Console Launcher")
        print("=" * 40)
        print("This version shows detailed error information")
        print("and doesn't close immediately like the .exe might")
        print()
        
        # Comprehensive system check
        python_ok, python_status = check_python()
        pip_ok = check_pip()
        files_ok, missing_files = check_files()
        package_rate, missing_packages = check_packages()
        
        # Summary
        log("\n📊 SYSTEM STATUS SUMMARY:")
        log("=" * 30)
        log(f"Python: {'✅' if python_ok else '❌'} ({python_status})")
        log(f"Pip: {'✅' if pip_ok else '❌'}")
        log(f"Files: {'✅' if files_ok else '❌'}")
        log(f"Packages: {package_rate:.0f}% available")
        
        if not python_ok:
            log("\n❌ PYTHON ISSUE DETECTED!")
            log("This is likely why the .exe closes immediately")
            log("Solution: Upgrade Python to 3.7+")
            wait_for_user()
            return
        
        if not pip_ok:
            log("\n❌ PIP ISSUE DETECTED!")
            log("This could cause the .exe to fail")
            log("Solution: Upgrade pip or reinstall Python")
            wait_for_user()
            return
        
        if not files_ok:
            log("\n❌ MISSING FILES DETECTED!")
            log("This is likely why the .exe closes immediately")
            log(f"Missing: {', '.join(missing_files)}")
            log("Solution: Re-download InLegalDesk or check extraction")
            wait_for_user()
            return
        
        if package_rate < 50:
            log("\n⚠️  MANY PACKAGES MISSING!")
            log("This could cause the .exe to fail on startup")
            log(f"Missing: {', '.join(missing_packages[:5])}")
            log("Solution: Install dependencies first")
            
            choice = input("\nInstall dependencies now? (y/N): ").lower()
            if choice == 'y':
                # Try to install dependencies
                log("🔧 Installing dependencies...")
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
                    subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages[:5])
                    log("✅ Basic dependencies installed")
                except Exception as e:
                    log(f"❌ Dependency installation failed: {e}")
            
            wait_for_user()
            return
        
        # If we get here, system looks good
        log("\n✅ SYSTEM APPEARS HEALTHY!")
        log("The .exe should work. If it's still closing immediately,")
        log("there might be a packaging issue with the .exe itself.")
        
        # Offer to launch components
        print("\n🚀 LAUNCH OPTIONS:")
        print("1. Launch Backend Server")
        print("2. Launch Desktop GUI (if PySide6 available)")
        print("3. Open Web Interface")
        print("4. Exit")
        
        while True:
            choice = input("\nChoose option (1-4): ").strip()
            
            if choice == "1":
                launch_backend()
                break
            elif choice == "2":
                try:
                    import PySide6
                    log("✅ PySide6 available - attempting desktop launch")
                    # Would launch desktop here
                    log("🖥️ Desktop launch would happen here")
                except ImportError:
                    log("❌ PySide6 not available - cannot launch desktop")
                break
            elif choice == "3":
                log("🌐 Opening web interface...")
                import webbrowser
                webbrowser.open("http://localhost:8877")
                break
            elif choice == "4":
                break
            else:
                print("Invalid choice. Please enter 1-4.")
        
        wait_for_user()
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        print("\nThis error explains why the .exe closes immediately!")
        wait_for_user()

if __name__ == "__main__":
    main()