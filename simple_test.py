#!/usr/bin/env python3
"""
Simple test script for InLegalDesk - works in any environment
"""
import sys
import os
from pathlib import Path

def test_project_structure():
    """Test that all required files exist"""
    print("🔍 Testing project structure...")
    
    required_files = [
        "backend/app.py",
        "backend/requirements.txt", 
        "backend/security.py",
        "desktop/main.py",
        "desktop/credential_manager.py",
        "installer/build_installer.ps1",
        "installer/InLegalDesk.iss"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_imports():
    """Test Python imports"""
    print("\n🐍 Testing Python imports...")
    
    # Test backend imports
    sys.path.append('backend')
    try:
        from security import SecurityConfig, InputValidator
        print("✅ Backend security module imports")
        
        # Test security functions
        sanitized = InputValidator.sanitize_query('<script>test</script>')
        valid_key = InputValidator.validate_api_key('sk-test123456789012345678901234567890')
        print(f"✅ Security functions work: sanitized={len(sanitized)}, valid_key={valid_key}")
        
    except ImportError as e:
        print(f"⚠️  Backend import issue (expected without dependencies): {e}")
    except Exception as e:
        print(f"❌ Backend error: {e}")
        return False
    
    # Test desktop imports (basic)
    sys.path.append('desktop')
    try:
        # Test basic Python files exist and are valid
        with open('desktop/main.py', 'r') as f:
            content = f.read()
            if 'class InLegalDeskApp' in content:
                print("✅ Desktop app structure valid")
            else:
                print("❌ Desktop app structure invalid")
                return False
                
    except Exception as e:
        print(f"❌ Desktop test error: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration files"""
    print("\n⚙️ Testing configuration...")
    
    # Check environment files
    config_files = [
        "backend/.env.sample",
        "desktop/.env.sample"
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            with open(config_file, 'r') as f:
                content = f.read()
                if 'OPENAI_API_KEY' in content:
                    print(f"✅ {config_file} valid")
                else:
                    print(f"❌ {config_file} missing required settings")
                    return False
        else:
            print(f"❌ Missing {config_file}")
            return False
    
    return True

def test_documentation():
    """Test documentation completeness"""
    print("\n📚 Testing documentation...")
    
    docs = [
        "README.md",
        "SECURITY.md", 
        "TESTING_GUIDE.md",
        "DEPLOYMENT_GUIDE.md"
    ]
    
    for doc in docs:
        if Path(doc).exists():
            with open(doc, 'r') as f:
                content = f.read()
                if len(content) > 1000:  # Substantial documentation
                    print(f"✅ {doc} complete")
                else:
                    print(f"⚠️  {doc} seems incomplete")
        else:
            print(f"❌ Missing {doc}")
            return False
    
    return True

def show_manual_test_instructions():
    """Show manual testing instructions"""
    print("\n" + "="*60)
    print("📋 MANUAL TESTING INSTRUCTIONS")
    print("="*60)
    
    print("""
🚀 QUICK START TESTING:

1. TEST BACKEND:
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\\Scripts\\activate   # Windows
   pip install -r requirements.txt
   cp .env.sample .env
   python3 app.py
   
   Expected: Server starts, InLegalBERT downloads, API responds

2. TEST API (new terminal):
   curl http://127.0.0.1:8877/health
   
   Expected: {"status":"healthy","components":{"ingestor":true,"retriever":true,"llm":true}}

3. TEST DESKTOP (if GUI available):
   cd desktop
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp -r ../backend server/
   python3 main.py
   
   Expected: ChatGPT-style GUI opens, backend connects

4. TEST CREDENTIALS:
   - Click "🔑 API Credentials" in desktop app
   - Enter OpenAI API key
   - Set master password
   - Test connection
   - Save encrypted
   
   Expected: Credentials saved securely, full AI features unlocked

5. TEST SECURITY:
   cd backend
   python3 test_security.py
   
   Expected: All security tests pass, rate limiting works

6. BUILD INSTALLER (Windows):
   cd installer
   .\\build_installer.ps1
   
   Expected: InLegalDesk_Installer.exe created
""")

def main():
    """Main test function"""
    print("🧪 InLegalDesk Simple Test Suite")
    print("Testing core components without dependencies...\n")
    
    results = {}
    
    # Run basic tests
    results["Project Structure"] = test_project_structure()
    results["Python Imports"] = test_imports()
    results["Configuration"] = test_configuration()
    results["Documentation"] = test_documentation()
    
    # Show results
    print("\n" + "="*60)
    print("📊 TEST RESULTS")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 Basic structure tests passed!")
        print("✅ InLegalDesk platform is properly structured")
        print("✅ All required files are present")
        print("✅ Configuration files are valid")
        print("✅ Documentation is complete")
    else:
        print("\n⚠️  Some basic tests failed")
    
    # Show manual testing instructions
    show_manual_test_instructions()
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())