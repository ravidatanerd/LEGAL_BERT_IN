#!/usr/bin/env python3
"""
InLegalDesk Startup with Automatic Model Download
Downloads AI models on first run, then starts the backend
"""
import os
import sys
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_ai_packages():
    """Check if AI packages are available"""
    try:
        import torch
        import transformers
        return True, "AI packages available"
    except ImportError as e:
        return False, f"AI packages missing: {e}"

def install_ai_packages():
    """Install AI packages if missing"""
    print("🤖 INSTALLING AI PACKAGES...")
    print("=" * 30)
    print()
    
    packages = [
        "torch>=1.7.0",
        "transformers>=4.12.0", 
        "sentence-transformers>=2.0.0",
        "numpy>=1.19.0"
    ]
    
    print("Installing AI packages for model support...")
    print("This may take a few minutes...")
    print()
    
    for package in packages:
        print(f"📦 Installing {package}...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ {package} installed")
            else:
                print(f"⚠️  {package} failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {package} installation timed out")
        except Exception as e:
            print(f"❌ {package} error: {e}")
    
    # Test if packages are now available
    ai_available, message = check_ai_packages()
    if ai_available:
        print("\n✅ AI packages installed successfully!")
        return True
    else:
        print(f"\n⚠️  AI packages still not available: {message}")
        print("Will continue in basic mode")
        return False

def download_models_on_first_run():
    """Download models on first run"""
    print("\n🤖 AI MODEL SETUP")
    print("=" * 20)
    
    # Check if AI packages are available
    ai_available, message = check_ai_packages()
    
    if not ai_available:
        print(f"⚠️  {message}")
        print()
        
        install_choice = input("Install AI packages for enhanced features? (Y/n): ").strip().lower()
        if install_choice != 'n':
            ai_available = install_ai_packages()
        
        if not ai_available:
            print("📋 Continuing without AI packages - basic mode available")
            return False
    
    # Check if models need to be downloaded
    try:
        from model_downloader import ModelDownloader
        
        downloader = ModelDownloader()
        download_info = downloader.get_download_info()
        
        if not download_info["download_required"]:
            print("✅ All AI models already downloaded!")
            return True
        
        print(f"\n📊 MODELS TO DOWNLOAD:")
        print("-" * 25)
        
        for model in download_info["models_to_download"]:
            status = "REQUIRED" if model["required"] else "OPTIONAL"
            print(f"• {model['name']}: {model['size']} ({status})")
        
        print(f"\nTotal size: {download_info['total_size_estimate']}")
        print("Download time: 5-15 minutes (depending on internet speed)")
        print()
        
        download_choice = input("Download AI models now? (Y/n): ").strip().lower()
        if download_choice == 'n':
            print("📋 Skipping model download - basic mode available")
            return False
        
        print("\n🚀 DOWNLOADING AI MODELS...")
        print("=" * 30)
        print()
        print("This will download InLegalBERT and other AI models")
        print("for enhanced legal research capabilities.")
        print()
        
        # Download models
        results = downloader.download_all_models(required_only=True)
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        if successful > 0:
            print(f"\n✅ Downloaded {successful}/{total} models successfully!")
            return True
        else:
            print(f"\n❌ Model download failed - continuing in basic mode")
            return False
            
    except ImportError:
        print("⚠️  Model downloader not available - basic mode only")
        return False
    except Exception as e:
        print(f"❌ Model download error: {e}")
        return False

def start_backend():
    """Start the backend server"""
    print("\n🚀 STARTING INLEGALDESK BACKEND")
    print("=" * 35)
    print()
    
    try:
        # Import and run the main app
        from simple_app import app
        import uvicorn
        
        port = int(os.getenv("BACKEND_PORT", 8877))
        
        print(f"🌐 Starting server on: http://localhost:{port}")
        print("📱 Features available:")
        print("   ✅ Legal question answering")
        print("   ✅ Document upload and analysis") 
        print("   ✅ ChatGPT-style interface")
        print("   ✅ Premium to free model fallback")
        
        if model_downloader:
            model_status = model_downloader.check_models_exist()
            available_models = sum(1 for exists in model_status.values() if exists)
            total_models = len(model_status)
            print(f"   🤖 AI models: {available_models}/{total_models} available")
        
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            masked_key = api_key[:7] + "..." + api_key[-4:] if len(api_key) > 10 else "sk-****"
            print(f"   🔑 OpenAI API: {masked_key}")
        else:
            print("   ⚠️  OpenAI API: Not configured (basic mode)")
        
        print()
        print("✅ Backend ready - open http://localhost:8877 in your browser!")
        print()
        
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Missing required packages - please install:")
        print("   pip install fastapi uvicorn pydantic")
        return False
    except Exception as e:
        print(f"❌ Startup error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main startup function"""
    print("🏛️ InLegalDesk Startup with Model Download")
    print("=" * 45)
    print()
    print("This will:")
    print("1. Check for AI packages")
    print("2. Download models on first run") 
    print("3. Start the backend server")
    print("4. Provide full working InLegalDesk")
    print()
    
    try:
        # Step 1: Download models if needed
        models_ready = download_models_on_first_run()
        
        if models_ready:
            print("🎉 AI models ready - full features available!")
        else:
            print("📋 Basic mode ready - still fully functional!")
        
        # Step 2: Start backend
        start_backend()
        
    except KeyboardInterrupt:
        print("\n👋 Startup cancelled by user")
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()