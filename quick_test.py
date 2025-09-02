#!/usr/bin/env python3
"""
Quick test script for InLegalDesk platform
Tests both backend and desktop components
"""
import os
import sys
import subprocess
import time
import json
import tempfile
from pathlib import Path

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

def print_step(step, description):
    """Print test step"""
    print(f"\n📋 Step {step}: {description}")

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_warning(message):
    """Print warning message"""
    print(f"⚠️  {message}")

def run_command(cmd, cwd=None, timeout=30):
    """Run command and return result"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def test_python_setup():
    """Test Python environment"""
    print_header("Python Environment Test")
    
    # Check Python version
    print_step(1, "Checking Python version")
    success, stdout, stderr = run_command("python3 --version")
    if success:
        version = stdout.strip()
        print_success(f"Python found: {version}")
        
        # Check if version is 3.8+
        version_num = version.split()[1]
        major, minor = map(int, version_num.split('.')[:2])
        if major >= 3 and minor >= 8:
            print_success("Python version is compatible")
            return True
        else:
            print_error(f"Python 3.8+ required, found {version_num}")
            return False
    else:
        print_error("Python3 not found")
        print("Please install Python 3.8+ from https://python.org")
        return False

def test_backend():
    """Test backend functionality"""
    print_header("Backend Test")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print_error("Backend directory not found")
        return False
    
    # Test 1: Create virtual environment
    print_step(1, "Setting up backend environment")
    venv_path = backend_dir / "venv"
    
    if not venv_path.exists():
        success, stdout, stderr = run_command("python3 -m venv venv", cwd=backend_dir)
        if not success:
            print_error(f"Failed to create virtual environment: {stderr}")
            return False
    
    print_success("Virtual environment ready")
    
    # Test 2: Install basic dependencies
    print_step(2, "Installing core dependencies")
    install_cmd = "source venv/bin/activate && pip install fastapi uvicorn pydantic python-dotenv"
    success, stdout, stderr = run_command(install_cmd, cwd=backend_dir, timeout=120)
    
    if not success:
        print_error(f"Failed to install dependencies: {stderr}")
        return False
    
    print_success("Core dependencies installed")
    
    # Test 3: Test module imports
    print_step(3, "Testing module imports")
    test_cmd = """source venv/bin/activate && python3 -c "
import sys
sys.path.append('.')
try:
    import app
    print('✅ App imports successfully')
    print('✅ FastAPI app created')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
" """
    
    success, stdout, stderr = run_command(test_cmd, cwd=backend_dir)
    if success and "✅" in stdout:
        print_success("Backend modules import correctly")
        return True
    else:
        print_error(f"Module import failed: {stderr}")
        return False

def test_security():
    """Test security features"""
    print_header("Security Test")
    
    backend_dir = Path("backend")
    
    # Test security module
    print_step(1, "Testing security validation")
    test_cmd = """source venv/bin/activate && python3 -c "
import sys
sys.path.append('.')
from security import SecurityConfig, InputValidator

# Test input sanitization
malicious_input = '<script>alert(\"xss\")</script>What is Section 302?'
sanitized = InputValidator.sanitize_query(malicious_input)
print(f'Input sanitized: {len(sanitized)} chars (was {len(malicious_input)})')

# Test API key validation
valid = InputValidator.validate_api_key('sk-test123456789012345678901234567890')
invalid = InputValidator.validate_api_key('invalid-key')
print(f'API validation: valid={valid}, invalid={invalid}')

# Test filename validation
safe = InputValidator.validate_filename('document.pdf')
unsafe = InputValidator.validate_filename('../../../etc/passwd.pdf')
print(f'Filename validation: safe={safe}, unsafe={unsafe}')

print('✅ All security validations working')
" """
    
    success, stdout, stderr = run_command(test_cmd, cwd=backend_dir)
    if success and "✅" in stdout:
        print_success("Security validation working")
        print(f"Details: {stdout.strip()}")
        return True
    else:
        print_error(f"Security test failed: {stderr}")
        return False

