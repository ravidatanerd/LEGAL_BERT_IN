#!/usr/bin/env python3
"""
Download AI Models NOW - Direct implementation
No complex imports, just direct downloads with progress
"""
import urllib.request
import urllib.error
import os
from pathlib import Path
import sys

def show_progress(block_num, block_size, total_size):
    """Show download progress"""
    if total_size <= 0:
        return
    
    downloaded = block_num * block_size
    percent = min(100, (downloaded * 100) // total_size)
    mb_downloaded = downloaded / (1024 * 1024)
    mb_total = total_size / (1024 * 1024)
    
    # Show progress every 5%
    if percent % 5 == 0:
        bar_length = 30
        filled = int(bar_length * percent // 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\r[{bar}] {percent:3.0f}% ({mb_downloaded:5.1f}/{mb_total:5.1f} MB)", end='', flush=True)

def download_file(url, filepath, description):
    """Download a single file with progress"""
    print(f"\n📥 Downloading: {description}")
    print(f"🔗 URL: {url}")
    print(f"📁 Saving to: {filepath}")
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Download with progress
        urllib.request.urlretrieve(url, filepath, show_progress)
        print(f"\n✅ Success: {description}")
        
        # Verify file was created
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"📊 File size: {size_mb:.1f} MB")
            return True
        else:
            print(f"❌ File creation failed: {filepath}")
            return False
            
    except urllib.error.URLError as e:
        print(f"\n❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Download error: {e}")
        return False

def main():
    """Download AI models directly"""
    print("🤖 InLegalDesk AI Model Downloader")
    print("=" * 40)
    print()
    print("This will download AI models for enhanced legal research:")
    print("• InLegalBERT: 420 MB (Indian legal AI)")
    print("• Sentence Transformer: 90 MB (Text embeddings)")
    print("• Total: ~510 MB")
    print()
    print("Download time: 5-20 minutes (depending on internet speed)")
    print()
    
    # Confirm download
    try:
        response = input("Start AI model download? (Y/n): ").strip().lower()
        if response == 'n':
            print("❌ Download cancelled")
            return False
    except KeyboardInterrupt:
        print("\n❌ Download cancelled")
        return False
    
    print("\n🚀 STARTING AI MODEL DOWNLOADS")
    print("=" * 35)
    
    downloads = [
        {
            "url": "https://huggingface.co/law-ai/InLegalBERT/resolve/main/config.json",
            "filepath": "models/inlegalbert/config.json",
            "description": "InLegalBERT Config"
        },
        {
            "url": "https://huggingface.co/law-ai/InLegalBERT/resolve/main/pytorch_model.bin",
            "filepath": "models/inlegalbert/pytorch_model.bin", 
            "description": "InLegalBERT Model (Main - 420MB)"
        },
        {
            "url": "https://huggingface.co/law-ai/InLegalBERT/resolve/main/tokenizer.json",
            "filepath": "models/inlegalbert/tokenizer.json",
            "description": "InLegalBERT Tokenizer"
        },
        {
            "url": "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/config.json",
            "filepath": "models/sentence-transformer/config.json",
            "description": "Sentence Transformer Config"
        },
        {
            "url": "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/pytorch_model.bin",
            "filepath": "models/sentence-transformer/pytorch_model.bin",
            "description": "Sentence Transformer Model (90MB)"
        }
    ]
    
    successful = 0
    total = len(downloads)
    
    for i, download in enumerate(downloads, 1):
        print(f"\n📦 Download {i}/{total}")
        print("-" * 20)
        
        # Check if already exists
        if os.path.exists(download["filepath"]) and os.path.getsize(download["filepath"]) > 0:
            print(f"✅ Already exists: {download['description']}")
            successful += 1
            continue
        
        # Download file
        if download_file(download["url"], download["filepath"], download["description"]):
            successful += 1
        else:
            print(f"⚠️  Failed to download: {download['description']}")
            print("Continuing with other downloads...")
    
    # Summary
    print(f"\n📊 DOWNLOAD SUMMARY")
    print("=" * 20)
    print(f"✅ Successful: {successful}/{total} files")
    print(f"📊 Success rate: {(successful/total)*100:.0f}%")
    
    if successful >= 3:
        print("🎉 Enough models downloaded for AI features!")
        
        # Create model registry
        with open("models/downloaded.txt", "w") as f:
            f.write(f"Models downloaded: {successful}/{total}\n")
            f.write(f"Download date: {__import__('datetime').datetime.now()}\n")
            f.write("InLegalDesk AI models ready\n")
        
        return True
    else:
        print("⚠️  Insufficient models - will use basic mode")
        return False

if __name__ == "__main__":
    try:
        print("🤖 Direct AI Model Download")
        print("=" * 30)
        print("This script downloads AI models directly with visible progress")
        print()
        
        success = main()
        
        if success:
            print("\n🎊 AI models downloaded successfully!")
            print("InLegalDesk now has enhanced AI capabilities")
        else:
            print("\n📋 Download incomplete - basic mode available")
        
        print("\nNext step: Start the backend")
        print("Run: python working_app.py")
        
    except KeyboardInterrupt:
        print("\n👋 Download cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    input("\nPress Enter to exit...")