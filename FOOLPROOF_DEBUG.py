#!/usr/bin/env python3
"""
Foolproof Debug Script - Captures ALL possible errors
This will show exactly why the .exe is closing immediately
"""

# Import only built-in modules to avoid import errors
import sys
import os
import traceback
import platform

def safe_print(message):
    """Print message safely"""
    try:
        print(message)
    except:
        # If even print fails, write to file
        try:
            with open("debug_output.txt", "a") as f:
                f.write(message + "\n")
        except:
            pass

def comprehensive_debug():
    """Comprehensive debug that captures everything"""
    
    safe_print("🔧 FOOLPROOF DEBUG - CAPTURE ALL ERRORS")
    safe_print("=" * 50)
    safe_print("")
    
    # Basic system info
    try:
        safe_print(f"📊 Python version: {sys.version}")
        safe_print(f"📊 Python executable: {sys.executable}")
        safe_print(f"📊 Platform: {platform.system()} {platform.release()}")
        safe_print(f"📊 Architecture: {platform.architecture()}")
        safe_print(f"📊 Current directory: {os.getcwd()}")
        safe_print("")
    except Exception as e:
        safe_print(f"❌ Basic info error: {e}")
    
    # Test critical modules
    safe_print("🧪 TESTING CRITICAL MODULES:")
    safe_print("-" * 30)
    
    modules_to_test = [
        ("sys", "System interface"),
        ("os", "Operating system interface"),
        ("pathlib", "Path handling"),
        ("subprocess", "Process management"),
        ("threading", "Multi-threading"),
        ("tkinter", "GUI framework"),
        ("json", "JSON handling"),
        ("urllib", "URL handling"),
        ("tempfile", "Temporary files"),
        ("shutil", "File operations")
    ]
    
    failed_modules = []
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            safe_print(f"✅ {description}: {module_name}")
        except ImportError as e:
            safe_print(f"❌ {description}: {module_name} - {e}")
            failed_modules.append(module_name)
        except Exception as e:
            safe_print(f"❌ {description}: {module_name} - Unexpected error: {e}")
            failed_modules.append(module_name)
    
    safe_print("")
    
    # Check directory structure
    safe_print("📂 CHECKING DIRECTORY STRUCTURE:")
    safe_print("-" * 35)
    
    required_paths = [
        "backend",
        "desktop", 
        "backend/app.py",
        "desktop/main.py",
        "README.md"
    ]
    
    missing_paths = []
    for path in required_paths:
        if os.path.exists(path):
            safe_print(f"✅ {path}")
        else:
            safe_print(f"❌ {path} - MISSING")
            missing_paths.append(path)
    
    safe_print("")
    
    # Test if we can import external packages
    safe_print("📦 TESTING EXTERNAL PACKAGES:")
    safe_print("-" * 30)
    
    external_packages = [
        ("fastapi", "Web framework"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation"),
        ("PySide6", "Desktop GUI"),
        ("numpy", "Numerical computing"),
        ("requests", "HTTP client")
    ]
    
    missing_packages = []
    for package, description in external_packages:
        try:
            __import__(package)
            safe_print(f"✅ {description}: {package}")
        except ImportError:
            safe_print(f"❌ {description}: {package} - Not installed")
            missing_packages.append(package)
        except Exception as e:
            safe_print(f"❌ {description}: {package} - Error: {e}")
            missing_packages.append(package)
    
    safe_print("")
    
    # Analyze the results
    safe_print("📊 DIAGNOSIS RESULTS:")
    safe_print("-" * 20)
    
    critical_issues = []
    
    if "tkinter" in failed_modules:
        critical_issues.append("tkinter missing - GUI .exe cannot work")
        safe_print("❌ CRITICAL: tkinter missing - this is why GUI .exe fails!")
    
    if missing_paths:
        critical_issues.append("Missing application files")
        safe_print(f"❌ CRITICAL: Missing files - {', '.join(missing_paths)}")
    
    if len(missing_packages) > len(external_packages) * 0.5:
        critical_issues.append("Too many packages missing")
        safe_print(f"❌ CRITICAL: {len(missing_packages)} packages missing")
    
    if not critical_issues:
        safe_print("✅ No critical issues found")
        safe_print("If .exe still closes, it's likely a packaging problem")
    else:
        safe_print(f"❌ Found {len(critical_issues)} critical issues")
    
    safe_print("")
    
    # Provide specific solutions
    safe_print("🔧 SPECIFIC SOLUTIONS:")
    safe_print("-" * 20)
    
    if "tkinter" in failed_modules:
        safe_print("For tkinter missing:")
        safe_print("1. Reinstall Python from https://python.org")
        safe_print("2. Choose 'Custom Installation'")
        safe_print("3. CHECK 'tcl/tk and IDLE' option")
        safe_print("4. CHECK 'Add Python to PATH'")
        safe_print("")
    
    if missing_paths:
        safe_print("For missing files:")
        safe_print("1. Re-download InLegalDesk from GitHub")
        safe_print("2. Extract ALL files from ZIP")
        safe_print("3. Make sure backend/ and desktop/ folders exist")
        safe_print("4. Run diagnostic from the correct directory")
        safe_print("")
    
    if missing_packages:
        safe_print("For missing packages:")
        safe_print("1. Run: python -m pip install --upgrade pip")
        safe_print("2. Run: UPGRADE_PIP_FIRST.bat")
        safe_print("3. Run: ULTIMATE_AI_FIX.bat")
        safe_print("")
    
    # Test launching components directly
    safe_print("🚀 TESTING DIRECT LAUNCH:")
    safe_print("-" * 25)
    
    if os.path.exists("backend/app.py"):
        safe_print("Testing backend launch...")
        try:
            # Test import of backend
            sys.path.insert(0, "backend")
            import app
            safe_print("✅ Backend app.py can be imported")
        except ImportError as e:
            safe_print(f"❌ Backend import failed: {e}")
        except Exception as e:
            safe_print(f"❌ Backend error: {e}")
        finally:
            if "backend" in sys.path:
                sys.path.remove("backend")
    
    if os.path.exists("desktop/main.py") and "tkinter" not in failed_modules:
        safe_print("Testing desktop import...")
        try:
            sys.path.insert(0, "desktop")
            # Just test if we can read the file
            with open("desktop/main.py", "r") as f:
                content = f.read()
                if "PySide6" in content:
                    safe_print("✅ Desktop uses PySide6")
                    try:
                        import PySide6
                        safe_print("✅ PySide6 available")
                    except ImportError:
                        safe_print("❌ PySide6 not installed")
        except Exception as e:
            safe_print(f"❌ Desktop check error: {e}")
        finally:
            if "desktop" in sys.path:
                sys.path.remove("desktop")
    
    safe_print("")
    safe_print("🎯 FINAL DIAGNOSIS:")
    safe_print("-" * 18)
    
    if critical_issues:
        safe_print("❌ .exe closes immediately because:")
        for i, issue in enumerate(critical_issues, 1):
            safe_print(f"   {i}. {issue}")
        safe_print("")
        safe_print("🔧 Fix these issues and the .exe should work!")
    else:
        safe_print("✅ System looks OK - .exe closing might be packaging issue")
        safe_print("💡 Try the manual installers instead")
    
    safe_print("")

def main():
    """Main debug function with maximum error capture"""
    
    # Create debug log file
    debug_file = "emergency_debug_log.txt"
    
    try:
        # Redirect output to both console and file
        import sys
        
        class TeeOutput:
            def __init__(self, *files):
                self.files = files
            
            def write(self, text):
                for f in self.files:
                    try:
                        f.write(text)
                        f.flush()
                    except:
                        pass
            
            def flush(self):
                for f in self.files:
                    try:
                        f.flush()
                    except:
                        pass
        
        # Open debug file
        with open(debug_file, "w") as debug_log:
            # Redirect stdout to both console and file
            original_stdout = sys.stdout
            sys.stdout = TeeOutput(original_stdout, debug_log)
            
            try:
                comprehensive_debug()
            finally:
                sys.stdout = original_stdout
        
        print(f"\n📋 Debug log saved to: {debug_file}")
        
    except Exception as e:
        # If even the tee output fails, just use direct output
        print(f"❌ Output redirection failed: {e}")
        print("Running direct debug...")
        comprehensive_debug()
    
    print("\n" + "="*50)
    print("🔍 EMERGENCY DEBUG COMPLETED")
    print("="*50)
    print("")
    print("If the .exe still closes immediately after fixing")
    print("the issues above, the problem is with the .exe")
    print("packaging itself - use the manual installers instead.")
    print("")
    
    # Don't close immediately
    try:
        input("Press Enter to exit...")
    except:
        import time
        time.sleep(10)  # Wait 10 seconds if input fails

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Absolute last resort error handling
        try:
            print(f"❌ CRITICAL FAILURE: {e}")
            print(f"📋 Traceback: {traceback.format_exc()}")
            input("Press Enter to exit...")
        except:
            # If everything fails, just wait
            import time
            time.sleep(10)