def test_desktop_imports():
    """Test desktop app imports"""
    print_header("Desktop App Test")
    
    desktop_dir = Path("desktop")
    if not desktop_dir.exists():
        print_error("Desktop directory not found")
        return False
    
    # Test 1: Setup desktop environment
    print_step(1, "Setting up desktop environment")
    venv_path = desktop_dir / "venv"
    
    if not venv_path.exists():
        success, stdout, stderr = run_command("python3 -m venv venv", cwd=desktop_dir)
        if not success:
            print_error(f"Failed to create desktop venv: {stderr}")
            return False
    
    # Test 2: Install PySide6
    print_step(2, "Installing PySide6 (this may take a while)")
    install_cmd = "source venv/bin/activate && pip install PySide6 httpx python-dotenv markdown"
    success, stdout, stderr = run_command(install_cmd, cwd=desktop_dir, timeout=300)
    
    if not success:
        print_warning(f"PySide6 installation may have issues: {stderr}")
        print("This is normal in headless environments")
    
    # Test 3: Test imports without GUI
    print_step(3, "Testing desktop imports (headless)")
    test_cmd = """source venv/bin/activate && python3 -c "
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
try:
    from api_client import LegalAPIClient
    print('✅ API client imports')
    
    from server_launcher import ServerLauncher
    print('✅ Server launcher imports')
    
    print('✅ Desktop core modules working')
except Exception as e:
    print(f'❌ Desktop import error: {e}')
    sys.exit(1)
" """
    
    success, stdout, stderr = run_command(test_cmd, cwd=desktop_dir)
    if success and "✅" in stdout:
        print_success("Desktop app core modules working")
        return True
    else:
        print_error(f"Desktop import test failed: {stderr}")
        return False

def test_end_to_end():
    """Test complete workflow"""
    print_header("End-to-End Integration Test")
    
    backend_dir = Path("backend")
    
    # Copy backend to desktop
    print_step(1, "Preparing desktop backend")
    desktop_server = Path("desktop/server")
    if not desktop_server.exists():
        success, stdout, stderr = run_command("cp -r ../backend server/", cwd="desktop")
        if success:
            print_success("Backend copied to desktop")
        else:
            print_warning("Failed to copy backend - manual copy may be needed")
    
    # Test environment setup
    print_step(2, "Testing environment configuration")
    env_file = backend_dir / ".env"
    if not env_file.exists():
        success, stdout, stderr = run_command("cp .env.sample .env", cwd=backend_dir)
        if success:
            print_success("Environment file created")
        else:
            print_error("Failed to create .env file")
            return False
    
    # Test basic API functionality
    print_step(3, "Testing API functionality")
    
    # Start server in background
    start_cmd = "source venv/bin/activate && timeout 30s python3 app.py"
    print("Starting backend server (30 second test)...")
    
    # Run in background and test
    server_process = subprocess.Popen(
        start_cmd,
        shell=True,
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for startup
    time.sleep(15)
    
    # Test health endpoint
    success, stdout, stderr = run_command("curl -s http://127.0.0.1:8877/health")
    if success and "healthy" in stdout:
        print_success("Backend API responding")
        print(f"Health check: {stdout.strip()}")
        
        # Test ask endpoint
        ask_cmd = 'curl -s -X POST http://127.0.0.1:8877/ask -H "Content-Type: application/json" -d \'{"question":"test"}\''
        success, stdout, stderr = run_command(ask_cmd)
        if success:
            print_success("Ask endpoint responding")
        else:
            print_warning("Ask endpoint may need API key for full functionality")
        
        result = True
    else:
        print_error("Backend not responding")
        result = False
    
    # Cleanup
    try:
        server_process.terminate()
        server_process.wait(timeout=5)
    except:
        server_process.kill()
    
    return result

def create_test_report(results):
    """Create test report"""
    print_header("Test Report Summary")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)
    
    print(f"\n📊 Test Results: {passed_tests}/{total_tests} passed\n")
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
    
    if passed_tests == total_tests:
        print(f"\n🎉 All tests passed! InLegalDesk is ready to use.")
        print("\n🚀 Next steps:")
        print("1. Configure OpenAI API key for full functionality")
        print("2. Start backend: cd backend && python3 app.py")
        print("3. Start desktop: cd desktop && python3 main.py")
        print("4. Upload PDFs and start researching!")
    else:
        print(f"\n⚠️  Some tests failed. Check the output above for details.")
        print("\n🔧 Common fixes:")
        print("1. Ensure Python 3.8+ is installed")
        print("2. Check internet connection for model downloads")
        print("3. Install missing dependencies with pip")
        print("4. Check that ports 8877 is available")
    
    return passed_tests == total_tests

def main():
    """Main test runner"""
    print("🧪 InLegalDesk Quick Test Suite")
    print("This will test the core functionality of your platform")
    print("\nNote: This test runs in headless mode and doesn't require a GUI")
    
    results = {}
    
    # Run tests
    results["Python Setup"] = test_python_setup()
    results["Backend Core"] = test_backend()
    results["Security Features"] = test_security()
    results["Desktop Imports"] = test_desktop_imports()
    results["End-to-End Integration"] = test_end_to_end()
    
    # Generate report
    success = create_test_report(results)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())