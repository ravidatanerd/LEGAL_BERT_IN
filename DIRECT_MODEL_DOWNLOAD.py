#!/usr/bin/env python3
"""
Direct AI Model Download Script
Downloads InLegalBERT and other AI models with visible progress
"""
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
import json
import time

def download_with_progress(url, filename, description):
    """Download file with progress bar"""
    print(f"\n🤖 DOWNLOADING {description}")
    print(f"📥 URL: {url}")
    print(f"📁 File: {filename}")
    print("-" * 60)
    
    def progress_hook(block_num, block_size, total_size):
        if total_size > 0:
            downloaded = block_num * block_size
            percent = min(100, (downloaded * 100) // total_size)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            
            # Update progress every 2%
            if percent % 2 == 0:
                bar_length = 40
                filled_length = int(bar_length * percent // 100)
                bar = '█' * filled_length + '-' * (bar_length - filled_length)
                print(f"\r[{bar}] {percent:3.0f}% ({mb_downloaded:6.1f}/{mb_total:6.1f} MB)", end='', flush=True)
    
    try:
        urllib.request.urlretrieve(url, filename, progress_hook)
        print(f"\n✅ Downloaded: {description}")
        return True
    except Exception as e:
        print(f"\n❌ Failed: {description} - {e}")
        return False

def download_inlegalbert():
    """Download InLegalBERT model files"""
    print("🤖 DOWNLOADING INLEGALBERT MODEL")
    print("=" * 40)
    print("This is the core AI model for Indian legal research")
    print("Size: ~420 MB (may take 5-15 minutes)")
    print()
    
    # Create models directory
    models_dir = Path("models/inlegalbert")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # InLegalBERT files to download
    files_to_download = [
        {
            "filename": "config.json",
            "url": "https://huggingface.co/law-ai/InLegalBERT/resolve/main/config.json",
            "description": "Model Configuration"
        },
        {
            "filename": "pytorch_model.bin", 
            "url": "https://huggingface.co/law-ai/InLegalBERT/resolve/main/pytorch_model.bin",
            "description": "InLegalBERT Model Weights (Main File)"
        },
        {
            "filename": "tokenizer.json",
            "url": "https://huggingface.co/law-ai/InLegalBERT/resolve/main/tokenizer.json", 
            "description": "Tokenizer Configuration"
        },
        {
            "filename": "tokenizer_config.json",
            "url": "https://huggingface.co/law-ai/InLegalBERT/resolve/main/tokenizer_config.json",
            "description": "Tokenizer Settings"
        },
        {
            "filename": "vocab.txt",
            "url": "https://huggingface.co/law-ai/InLegalBERT/resolve/main/vocab.txt",
            "description": "Vocabulary File"
        }
    ]
    
    successful_downloads = 0
    
    for file_info in files_to_download:
        file_path = models_dir / file_info["filename"]
        
        # Skip if already exists and not empty
        if file_path.exists() and file_path.stat().st_size > 0:
            print(f"✅ Already exists: {file_info['description']}")
            successful_downloads += 1
            continue
        
        # Download file
        success = download_with_progress(
            file_info["url"],
            str(file_path),
            file_info["description"]
        )
        
        if success:
            successful_downloads += 1
        else:
            print(f"⚠️  Continuing without {file_info['description']}")
    
    print(f"\n📊 InLegalBERT Download Summary: {successful_downloads}/{len(files_to_download)} files")
    
    if successful_downloads >= 3:  # At least config, model, and tokenizer
        print("✅ InLegalBERT download successful!")
        return True
    else:
        print("⚠️  InLegalBERT download incomplete")
        return False

def download_sentence_transformer():
    """Download Sentence Transformer model"""
    print("\n🔤 DOWNLOADING SENTENCE TRANSFORMER")
    print("=" * 40)
    print("General purpose sentence embeddings")
    print("Size: ~90 MB")
    print()
    
    models_dir = Path("models/sentence-transformer")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    files = [
        {
            "filename": "config.json",
            "url": "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/config.json",
            "description": "Sentence Transformer Config"
        },
        {
            "filename": "pytorch_model.bin",
            "url": "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/pytorch_model.bin",
            "description": "Sentence Transformer Weights"
        }
    ]
    
    successful = 0
    for file_info in files:
        file_path = models_dir / file_info["filename"]
        
        if file_path.exists() and file_path.stat().st_size > 0:
            print(f"✅ Already exists: {file_info['description']}")
            successful += 1
            continue
        
        if download_with_progress(file_info["url"], str(file_path), file_info["description"]):
            successful += 1
    
    return successful >= 1

def create_model_info():
    """Create model information file"""
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    model_info = {
        "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "models": {
            "inlegalbert": {
                "name": "InLegalBERT",
                "description": "Indian Legal BERT for embeddings",
                "path": "models/inlegalbert",
                "ready": (models_dir / "inlegalbert" / "pytorch_model.bin").exists()
            },
            "sentence_transformer": {
                "name": "Sentence Transformer",
                "description": "General purpose embeddings",
                "path": "models/sentence-transformer", 
                "ready": (models_dir / "sentence-transformer" / "pytorch_model.bin").exists()
            }
        },
        "download_complete": True
    }
    
    info_file = models_dir / "model_info.json"
    with open(info_file, 'w') as f:
        json.dump(model_info, f, indent=2)
    
    print(f"\n📋 Model info saved to: {info_file}")

def main():
    """Main download function"""
    print("🤖 InLegalDesk AI Model Downloader")
    print("=" * 40)
    print()
    print("This will download AI models for enhanced legal research:")
    print("• InLegalBERT (420 MB) - Indian legal embeddings")
    print("• Sentence Transformer (90 MB) - General embeddings")
    print("• Total: ~510 MB")
    print()
    
    # Check if already downloaded
    inlegal_exists = Path("models/inlegalbert/pytorch_model.bin").exists()
    sentence_exists = Path("models/sentence-transformer/pytorch_model.bin").exists()
    
    if inlegal_exists and sentence_exists:
        print("✅ All models already downloaded!")
        print("🚀 Models are ready for use")
        return True
    
    print("📥 Starting model downloads...")
    print("This may take 10-20 minutes depending on internet speed")
    print()
    
    try:
        # Download InLegalBERT
        inlegal_success = download_inlegalbert()
        
        # Download Sentence Transformer
        sentence_success = download_sentence_transformer()
        
        # Create model info
        create_model_info()
        
        # Summary
        print("\n🎊 DOWNLOAD SUMMARY")
        print("=" * 20)
        
        if inlegal_success and sentence_success:
            print("✅ All models downloaded successfully!")
            print("🚀 InLegalDesk now has full AI capabilities")
            return True
        elif inlegal_success or sentence_success:
            print("⚠️  Some models downloaded - partial AI features available")
            return True
        else:
            print("❌ Model downloads failed - will use basic mode")
            return False
            
    except KeyboardInterrupt:
        print("\n👋 Download cancelled by user")
        return False
    except Exception as e:
        print(f"\n❌ Download error: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        
        if success:
            print("\n🎉 Model download completed!")
            print("You can now start InLegalDesk with full AI features")
        else:
            print("\n📋 InLegalDesk will work in basic mode")
            print("You can retry model download later")
        
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
    
    input("\nPress Enter to exit...")