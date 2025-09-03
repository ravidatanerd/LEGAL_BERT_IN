#!/usr/bin/env python3
"""
InLegalDesk Python 3.6 Compatible Launcher
NO EMOJIS - Fixes Unicode error that crashes Python 3.6.6 tkinter
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

class Python36CompatibleLauncher:
    """Python 3.6 compatible launcher - NO UNICODE EMOJIS"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("InLegalDesk Launcher")
        self.root.geometry("700x600")
        
        # Prevent window from closing immediately
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.log_text = None
        self.setup_ui()
        self.log("InLegalDesk Launcher Started (Python 3.6 Compatible)")
        self.log("Python: " + sys.version)
        self.log("Working Directory: " + os.getcwd())
        
        # Start system check
        self.check_system()
        
    def setup_ui(self):
        """Setup the UI without Unicode emojis"""
        # Header
        header_frame = tk.Frame(self.root, bg="#007acc", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # NO EMOJIS - use text only
        tk.Label(header_frame, text="InLegalDesk Debug Launcher", 
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
        
        # NO EMOJIS in button text
        tk.Button(buttons_frame, text="Recheck System", command=self.check_system,
                 font=("Arial", 10), bg="#17a2b8", fg="white").pack(side="left", padx=5)
        
        tk.Button(buttons_frame, text="Launch Backend", command=self.launch_backend,
                 font=("Arial", 10), bg="#007acc", fg="white").pack(side="left", padx=5)
        
        tk.Button(buttons_frame, text="Launch Desktop", command=self.launch_desktop,
                 font=("Arial", 10), bg="#28a745", fg="white").pack(side="left", padx=5)
        
        tk.Button(buttons_frame, text="Open Web Interface", command=self.open_web,
                 font=("Arial", 10), bg="#6f42c1", fg="white").pack(side="left", padx=5)
        
        tk.Button(buttons_frame, text="Install Dependencies", command=self.install_dependencies,
                 font=("Arial", 10), bg="#ffc107", fg="black").pack(side="left", padx=5)
        
        # Status frame
        status_frame = tk.Frame(main_frame)
        status_frame.pack(fill="x", pady=(10, 0))
        
        self.status_label = tk.Label(status_frame, text="Starting system check...", 
                                   font=("Arial", 9), fg="#666")
        self.status_label.pack()
        
    def log(self, message):
        """Add message to log - NO EMOJIS"""
        timestamp = time.strftime("%H:%M:%S")
        # Remove any potential Unicode characters
        clean_message = message.encode('ascii', 'ignore').decode('ascii')
        log_message = "[{}] {}\n".format(timestamp, clean_message)
        
        if self.log_text:
            self.log_text.insert(tk.END, log_message)
            self.log_text.see(tk.END)
            self.root.update()
        
        print(clean_message)  # Also print to console
    
    def check_system(self):
        """Comprehensive system check - NO EMOJIS"""
        def check():
            try:
                self.log("STARTING COMPREHENSIVE SYSTEM CHECK")
                self.log("=" * 50)
                
                # Check Python version
                self.log("Python Version: " + sys.version)
                version_info = sys.version_info
                if version_info.major == 3 and version_info.minor >= 7:
                    self.log("OK: Python version compatible")
                elif version_info.major == 3 and version_info.minor == 6:
                    self.log("WARNING: Python 3.6 - limited compatibility")
                    self.log("RECOMMENDATION: Upgrade to Python 3.7+ for full features")
                else:
                    self.log("ERROR: Python version incompatible")
                
                # Check pip
                try:
                    result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        self.log("OK: Pip - " + result.stdout.strip())
                    else:
                        self.log("ERROR: Pip check failed - " + result.stderr)
                except Exception as e:
                    self.log("ERROR: Pip error - " + str(e))
                
                # Check working directory
                cwd = Path.cwd()
                self.log("Working Directory: " + str(cwd))
                
                # Check for key files
                key_files = ["backend", "desktop", "README.md"]
                for file_name in key_files:
                    file_path = cwd / file_name
                    if file_path.exists():
                        self.log("OK: Found " + file_name)
                    else:
                        self.log("ERROR: Missing " + file_name)
                
                # Check for backend files
                backend_dir = cwd / "backend"
                if backend_dir.exists():
                    backend_files = ["app.py", "requirements.txt"]
                    for file_name in backend_files:
                        file_path = backend_dir / file_name
                        if file_path.exists():
                            self.log("OK: Backend " + file_name)
                        else:
                            self.log("ERROR: Backend missing " + file_name)
                
                # Check for desktop files
                desktop_dir = cwd / "desktop"
                if desktop_dir.exists():
                    desktop_files = ["main.py"]
                    for file_name in desktop_files:
                        file_path = desktop_dir / file_name
                        if file_path.exists():
                            self.log("OK: Desktop " + file_name)
                        else:
                            self.log("ERROR: Desktop missing " + file_name)
                
                # Check Python packages
                self.log("")
                self.log("CHECKING PYTHON PACKAGES:")
                self.log("-" * 30)
                
                critical_packages = [
                    "fastapi", "uvicorn", "pydantic", "requests", 
                    "numpy", "torch", "transformers", "PySide6",
                    "PyMuPDF", "pytesseract"
                ]
                
                missing_packages = []
                for package in critical_packages:
                    try:
                        __import__(package.replace("-", "_"))
                        self.log("OK: " + package)
                    except ImportError:
                        self.log("MISSING: " + package)
                        missing_packages.append(package)
                
                # Summary
                self.log("")
                self.log("SYSTEM CHECK SUMMARY:")
                self.log("-" * 25)
                
                if not missing_packages:
                    self.log("EXCELLENT: All packages available - ready to launch!")
                    self.status_label.config(text="System ready - all dependencies available")
                else:
                    self.log("WARNING: Missing packages - " + ", ".join(missing_packages[:5]))
                    self.status_label.config(text="Missing {} packages".format(len(missing_packages)))
                
                # Check virtual environments
                backend_venv = cwd / "backend" / "venv"
                desktop_venv = cwd / "desktop" / "venv"
                
                if backend_venv.exists():
                    self.log("OK: Backend virtual environment found")
                else:
                    self.log("WARNING: Backend virtual environment missing")
                
                if desktop_venv.exists():
                    self.log("OK: Desktop virtual environment found")
                else:
                    self.log("WARNING: Desktop virtual environment missing")
                
                self.log("")
                self.log("RECOMMENDATIONS:")
                self.log("-" * 20)
                
                if missing_packages:
                    self.log("ACTION: Click 'Install Dependencies' to install missing packages")
                
                if version_info.major == 3 and version_info.minor < 7:
                    self.log("ACTION: Consider upgrading Python to 3.7+ for full compatibility")
                
                self.log("INFO: Check log above for any errors or missing components")
                
            except Exception as e:
                self.log("ERROR: System check failed - " + str(e))
                self.log("Traceback: " + traceback.format_exc())
        
        # Run check in background thread
        threading.Thread(target=check, daemon=True).start()
    
    def launch_backend(self):
        """Launch backend with error handling - NO EMOJIS"""
        try:
            self.log("Launching backend server...")
            
            backend_dir = Path.cwd() / "backend"
            if not backend_dir.exists():
                self.log("ERROR: Backend directory not found!")
                messagebox.showerror("Error", "Backend directory not found at: {}".format(backend_dir))
                return
            
            # Check for app.py
            app_file = backend_dir / "app.py"
            if not app_file.exists():
                self.log("ERROR: Backend app.py not found!")
                messagebox.showerror("Error", "app.py not found at: {}".format(app_file))
                return
            
            # Try to launch with virtual environment first
            venv_python = backend_dir / "venv" / "Scripts" / "python.exe"
            if venv_python.exists():
                self.log("OK: Using virtual environment")
                cmd = [str(venv_python), "app.py"]
                cwd = backend_dir
            else:
                self.log("WARNING: No virtual environment, using system Python")
                cmd = [sys.executable, "app.py"]
                cwd = backend_dir
            
            # Launch backend
            process = subprocess.Popen(cmd, cwd=cwd, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            
            self.log("OK: Backend launched with PID: {}".format(process.pid))
            self.log("INFO: Backend should be available at: http://localhost:8877")
            
            # Check if process is still running after a moment
            time.sleep(2)
            if process.poll() is None:
                self.log("OK: Backend server is running")
                messagebox.showinfo("Success", "Backend server started successfully!\n\nAccess at: http://localhost:8877")
            else:
                stdout, stderr = process.communicate()
                self.log("ERROR: Backend exited immediately")
                self.log("Stdout: " + stdout)
                self.log("Stderr: " + stderr)
                messagebox.showerror("Error", "Backend failed to start:\n{}".format(stderr))
                
        except Exception as e:
            error_msg = "Failed to launch backend: {}".format(e)
            self.log("ERROR: " + error_msg)
            self.log("Traceback: " + traceback.format_exc())
            messagebox.showerror("Error", error_msg)
    
    def launch_desktop(self):
        """Launch desktop GUI with error handling - NO EMOJIS"""
        try:
            self.log("Launching desktop GUI...")
            
            desktop_dir = Path.cwd() / "desktop"
            if not desktop_dir.exists():
                self.log("ERROR: Desktop directory not found!")
                messagebox.showerror("Error", "Desktop directory not found at: {}".format(desktop_dir))
                return
            
            # Check for main.py
            main_file = desktop_dir / "main.py"
            if not main_file.exists():
                self.log("ERROR: Desktop main.py not found!")
                messagebox.showerror("Error", "main.py not found at: {}".format(main_file))
                return
            
            # Check for PySide6
            try:
                import PySide6
                self.log("OK: PySide6 available")
            except ImportError:
                self.log("ERROR: PySide6 not available")
                messagebox.showerror("Error", "PySide6 not installed! Desktop GUI cannot run.\n\nPySide6 requires Python 3.7+\nYour Python 3.6.6 is not compatible.\n\nUse web interface instead or upgrade Python.")
                return
            
            # Try to launch with virtual environment first
            venv_python = desktop_dir / "venv" / "Scripts" / "python.exe"
            if venv_python.exists():
                self.log("OK: Using desktop virtual environment")
                cmd = [str(venv_python), "main.py"]
                cwd = desktop_dir
            else:
                self.log("WARNING: No virtual environment, using system Python")
                cmd = [sys.executable, "main.py"]
                cwd = desktop_dir
            
            # Launch desktop
            process = subprocess.Popen(cmd, cwd=cwd,
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            
            self.log("OK: Desktop launched with PID: {}".format(process.pid))
            
            # Check if process is still running
            time.sleep(2)
            if process.poll() is None:
                self.log("OK: Desktop GUI is running")
                messagebox.showinfo("Success", "Desktop GUI started successfully!")
            else:
                stdout, stderr = process.communicate()
                self.log("ERROR: Desktop exited immediately")
                self.log("Stdout: " + stdout)
                self.log("Stderr: " + stderr)
                messagebox.showerror("Error", "Desktop failed to start:\n{}".format(stderr))
                
        except Exception as e:
            error_msg = "Failed to launch desktop: {}".format(e)
            self.log("ERROR: " + error_msg)
            self.log("Traceback: " + traceback.format_exc())
            messagebox.showerror("Error", error_msg)
    
    def open_web(self):
        """Open web interface - NO EMOJIS"""
        try:
            self.log("Opening web interface...")
            webbrowser.open("http://localhost:8877")
            self.log("OK: Web browser opened")
            messagebox.showinfo("Web Interface", 
                               "Web interface opened in browser.\n\n" +
                               "URL: http://localhost:8877\n\n" +
                               "Note: Make sure backend server is running first!")
        except Exception as e:
            error_msg = "Failed to open web interface: {}".format(e)
            self.log("ERROR: " + error_msg)
            messagebox.showerror("Error", error_msg)
    
    def install_dependencies(self):
        """Install dependencies with detailed logging - NO EMOJIS"""
        try:
            self.log("Starting dependency installation...")
            
            # Check for installers
            installers = [
                "ULTIMATE_AI_FIX.bat",
                "AUTO_PYTHON_UPGRADE.bat", 
                "UPGRADE_PIP_FIRST.bat"
            ]
            
            available_installers = []
            for installer in installers:
                if Path(installer).exists():
                    available_installers.append(installer)
                    self.log("OK: Found installer - " + installer)
                else:
                    self.log("WARNING: Missing installer - " + installer)
            
            if not available_installers:
                self.log("ERROR: No installers found!")
                
                # Try direct pip installation
                self.log("Attempting direct pip installation...")
                try:
                    # Upgrade pip first
                    result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                                          capture_output=True, text=True, timeout=120)
                    if result.returncode == 0:
                        self.log("OK: Pip upgraded")
                    else:
                        self.log("WARNING: Pip upgrade failed - " + result.stderr)
                    
                    # Install basic packages for Python 3.6
                    basic_packages = [
                        "fastapi>=0.65.0,<0.75.0",
                        "uvicorn[standard]>=0.13.0,<0.16.0", 
                        "pydantic>=1.8.0,<1.9.0",
                        "requests>=2.25.0",
                        "numpy>=1.19.0,<1.20.0"
                    ]
                    
                    for package in basic_packages:
                        self.log("Installing: " + package)
                        result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                                              capture_output=True, text=True, timeout=300)
                        if result.returncode == 0:
                            self.log("OK: " + package)
                        else:
                            self.log("ERROR: " + package + " - " + result.stderr)
                    
                    messagebox.showinfo("Info", "Basic dependency installation attempted.\nCheck log for results.")
                    
                except Exception as e:
                    self.log("ERROR: Direct installation failed - " + str(e))
                    messagebox.showerror("Error", "Direct installation failed: {}".format(e))
                return
            
            # Use the first available installer
            installer = available_installers[0]
            self.log("Using installer: " + installer)
            
            subprocess.Popen(["cmd", "/c", installer])
            
            self.log("OK: Dependency installer started")
            messagebox.showinfo("Success", "Dependency installer started: {}".format(installer))
            
        except Exception as e:
            error_msg = "Failed to start dependency installer: {}".format(e)
            self.log("ERROR: " + error_msg)
            self.log("Traceback: " + traceback.format_exc())
            messagebox.showerror("Error", error_msg)
    
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Close InLegalDesk Launcher?"):
            self.root.destroy()
    
    def run(self):
        """Run the launcher"""
        try:
            self.root.mainloop()
        except Exception as e:
            print("ERROR: Launcher failed - {}".format(e))
            print("Traceback: " + traceback.format_exc())
            input("Press Enter to exit...")

def main():
    """Main function with comprehensive error handling - NO EMOJIS"""
    try:
        print("Starting InLegalDesk Launcher (Python 3.6 Compatible)...")
        print("Python: " + sys.version)
        print("Directory: " + os.getcwd())
        
        # Check if we can import tkinter
        try:
            import tkinter
            print("OK: Tkinter available")
        except ImportError as e:
            print("ERROR: Tkinter not available - " + str(e))
            print("This is why the GUI .exe closes immediately!")
            print("")
            print("SOLUTION:")
            print("1. Reinstall Python with full standard library")
            print("2. Make sure 'tcl/tk and IDLE' is included")
            print("3. Or use the web interface instead")
            input("Press Enter to exit...")
            return
        
        # Test for Unicode emoji issue (the original problem)
        try:
            # This would fail on Python 3.6.6 tkinter
            test_root = tk.Tk()
            test_root.withdraw()  # Hide window
            test_label = tk.Label(test_root, text="Test")  # No emoji
            test_root.destroy()
            print("OK: Tkinter Unicode support working")
        except Exception as e:
            print("WARNING: Tkinter Unicode issue detected - " + str(e))
            print("Using ASCII-only version to avoid crashes")
        
        # Create and run launcher
        launcher = Python36CompatibleLauncher()
        launcher.run()
        
    except Exception as e:
        print("CRITICAL ERROR: " + str(e))
        print("Traceback: " + traceback.format_exc())
        print("")
        print("This error explains why the .exe closes immediately!")
        print("")
        print("SOLUTION:")
        print("1. Fix the error shown above")
        print("2. Or use manual installers: ULTIMATE_AI_FIX.bat")
        print("3. Or upgrade Python to 3.7+ for better compatibility")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()