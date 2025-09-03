#!/usr/bin/env python3
"""
InLegalDesk Debug Launcher
Shows detailed error messages and doesn't close immediately
Helps diagnose why the .exe might be closing quickly
"""
import sys
import os
import subprocess
import traceback
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from pathlib import Path
import threading
import webbrowser
import time

class DebugLauncher:
    """Debug launcher with detailed error reporting"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("InLegalDesk Debug Launcher")
        self.root.geometry("700x600")
        
        # Prevent window from closing immediately
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.log_text = None
        self.setup_ui()
        self.log("🚀 InLegalDesk Debug Launcher Started")
        self.log(f"📊 Python: {sys.version}")
        self.log(f"📂 Working Directory: {os.getcwd()}")
        
        # Start system check
        self.check_system()
        
    def setup_ui(self):
        """Setup the debug UI"""
        # Header
        header_frame = tk.Frame(self.root, bg="#007acc", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🔧 InLegalDesk Debug Launcher", 
                font=("Arial", 16, "bold"), bg="#007acc", fg="white").pack(pady=15)
        
        # Main content
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Log area
        log_frame = tk.LabelFrame(main_frame, text="System Check Log", font=("Arial", 10, "bold"))
        log_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Buttons frame
        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(fill="x")
        
        tk.Button(buttons_frame, text="🔍 Recheck System", command=self.check_system,
                 font=("Arial", 10), bg="#17a2b8", fg="white").pack(side="left", padx=5)
        
        tk.Button(buttons_frame, text="🚀 Launch Backend", command=self.launch_backend,
                 font=("Arial", 10), bg="#007acc", fg="white").pack(side="left", padx=5)
        
        tk.Button(buttons_frame, text="🖥️ Launch Desktop", command=self.launch_desktop,
                 font=("Arial", 10), bg="#28a745", fg="white").pack(side="left", padx=5)
        
        tk.Button(buttons_frame, text="🌐 Open Web", command=self.open_web,
                 font=("Arial", 10), bg="#6f42c1", fg="white").pack(side="left", padx=5)
        
        tk.Button(buttons_frame, text="🔧 Install Deps", command=self.install_dependencies,
                 font=("Arial", 10), bg="#ffc107", fg="black").pack(side="left", padx=5)
        
        # Status frame
        status_frame = tk.Frame(main_frame)
        status_frame.pack(fill="x", pady=(10, 0))
        
        self.status_label = tk.Label(status_frame, text="Starting system check...", 
                                   font=("Arial", 9), fg="#666")
        self.status_label.pack()
        
    def log(self, message: str):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        if self.log_text:
            self.log_text.insert(tk.END, log_message)
            self.log_text.see(tk.END)
            self.root.update()
        
        print(message)  # Also print to console
    
    def check_system(self):
        """Comprehensive system check"""
        def check():
            try:
                self.log("🔍 STARTING COMPREHENSIVE SYSTEM CHECK")
                self.log("=" * 50)
                
                # Check Python version
                self.log(f"🐍 Python Version: {sys.version}")
                version_info = sys.version_info
                if version_info.major == 3 and version_info.minor >= 7:
                    self.log("✅ Python version compatible")
                elif version_info.major == 3 and version_info.minor == 6:
                    self.log("⚠️  Python 3.6 - limited compatibility")
                else:
                    self.log("❌ Python version incompatible")
                
                # Check pip
                try:
                    result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        self.log(f"✅ Pip: {result.stdout.strip()}")
                    else:
                        self.log(f"❌ Pip check failed: {result.stderr}")
                except Exception as e:
                    self.log(f"❌ Pip error: {e}")
                
                # Check working directory
                cwd = Path.cwd()
                self.log(f"📂 Working Directory: {cwd}")
                
                # Check for key files
                key_files = ["backend", "desktop", "README.md", "requirements.txt"]
                for file_name in key_files:
                    file_path = cwd / file_name
                    if file_path.exists():
                        self.log(f"✅ Found: {file_name}")
                    else:
                        self.log(f"❌ Missing: {file_name}")
                
                # Check for backend files
                backend_dir = cwd / "backend"
                if backend_dir.exists():
                    backend_files = ["app.py", "requirements.txt", ".env.sample"]
                    for file_name in backend_files:
                        file_path = backend_dir / file_name
                        if file_path.exists():
                            self.log(f"✅ Backend: {file_name}")
                        else:
                            self.log(f"❌ Backend missing: {file_name}")
                
                # Check for desktop files
                desktop_dir = cwd / "desktop"
                if desktop_dir.exists():
                    desktop_files = ["main.py", "api_client.py"]
                    for file_name in desktop_files:
                        file_path = desktop_dir / file_name
                        if file_path.exists():
                            self.log(f"✅ Desktop: {file_name}")
                        else:
                            self.log(f"❌ Desktop missing: {file_name}")
                
                # Check Python packages
                self.log("\n🔍 CHECKING PYTHON PACKAGES:")
                self.log("-" * 30)
                
                critical_packages = [
                    "fastapi", "uvicorn", "pydantic", "requests", 
                    "numpy", "torch", "transformers", "PySide6",
                    "PyMuPDF", "opencv-python-headless", "pytesseract"
                ]
                
                missing_packages = []
                for package in critical_packages:
                    try:
                        __import__(package.replace("-", "_"))
                        self.log(f"✅ {package}")
                    except ImportError:
                        self.log(f"❌ {package} - not installed")
                        missing_packages.append(package)
                
                # Summary
                self.log("\n📊 SYSTEM CHECK SUMMARY:")
                self.log("-" * 25)
                
                if not missing_packages:
                    self.log("🎉 All packages available - ready to launch!")
                    self.status_label.config(text="✅ System ready - all dependencies available")
                else:
                    self.log(f"⚠️  Missing packages: {', '.join(missing_packages[:5])}")
                    self.status_label.config(text=f"⚠️  Missing {len(missing_packages)} packages")
                
                # Check virtual environments
                backend_venv = cwd / "backend" / "venv"
                desktop_venv = cwd / "desktop" / "venv"
                
                if backend_venv.exists():
                    self.log("✅ Backend virtual environment found")
                else:
                    self.log("❌ Backend virtual environment missing")
                
                if desktop_venv.exists():
                    self.log("✅ Desktop virtual environment found")
                else:
                    self.log("❌ Desktop virtual environment missing")
                
                self.log("\n🎯 RECOMMENDATIONS:")
                self.log("-" * 20)
                
                if missing_packages:
                    self.log("🔧 Click 'Install Deps' to install missing packages")
                
                if version_info.major == 3 and version_info.minor < 7:
                    self.log("🔄 Consider upgrading Python to 3.7+ for full compatibility")
                
                self.log("📋 Check log above for any errors or missing components")
                
            except Exception as e:
                self.log(f"❌ System check failed: {e}")
                self.log(f"📋 Traceback: {traceback.format_exc()}")
        
        # Run check in background thread
        threading.Thread(target=check, daemon=True).start()
    
    def launch_backend(self):
        """Launch backend with error handling"""
        try:
            self.log("🚀 Launching backend server...")
            
            backend_dir = Path.cwd() / "backend"
            if not backend_dir.exists():
                self.log("❌ Backend directory not found!")
                messagebox.showerror("Error", f"Backend directory not found at: {backend_dir}")
                return
            
            # Check for app.py
            app_file = backend_dir / "app.py"
            if not app_file.exists():
                self.log("❌ Backend app.py not found!")
                messagebox.showerror("Error", f"app.py not found at: {app_file}")
                return
            
            # Try to launch with virtual environment first
            venv_python = backend_dir / "venv" / "Scripts" / "python.exe"
            if venv_python.exists():
                self.log("✅ Using virtual environment")
                cmd = [str(venv_python), "app.py"]
                cwd = backend_dir
            else:
                self.log("⚠️  No virtual environment, using system Python")
                cmd = [sys.executable, "app.py"]
                cwd = backend_dir
            
            # Launch backend
            process = subprocess.Popen(cmd, cwd=cwd, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            
            self.log(f"✅ Backend launched with PID: {process.pid}")
            self.log("🌐 Backend should be available at: http://localhost:8877")
            
            # Check if process is still running after a moment
            time.sleep(2)
            if process.poll() is None:
                self.log("✅ Backend server is running")
                messagebox.showinfo("Success", "Backend server started successfully!\n\nAccess at: http://localhost:8877")
            else:
                stdout, stderr = process.communicate()
                self.log(f"❌ Backend exited immediately")
                self.log(f"📋 Stdout: {stdout}")
                self.log(f"📋 Stderr: {stderr}")
                messagebox.showerror("Error", f"Backend failed to start:\n{stderr}")
                
        except Exception as e:
            error_msg = f"Failed to launch backend: {e}"
            self.log(f"❌ {error_msg}")
            self.log(f"📋 Traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", error_msg)
    
    def launch_desktop(self):
        """Launch desktop GUI with error handling"""
        try:
            self.log("🖥️ Launching desktop GUI...")
            
            desktop_dir = Path.cwd() / "desktop"
            if not desktop_dir.exists():
                self.log("❌ Desktop directory not found!")
                messagebox.showerror("Error", f"Desktop directory not found at: {desktop_dir}")
                return
            
            # Check for main.py
            main_file = desktop_dir / "main.py"
            if not main_file.exists():
                self.log("❌ Desktop main.py not found!")
                messagebox.showerror("Error", f"main.py not found at: {main_file}")
                return
            
            # Check for PySide6
            try:
                import PySide6
                self.log("✅ PySide6 available")
            except ImportError:
                self.log("❌ PySide6 not available")
                messagebox.showerror("Error", "PySide6 not installed! Desktop GUI cannot run.\n\nUse web interface instead or install dependencies.")
                return
            
            # Try to launch with virtual environment first
            venv_python = desktop_dir / "venv" / "Scripts" / "python.exe"
            if venv_python.exists():
                self.log("✅ Using desktop virtual environment")
                cmd = [str(venv_python), "main.py"]
                cwd = desktop_dir
            else:
                self.log("⚠️  No virtual environment, using system Python")
                cmd = [sys.executable, "main.py"]
                cwd = desktop_dir
            
            # Launch desktop
            process = subprocess.Popen(cmd, cwd=cwd,
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            
            self.log(f"✅ Desktop launched with PID: {process.pid}")
            
            # Check if process is still running
            time.sleep(2)
            if process.poll() is None:
                self.log("✅ Desktop GUI is running")
                messagebox.showinfo("Success", "Desktop GUI started successfully!")
            else:
                stdout, stderr = process.communicate()
                self.log(f"❌ Desktop exited immediately")
                self.log(f"📋 Stdout: {stdout}")
                self.log(f"📋 Stderr: {stderr}")
                messagebox.showerror("Error", f"Desktop failed to start:\n{stderr}")
                
        except Exception as e:
            error_msg = f"Failed to launch desktop: {e}"
            self.log(f"❌ {error_msg}")
            self.log(f"📋 Traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", error_msg)
    
    def open_web(self):
        """Open web interface"""
        try:
            self.log("🌐 Opening web interface...")
            webbrowser.open("http://localhost:8877")
            self.log("✅ Web browser opened")
            messagebox.showinfo("Web Interface", 
                               "Web interface opened in browser.\n\n" +
                               "URL: http://localhost:8877\n\n" +
                               "Note: Make sure backend server is running first!")
        except Exception as e:
            error_msg = f"Failed to open web interface: {e}"
            self.log(f"❌ {error_msg}")
            messagebox.showerror("Error", error_msg)
    
    def install_dependencies(self):
        """Install dependencies with detailed logging"""
        try:
            self.log("🔧 Starting dependency installation...")
            
            # Check for installers
            installers = [
                "smart_dependency_installer.py",
                "ULTIMATE_AI_FIX.bat",
                "AUTO_PYTHON_UPGRADE.bat",
                "UPGRADE_PIP_FIRST.bat"
            ]
            
            available_installers = []
            for installer in installers:
                if Path(installer).exists():
                    available_installers.append(installer)
                    self.log(f"✅ Found installer: {installer}")
                else:
                    self.log(f"❌ Missing installer: {installer}")
            
            if not available_installers:
                self.log("❌ No installers found!")
                messagebox.showerror("Error", "No dependency installers found!")
                return
            
            # Use the first available installer
            installer = available_installers[0]
            self.log(f"🚀 Using installer: {installer}")
            
            if installer.endswith(".py"):
                subprocess.Popen([sys.executable, installer])
            else:
                subprocess.Popen(["cmd", "/c", installer])
            
            self.log("✅ Dependency installer started")
            messagebox.showinfo("Success", f"Dependency installer started: {installer}")
            
        except Exception as e:
            error_msg = f"Failed to start dependency installer: {e}"
            self.log(f"❌ {error_msg}")
            self.log(f"📋 Traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", error_msg)
    
    def check_system(self):
        """Check system status"""
        def check():
            try:
                self.status_label.config(text="🔍 Checking system...")
                
                # Check Python
                self.log(f"🐍 Python executable: {sys.executable}")
                self.log(f"🐍 Python version: {sys.version}")
                
                # Check current directory and files
                cwd = Path.cwd()
                self.log(f"📂 Current directory: {cwd}")
                
                # List directory contents
                self.log("📋 Directory contents:")
                try:
                    for item in cwd.iterdir():
                        if item.is_dir():
                            self.log(f"   📁 {item.name}/")
                        else:
                            self.log(f"   📄 {item.name}")
                except Exception as e:
                    self.log(f"❌ Could not list directory: {e}")
                
                # Check pip
                try:
                    result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        self.log(f"✅ Pip available: {result.stdout.strip()}")
                    else:
                        self.log(f"❌ Pip issue: {result.stderr}")
                except Exception as e:
                    self.log(f"❌ Pip check error: {e}")
                
                # Check key packages
                self.log("\n🔍 Checking Python packages:")
                packages = ["fastapi", "uvicorn", "PySide6", "torch", "transformers", "numpy"]
                available = 0
                for package in packages:
                    try:
                        __import__(package.replace("-", "_"))
                        self.log(f"✅ {package}")
                        available += 1
                    except ImportError:
                        self.log(f"❌ {package}")
                
                # Calculate status
                success_rate = (available / len(packages)) * 100
                self.log(f"\n📊 Package availability: {available}/{len(packages)} ({success_rate:.0f}%)")
                
                if success_rate >= 80:
                    self.status_label.config(text="✅ System ready")
                elif success_rate >= 50:
                    self.status_label.config(text="⚠️  Partial setup - some packages missing")
                else:
                    self.status_label.config(text="❌ Setup incomplete - install dependencies")
                
                self.log("\n🎯 System check completed")
                
            except Exception as e:
                error_msg = f"System check failed: {e}"
                self.log(f"❌ {error_msg}")
                self.log(f"📋 Traceback: {traceback.format_exc()}")
                self.status_label.config(text="❌ System check failed")
        
        # Run in background
        threading.Thread(target=check, daemon=True).start()
    
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Close InLegalDesk Debug Launcher?"):
            self.root.destroy()
    
    def run(self):
        """Run the launcher"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"❌ Launcher failed: {e}")
            print(f"📋 Traceback: {traceback.format_exc()}")
            input("Press Enter to exit...")

def main():
    """Main function with comprehensive error handling"""
    try:
        print("🚀 Starting InLegalDesk Debug Launcher...")
        print(f"📊 Python: {sys.version}")
        print(f"📂 Directory: {os.getcwd()}")
        
        # Check if we can import tkinter
        try:
            import tkinter
            print("✅ Tkinter available")
        except ImportError as e:
            print(f"❌ Tkinter not available: {e}")
            print("This is likely why the .exe closes immediately!")
            input("Press Enter to exit...")
            return
        
        # Create and run launcher
        launcher = DebugLauncher()
        launcher.run()
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        print("\nThis error explains why the .exe closes immediately!")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()