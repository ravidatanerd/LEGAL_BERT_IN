"""
AI Model Manager for InLegalDesk
Handles downloading, caching, and managing AI models for the installer
"""
import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import requests
from transformers import AutoTokenizer, AutoModel
import torch

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages AI model downloading and caching for offline use"""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # Model configurations
        self.models_config = {
            "inlegalbert": {
                "name": "law-ai/InLegalBERT",
                "type": "transformers",
                "required": True,
                "size_mb": 500,
                "description": "Legal domain embeddings for Indian law"
            },
            "t5-small": {
                "name": "t5-small",
                "type": "transformers",
                "required": False,
                "size_mb": 240,
                "description": "Encoder-decoder for structured generation"
            },
            "xlnet-base": {
                "name": "xlnet-base-cased",
                "type": "transformers", 
                "required": False,
                "size_mb": 460,
                "description": "Hybrid autoregressive + bidirectional model"
            }
        }
    
    def download_model(self, model_key: str, force_download: bool = False) -> bool:
        """Download and cache a specific model"""
        try:
            if model_key not in self.models_config:
                logger.error(f"Unknown model: {model_key}")
                return False
            
            config = self.models_config[model_key]
            model_path = self.models_dir / model_key
            
            # Check if already downloaded
            if model_path.exists() and not force_download:
                logger.info(f"Model {model_key} already cached")
                return True
            
            logger.info(f"Downloading {config['name']} (~{config['size_mb']}MB)...")
            
            # Download using transformers
            if config["type"] == "transformers":
                try:
                    # Download tokenizer and model
                    tokenizer = AutoTokenizer.from_pretrained(
                        config["name"],
                        cache_dir=str(model_path / "tokenizer")
                    )
                    
                    model = AutoModel.from_pretrained(
                        config["name"],
                        cache_dir=str(model_path / "model")
                    )
                    
                    # Save model info
                    model_info = {
                        "name": config["name"],
                        "type": config["type"],
                        "downloaded": True,
                        "path": str(model_path),
                        "size_mb": config["size_mb"]
                    }
                    
                    with open(model_path / "model_info.json", "w") as f:
                        json.dump(model_info, f, indent=2)
                    
                    logger.info(f"✅ Model {model_key} downloaded successfully")
                    return True
                    
                except Exception as e:
                    logger.error(f"Failed to download {model_key}: {e}")
                    return False
            
        except Exception as e:
            logger.error(f"Model download failed: {e}")
            return False
    
    def download_all_models(self, include_optional: bool = True) -> Dict[str, bool]:
        """Download all required models"""
        results = {}
        
        for model_key, config in self.models_config.items():
            if config["required"] or include_optional:
                logger.info(f"Downloading {model_key}...")
                results[model_key] = self.download_model(model_key)
            else:
                logger.info(f"Skipping optional model: {model_key}")
                results[model_key] = False
        
        return results
    
    def get_model_status(self) -> Dict[str, Dict]:
        """Get status of all models"""
        status = {}
        
        for model_key, config in self.models_config.items():
            model_path = self.models_dir / model_key
            
            if model_path.exists() and (model_path / "model_info.json").exists():
                try:
                    with open(model_path / "model_info.json", "r") as f:
                        model_info = json.load(f)
                    
                    status[model_key] = {
                        "downloaded": True,
                        "path": str(model_path),
                        "size_mb": config["size_mb"],
                        "required": config["required"]
                    }
                except Exception:
                    status[model_key] = {
                        "downloaded": False,
                        "error": "Corrupted cache",
                        "required": config["required"]
                    }
            else:
                status[model_key] = {
                    "downloaded": False,
                    "required": config["required"],
                    "size_mb": config["size_mb"]
                }
        
        return status
    
    def estimate_download_size(self, include_optional: bool = True) -> int:
        """Estimate total download size in MB"""
        total_size = 0
        
        for model_key, config in self.models_config.items():
            if config["required"] or include_optional:
                model_path = self.models_dir / model_key
                if not model_path.exists():
                    total_size += config["size_mb"]
        
        return total_size
    
    def create_offline_package(self, output_dir: str) -> bool:
        """Create offline model package for installer"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            # Download all models first
            logger.info("Downloading models for offline package...")
            results = self.download_all_models(include_optional=True)
            
            # Check if all required models downloaded
            required_models = [k for k, v in self.models_config.items() if v["required"]]
            missing_required = [k for k in required_models if not results.get(k, False)]
            
            if missing_required:
                logger.error(f"Missing required models: {missing_required}")
                return False
            
            # Copy models to output directory
            import shutil
            models_output = output_path / "models"
            if models_output.exists():
                shutil.rmtree(models_output)
            
            shutil.copytree(self.models_dir, models_output)
            
            # Create model manifest
            manifest = {
                "version": "1.0.0",
                "models": self.models_config,
                "download_results": results,
                "total_size_mb": sum(config["size_mb"] for config in self.models_config.values())
            }
            
            with open(output_path / "model_manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"✅ Offline model package created in {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create offline package: {e}")
            return False

def download_models_for_installer():
    """Download models for installer packaging"""
    print("📦 Downloading AI Models for Installer")
    print("=" * 40)
    
    manager = ModelManager("installer_models")
    
    # Get download estimate
    download_size = manager.estimate_download_size(include_optional=True)
    print(f"📊 Estimated download: ~{download_size}MB")
    
    if download_size > 0:
        response = input(f"Download {download_size}MB of AI models? (y/n): ")
        if response.lower() != 'y':
            print("⚠️  Skipping model download")
            return False
    
    # Download models
    print("🔄 Downloading models...")
    results = manager.download_all_models(include_optional=True)
    
    # Show results
    for model_key, success in results.items():
        config = manager.models_config[model_key]
        status = "✅" if success else "❌"
        required = "Required" if config["required"] else "Optional"
        print(f"{status} {model_key}: {config['description']} ({required})")
    
    # Create offline package
    print("\n📦 Creating offline package...")
    if manager.create_offline_package("installer/models_package"):
        print("✅ Offline model package created for installer")
        return True
    else:
        print("❌ Failed to create offline package")
        return False

if __name__ == "__main__":
    download_models_for_installer()