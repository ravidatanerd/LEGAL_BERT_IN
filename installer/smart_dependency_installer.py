#!/usr/bin/env python3
"""
InLegalDesk Smart Dependency Installer
Automatically detects and installs all required dependencies from the web
Handles Python version upgrades, pip upgrades, and package installation
"""
import sys
import os
import subprocess
import urllib.request
import urllib.error
import platform
import json
import tempfile
import zipfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class DependencyInstaller:
    """Smart dependency installer with web downloads"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.install_log = []
        self.errors = []
        
    def log(self, message: str, is_error: bool = False):
        """Log installation progress"""
        print(message)
        self.install_log.append(message)
        if is_error:
            self.errors.append(message)
    
    def check_python_version(self) -> Tuple[bool, str, str]:
        """Check if Python version is compatible"""
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        if version.major == 3 and version.minor >= 9:
            return True, version_str, "optimal"
        elif version.major == 3 and version.minor >= 7:
            return True, version_str, "good"
        elif version.major == 3 and version.minor >= 6:
            return False, version_str, "old"
        else:
            return False, version_str, "incompatible"
    
    def download_file(self, url: str, filename: str) -> bool:
        """Download file from URL with progress"""
        try:
            self.log(f"📥 Downloading {filename}...")
            
            def progress_hook(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(100, (block_num * block_size * 100) // total_size)
                    if percent % 10 == 0:  # Show every 10%
                        print(f"   Progress: {percent}%")
            
            file_path = self.temp_dir / filename
            urllib.request.urlretrieve(url, file_path, progress_hook)
            self.log(f"✅ Downloaded {filename}")
            return True
            
        except urllib.error.URLError as e:
            self.log(f"❌ Download failed: {e}", True)
            return False
    
    def install_python_39(self) -> bool:
        """Download and install Python 3.9.13"""
        self.log("🐍 INSTALLING PYTHON 3.9.13...")
        self.log("=" * 40)
        
        # Download Python installer
        python_url = "https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe"
        if not self.download_file(python_url, "python-3.9.13-amd64.exe"):
            return False
        
        # Install Python
        installer_path = self.temp_dir / "python-3.9.13-amd64.exe"
        self.log("🔧 Installing Python 3.9.13...")
        
        try:
            # Silent installation with optimal settings
            result = subprocess.run([
                str(installer_path),
                "/quiet",
                "InstallAllUsers=1",
                "PrependPath=1",
                "Include_pip=1",
                "Include_test=0",
                "Include_doc=0"
            ], timeout=300)
            
            if result.returncode == 0:
                self.log("✅ Python 3.9.13 installed successfully")
                return True
            else:
                self.log(f"❌ Python installation failed (exit code: {result.returncode})", True)
                return False
                
        except subprocess.TimeoutExpired:
            self.log("❌ Python installation timed out", True)
            return False
        except Exception as e:
            self.log(f"❌ Python installation error: {e}", True)
            return False
    
    def upgrade_pip(self) -> bool:
        """Upgrade pip to latest version"""
        self.log("📦 UPGRADING PIP TO LATEST VERSION...")
        self.log("=" * 40)
        
        # Method 1: Standard upgrade
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", "pip"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                self.log("✅ Pip upgraded successfully")
                return True
            else:
                self.log(f"⚠️  Standard pip upgrade failed: {result.stderr}")
        except Exception as e:
            self.log(f"⚠️  Standard pip upgrade error: {e}")
        
        # Method 2: Using get-pip.py
        self.log("🔧 Trying alternative pip upgrade method...")
        try:
            get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
            if self.download_file(get_pip_url, "get-pip.py"):
                get_pip_path = self.temp_dir / "get-pip.py"
                result = subprocess.run([
                    sys.executable, str(get_pip_path)
                ], timeout=120)
                
                if result.returncode == 0:
                    self.log("✅ Pip upgraded using get-pip.py")
                    return True
        except Exception as e:
            self.log(f"❌ get-pip.py method failed: {e}", True)
        
        # Method 3: ensurepip
        self.log("🔧 Trying ensurepip method...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "ensurepip", "--upgrade"
            ], timeout=60)
            
            if result.returncode == 0:
                self.log("✅ Pip upgraded using ensurepip")
                return True
        except Exception as e:
            self.log(f"⚠️  ensurepip method failed: {e}")
        
        self.log("⚠️  All pip upgrade methods failed - continuing with current version")
        return False
    
    def install_package(self, package: str, fallback_version: Optional[str] = None) -> bool:
        """Install a package with fallback options"""
        self.log(f"📦 Installing {package}...")
        
        # Try main package first
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log(f"✅ {package} installed successfully")
                return True
            else:
                self.log(f"⚠️  {package} installation failed: {result.stderr}")
        except Exception as e:
            self.log(f"⚠️  {package} installation error: {e}")
        
        # Try fallback version if provided
        if fallback_version:
            self.log(f"🔧 Trying fallback version: {fallback_version}")
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", f"{package}{fallback_version}"
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    self.log(f"✅ {package} (fallback) installed successfully")
                    return True
            except Exception as e:
                self.log(f"❌ {package} fallback failed: {e}")
        
        self.log(f"❌ Failed to install {package}", True)
        return False
    
    def install_essential_packages(self) -> Dict[str, bool]:
        """Install essential packages with smart fallbacks"""
        self.log("🚀 INSTALLING ESSENTIAL PACKAGES...")
        self.log("=" * 40)
        
        # Check Python version for compatibility
        is_compatible, version, quality = self.check_python_version()
        
        packages = {
            # Core build tools (always needed)
            "wheel": {"package": "wheel", "fallback": None},
            "setuptools": {"package": "setuptools", "fallback": None},
            
            # Web framework
            "fastapi": {
                "package": "fastapi", 
                "fallback": ">=0.65.0,<0.75.0" if quality == "old" else None
            },
            "uvicorn": {
                "package": "uvicorn[standard]", 
                "fallback": ">=0.13.0,<0.16.0" if quality == "old" else None
            },
            "pydantic": {
                "package": "pydantic", 
                "fallback": ">=1.8.0,<1.9.0" if quality == "old" else None
            },
            
            # Essential libraries
            "numpy": {
                "package": "numpy", 
                "fallback": ">=1.19.0,<1.20.0" if quality == "old" else None
            },
            "requests": {"package": "requests", "fallback": None},
            "python-dotenv": {"package": "python-dotenv", "fallback": None},
            
            # AI libraries (version-aware)
            "torch": {
                "package": "torch",
                "fallback": ">=1.7.0,<1.11.0" if quality == "old" else None
            },
            "transformers": {
                "package": "transformers",
                "fallback": ">=4.12.0,<=4.18.0" if quality == "old" else None
            },
            
            # Document processing
            "PyMuPDF": {
                "package": "PyMuPDF",
                "fallback": ">=1.16.0,<=1.19.6" if quality == "old" else None
            },
            "Pillow": {"package": "Pillow", "fallback": None},
            "opencv-python-headless": {"package": "opencv-python-headless", "fallback": None},
            
            # Desktop GUI (only for compatible Python)
            "PySide6": {
                "package": "PySide6",
                "fallback": None
            } if quality != "old" else None,
            
            # Optional packages
            "sentence-transformers": {"package": "sentence-transformers", "fallback": None},
            "pytesseract": {"package": "pytesseract", "fallback": None},
            "faiss-cpu": {"package": "faiss-cpu", "fallback": None},
            "cryptography": {"package": "cryptography", "fallback": None},
        }
        
        # Remove None entries
        packages = {k: v for k, v in packages.items() if v is not None}
        
        results = {}
        for name, info in packages.items():
            success = self.install_package(info["package"], info["fallback"])
            results[name] = success
        
        return results
    
    def create_launcher_script(self, install_dir: Path):
        """Create launcher script for the application"""
        launcher_content = f'''
import sys
import os
import subprocess
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

def launch_backend():
    """Launch the backend server"""
    backend_dir = Path("{install_dir}") / "backend"
    if backend_dir.exists():
        os.chdir(backend_dir)
        if (backend_dir / "venv" / "Scripts" / "activate.bat").exists():
            subprocess.Popen(["cmd", "/c", "venv\\\\Scripts\\\\activate.bat && python app.py"])
        else:
            subprocess.Popen([sys.executable, "app.py"])
        return True
    return False

def launch_desktop():
    """Launch the desktop GUI"""
    desktop_dir = Path("{install_dir}") / "desktop"
    if desktop_dir.exists():
        os.chdir(desktop_dir)
        if (desktop_dir / "venv" / "Scripts" / "activate.bat").exists():
            subprocess.Popen(["cmd", "/c", "venv\\\\Scripts\\\\activate.bat && python main.py"])
        else:
            subprocess.Popen([sys.executable, "main.py"])
        return True
    return False

def main():
    root = tk.Tk()
    root.title("InLegalDesk Launcher")
    root.geometry("400x300")
    
    tk.Label(root, text="🏛️ InLegalDesk", font=("Arial", 20, "bold")).pack(pady=20)
    tk.Label(root, text="Indian Legal Research Platform", font=("Arial", 12)).pack(pady=5)
    
    tk.Button(root, text="🚀 Launch Backend Server", command=launch_backend, 
              font=("Arial", 12), width=25, height=2).pack(pady=10)
    
    tk.Button(root, text="🖥️ Launch Desktop GUI", command=launch_desktop,
              font=("Arial", 12), width=25, height=2).pack(pady=10)
    
    tk.Label(root, text="Web Interface: http://localhost:8877", 
             font=("Arial", 10), fg="blue").pack(pady=20)
    
    root.mainloop()

if __name__ == "__main__":
    main()
'''
        
        launcher_path = install_dir / "InLegalDesk_Launcher.py"
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)
        
        return launcher_path
    
    def run_installation(self, install_dir: str = None) -> bool:
        """Run complete installation process"""
        self.log("🚀 INLEGALDESK SMART DEPENDENCY INSTALLER")
        self.log("=" * 50)
        self.log("")
        
        # Step 1: Check Python version
        is_compatible, version, quality = self.check_python_version()
        self.log(f"📊 Current Python: {version} ({quality})")
        
        if not is_compatible and quality == "old":
            self.log("⚠️  Python 3.6 detected - some packages may have issues")
            self.log("💡 Consider upgrading to Python 3.7+ for best results")
        elif not is_compatible:
            self.log("❌ Python version incompatible - upgrade required")
            return False
        
        # Step 2: Upgrade pip
        self.log("")
        pip_success = self.upgrade_pip()
        if not pip_success:
            self.log("⚠️  Pip upgrade had issues - continuing anyway")
        
        # Step 3: Install packages
        self.log("")
        results = self.install_essential_packages()
        
        # Step 4: Create launcher
        if install_dir:
            install_path = Path(install_dir)
            self.create_launcher_script(install_path)
            self.log(f"✅ Launcher created at {install_path}")
        
        # Step 5: Summary
        self.log("")
        self.log("📊 INSTALLATION SUMMARY")
        self.log("=" * 25)
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        success_rate = (successful / total) * 100 if total > 0 else 0
        
        self.log(f"✅ Successful: {successful}/{total} packages ({success_rate:.0f}%)")
        
        if self.errors:
            self.log(f"❌ Errors: {len(self.errors)}")
            for error in self.errors[-3:]:  # Show last 3 errors
                self.log(f"   • {error}")
        
        # Recommendations
        self.log("")
        self.log("🎯 RECOMMENDATIONS:")
        
        if success_rate >= 90:
            self.log("🎉 Excellent! InLegalDesk should work perfectly")
        elif success_rate >= 75:
            self.log("✅ Good! Most features will work")
        else:
            self.log("⚠️  Some issues detected - check manual installers")
        
        if not results.get("PySide6", False):
            self.log("💡 Desktop GUI unavailable - use web interface at http://localhost:8877")
        
        if not results.get("transformers", False):
            self.log("💡 AI features limited - configure OpenAI API key for backup")
        
        return success_rate >= 70
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            self.log(f"⚠️  Cleanup warning: {e}")

def main():
    """Main installation function"""
    installer = DependencyInstaller()
    
    try:
        # Get installation directory
        install_dir = os.getenv("INSTALL_DIR", os.getcwd())
        
        # Run installation
        success = installer.run_installation(install_dir)
        
        if success:
            print("\n🎉 InLegalDesk installation completed!")
            print("🚀 You can now use the platform:")
            print("   • Desktop: Run InLegalDesk_Launcher.py")
            print("   • Web: Visit http://localhost:8877")
        else:
            print("\n❌ Installation had significant issues")
            print("💡 Try manual installation scripts as backup")
        
        # Save installation log
        log_file = Path(install_dir) / "installation_log.txt"
        with open(log_file, 'w') as f:
            f.write('\n'.join(installer.install_log))
        print(f"\n📋 Installation log saved to: {log_file}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Installation cancelled by user")
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
    finally:
        installer.cleanup()

if __name__ == "__main__":
    main()