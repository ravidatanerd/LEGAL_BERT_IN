#!/usr/bin/env python3
"""
InLegalDesk Model Downloader
Automatically downloads AI models on first run with progress indicators
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import urllib.request
import urllib.error
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelDownloader:
    """Downloads and manages AI models for InLegalDesk"""
    
    def __init__(self):
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        # Model configurations
        self.models_config = {
            "inlegalbert": {
                "name": "InLegalBERT",
                "description": "Indian Legal BERT model for embeddings",
                "size": "420 MB",
                "required": True,
                "huggingface_repo": "law-ai/InLegalBERT",
                "files": [
                    "config.json",
                    "pytorch_model.bin", 
                    "tokenizer.json",
                    "tokenizer_config.json",
                    "vocab.txt"
                ]
            },
            "sentence_transformer": {
                "name": "Sentence Transformer",
                "description": "General purpose sentence embeddings",
                "size": "90 MB",
                "required": True,
                "huggingface_repo": "sentence-transformers/all-MiniLM-L6-v2",
                "files": [
                    "config.json",
                    "pytorch_model.bin",
                    "tokenizer.json",
                    "tokenizer_config.json"
                ]
            },
            "legal_ner": {
                "name": "Legal NER",
                "description": "Legal Named Entity Recognition model",
                "size": "150 MB", 
                "required": False,
                "huggingface_repo": "law-ai/legal-ner",
                "files": [
                    "config.json",
                    "pytorch_model.bin",
                    "tokenizer.json"
                ]
            }
        }
        
        self.download_status = {}
        self.total_size = 0
        self.downloaded_size = 0
    
    def check_models_exist(self) -> Dict[str, bool]:
        """Check which models are already downloaded"""
        status = {}
        
        for model_id, config in self.models_config.items():
            model_dir = self.models_dir / model_id
            
            if model_dir.exists():
                # Check if all required files exist
                all_files_exist = all(
                    (model_dir / file_name).exists() 
                    for file_name in config["files"]
                )
                status[model_id] = all_files_exist
            else:
                status[model_id] = False
        
        return status
    
    def get_download_info(self) -> Dict[str, Any]:
        """Get information about what needs to be downloaded"""
        existing_models = self.check_models_exist()
        
        to_download = []
        total_size_mb = 0
        
        for model_id, config in self.models_config.items():
            if not existing_models[model_id]:
                to_download.append({
                    "id": model_id,
                    "name": config["name"],
                    "size": config["size"],
                    "required": config["required"]
                })
                
                # Parse size (rough estimate)
                size_str = config["size"].replace(" MB", "").replace(" GB", "000")
                try:
                    size_mb = int(size_str)
                    total_size_mb += size_mb
                except:
                    pass
        
        return {
            "models_to_download": to_download,
            "total_size_estimate": f"{total_size_mb} MB",
            "existing_models": existing_models,
            "download_required": len(to_download) > 0
        }
    
    def download_progress_hook(self, block_num: int, block_size: int, total_size: int):
        """Progress hook for urllib downloads"""
        if total_size > 0:
            downloaded = block_num * block_size
            percent = min(100, (downloaded * 100) // total_size)
            
            # Show progress every 5%
            if percent % 5 == 0:
                mb_downloaded = downloaded / (1024 * 1024)
                mb_total = total_size / (1024 * 1024)
                print(f"   Progress: {percent}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)")
    
    def download_file_from_huggingface(self, repo: str, filename: str, output_path: Path) -> bool:
        """Download file from Hugging Face Hub"""
        try:
            url = f"https://huggingface.co/{repo}/resolve/main/{filename}"
            
            print(f"📥 Downloading {filename}...")
            urllib.request.urlretrieve(url, output_path, self.download_progress_hook)
            
            if output_path.exists() and output_path.stat().st_size > 0:
                print(f"✅ Downloaded {filename}")
                return True
            else:
                print(f"❌ Download failed: {filename}")
                return False
                
        except urllib.error.URLError as e:
            print(f"❌ Network error downloading {filename}: {e}")
            return False
        except Exception as e:
            print(f"❌ Error downloading {filename}: {e}")
            return False
    
    def download_model(self, model_id: str) -> bool:
        """Download a specific model"""
        if model_id not in self.models_config:
            print(f"❌ Unknown model: {model_id}")
            return False
        
        config = self.models_config[model_id]
        model_dir = self.models_dir / model_id
        model_dir.mkdir(exist_ok=True)
        
        print(f"\n🤖 DOWNLOADING {config['name']}")
        print(f"📊 Size: {config['size']}")
        print(f"📁 Location: {model_dir}")
        print("-" * 50)
        
        success_count = 0
        total_files = len(config["files"])
        
        for filename in config["files"]:
            output_path = model_dir / filename
            
            # Skip if already exists
            if output_path.exists() and output_path.stat().st_size > 0:
                print(f"✅ Already exists: {filename}")
                success_count += 1
                continue
            
            # Download file
            if self.download_file_from_huggingface(config["huggingface_repo"], filename, output_path):
                success_count += 1
            else:
                # Try alternative download methods
                print(f"🔧 Trying alternative download for {filename}...")
                
                # Try without cache
                alt_url = f"https://huggingface.co/{config['huggingface_repo']}/resolve/main/{filename}?download=true"
                try:
                    urllib.request.urlretrieve(alt_url, output_path)
                    if output_path.exists() and output_path.stat().st_size > 0:
                        print(f"✅ Alternative download succeeded: {filename}")
                        success_count += 1
                    else:
                        print(f"❌ Alternative download failed: {filename}")
                except:
                    print(f"❌ All download methods failed: {filename}")
        
        # Check if download was successful
        success_rate = (success_count / total_files) * 100
        
        if success_rate >= 80:
            print(f"\n✅ {config['name']} downloaded successfully ({success_count}/{total_files} files)")
            
            # Create model info file
            info_file = model_dir / "model_info.json"
            with open(info_file, 'w') as f:
                json.dump({
                    "model_id": model_id,
                    "name": config["name"],
                    "downloaded_at": datetime.now().isoformat(),
                    "files_downloaded": success_count,
                    "total_files": total_files,
                    "success_rate": success_rate
                }, f, indent=2)
            
            return True
        else:
            print(f"\n❌ {config['name']} download incomplete ({success_count}/{total_files} files)")
            return False
    
    def download_all_models(self, required_only: bool = False) -> Dict[str, bool]:
        """Download all required models"""
        print("🤖 INLEGALDESK MODEL DOWNLOADER")
        print("=" * 40)
        print()
        
        # Check what's needed
        download_info = self.get_download_info()
        
        if not download_info["download_required"]:
            print("✅ All models already downloaded!")
            return download_info["existing_models"]
        
        print(f"📦 Models to download: {len(download_info['models_to_download'])}")
        print(f"📊 Estimated total size: {download_info['total_size_estimate']}")
        print()
        
        # Ask user for confirmation
        if not self._confirm_download(download_info):
            print("❌ Download cancelled by user")
            return download_info["existing_models"]
        
        # Download models
        results = {}
        
        for model_info in download_info["models_to_download"]:
            model_id = model_info["id"]
            
            if required_only and not model_info["required"]:
                print(f"⏭️  Skipping optional model: {model_info['name']}")
                results[model_id] = False
                continue
            
            try:
                results[model_id] = self.download_model(model_id)
            except Exception as e:
                print(f"❌ Failed to download {model_info['name']}: {e}")
                results[model_id] = False
        
        # Summary
        print("\n📊 DOWNLOAD SUMMARY")
        print("=" * 20)
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        print(f"✅ Successful: {successful}/{total} models")
        
        if successful == total:
            print("🎉 All models downloaded successfully!")
        elif successful > 0:
            print("⚠️  Some models downloaded - InLegalDesk will work with reduced features")
        else:
            print("❌ No models downloaded - will use basic mode only")
        
        return results
    
    def _confirm_download(self, download_info: Dict) -> bool:
        """Confirm download with user"""
        print("🔍 DOWNLOAD CONFIRMATION")
        print("-" * 25)
        
        for model in download_info["models_to_download"]:
            status = "REQUIRED" if model["required"] else "OPTIONAL"
            print(f"• {model['name']}: {model['size']} ({status})")
        
        print(f"\nTotal estimated size: {download_info['total_size_estimate']}")
        print("This may take 5-15 minutes depending on your internet speed.")
        print()
        
        try:
            response = input("Download models now? (Y/n): ").strip().lower()
            return response != 'n'
        except KeyboardInterrupt:
            return False
    
    def create_download_script(self):
        """Create standalone download script"""
        script_content = f'''#!/usr/bin/env python3
"""
Standalone Model Downloader for InLegalDesk
Run this script to download AI models manually
"""

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add current directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from model_downloader import ModelDownloader
        
        downloader = ModelDownloader()
        downloader.download_all_models()
        
        print("\\n🎊 Model download completed!")
        print("You can now start InLegalDesk with full AI features.")
        
    except ImportError as e:
        print(f"❌ Import error: {{e}}")
        print("Make sure you're running this from the working_backend directory")
    except Exception as e:
        print(f"❌ Download error: {{e}}")
    
    input("\\nPress Enter to exit...")
'''
        
        script_path = Path("download_models.py")
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        print(f"✅ Download script created: {script_path}")
        return script_path

def main():
    """Main function for standalone execution"""
    try:
        downloader = ModelDownloader()
        
        # Check current status
        existing_models = downloader.check_models_exist()
        print("📊 Current model status:")
        for model_id, exists in existing_models.items():
            config = downloader.models_config[model_id]
            status = "✅ Downloaded" if exists else "❌ Missing"
            print(f"   {config['name']}: {status}")
        
        # Download missing models
        if not all(existing_models.values()):
            print("\n🚀 Starting model download...")
            results = downloader.download_all_models()
        else:
            print("\n✅ All models already available!")
        
    except KeyboardInterrupt:
        print("\n👋 Download cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Model download error: {e}")

if __name__ == "__main__":
    main()