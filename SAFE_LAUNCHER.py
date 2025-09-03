#!/usr/bin/env python3
"""
Safe InLegalDesk Launcher
Automatically detects Python version and uses appropriate interface
Fixes Unicode emoji issues with Python 3.6.6
"""
import sys
import os

def check_python_emoji_support():
    """Check if Python/tkinter supports Unicode emojis"""
    try:
        import tkinter as tk
        
        # Test if we can create a label with emoji
        test_root = tk.Tk()
        test_root.withdraw()  # Hide window
        
        # Try to create label with emoji - this will fail on Python 3.6.6
        test_label = tk.Label(test_root, text="🔧")
        test_root.destroy()
        
        return True  # If we get here, emojis work
        
    except Exception as e:
        # Unicode emoji not supported
        return False

def launch_appropriate_version():
    """Launch the appropriate version based on Python capabilities"""
    
    print("InLegalDesk Safe Launcher")
    print("=" * 30)
    print("Python version: {}".format(sys.version))
    
    # Check Python version
    version_info = sys.version_info
    is_python36 = version_info.major == 3 and version_info.minor == 6
    
    # Check emoji support
    emoji_support = check_python_emoji_support()
    
    print("Python 3.6: {}".format("Yes" if is_python36 else "No"))
    print("Emoji support: {}".format("Yes" if emoji_support else "No"))
    print("")
    
    if is_python36 or not emoji_support:
        print("Using Python 3.6 compatible version (no emojis)")
        print("This fixes the Unicode emoji crash issue.")
        print("")
        
        # Use Python 3.6 compatible version
        if os.path.exists("InLegalDesk_Python36_Compatible.py"):
            print("Launching Python 3.6 compatible version...")
            os.system("python InLegalDesk_Python36_Compatible.py")
        else:
            print("Python 3.6 compatible version not found!")
            print("Creating emergency launcher...")
            create_emergency_launcher()
    else:
        print("Using full-featured version with emoji support")
        print("")
        
        # Use full version
        if os.path.exists("InLegalDesk_Debug_Launcher.py"):
            print("Launching full debug version...")
            os.system("python InLegalDesk_Debug_Launcher.py")
        elif os.path.exists("InLegalDesk_Console.py"):
            print("Launching console version...")
            os.system("python InLegalDesk_Console.py")
        else:
            print("No launcher found! Creating emergency version...")
            create_emergency_launcher()

def create_emergency_launcher():
    """Create emergency launcher if none exist"""
    print("Creating emergency launcher...")
    
    emergency_code = '''
import sys
import os
import subprocess
import tkinter as tk
from tkinter import messagebox

def launch_backend():
    try:
        if os.path.exists("backend/app.py"):
            os.chdir("backend")
            subprocess.Popen([sys.executable, "app.py"])
            messagebox.showinfo("Success", "Backend started!\\nVisit: http://localhost:8877")
        else:
            messagebox.showerror("Error", "backend/app.py not found!")
    except Exception as e:
        messagebox.showerror("Error", "Failed to start backend: " + str(e))

def main():
    root = tk.Tk()
    root.title("InLegalDesk Emergency Launcher")
    root.geometry("400x250")
    
    tk.Label(root, text="InLegalDesk Emergency Launcher", 
             font=("Arial", 14, "bold")).pack(pady=20)
    
    tk.Label(root, text="Python 3.6.6 Compatible Version", 
             font=("Arial", 10)).pack(pady=5)
    
    tk.Button(root, text="Launch Backend Server", 
              command=launch_backend, width=20, height=2).pack(pady=10)
    
    tk.Label(root, text="After clicking above, visit:", 
             font=("Arial", 10)).pack(pady=5)
    
    tk.Label(root, text="http://localhost:8877", 
             font=("Arial", 10, "bold"), fg="blue").pack(pady=5)
    
    tk.Label(root, text="(Web interface works with Python 3.6.6)", 
             font=("Arial", 9), fg="gray").pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR: " + str(e))
        input("Press Enter to exit...")
'''
    
    with open("emergency_launcher.py", "w") as f:
        f.write(emergency_code)
    
    print("Emergency launcher created: emergency_launcher.py")
    print("Running emergency launcher...")
    os.system("python emergency_launcher.py")

if __name__ == "__main__":
    try:
        launch_appropriate_version()
    except Exception as e:
        print("CRITICAL ERROR: {}".format(e))
        print("")
        print("Even the safe launcher failed!")
        print("This indicates a serious Python installation issue.")
        print("")
        print("SOLUTIONS:")
        print("1. Reinstall Python 3.7+ from https://python.org")
        print("2. Make sure 'Add Python to PATH' is checked")
        print("3. Include full standard library (tcl/tk)")
        print("4. Restart computer after installation")
        print("")
        try:
            input("Press Enter to exit...")
        except:
            import time
            time.sleep(10)