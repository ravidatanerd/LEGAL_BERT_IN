"""
Offline Model Loader for InLegalDesk
Loads AI models from bundled installer package or downloads if needed
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import torch
from transformers import AutoTokenizer, AutoModel, T5Tokenizer, T5ForConditionalGeneration
from transformers import XLNetTokenizer, XLNetLMHeadModel

logger = logging.getLogger(__name__)

class OfflineModelLoader:
    """Loads AI models from bundled package or downloads as fallback"""
    
    def __init__(self):
        # Check for bundled models (from installer)
        self.bundled_models_dir = self._find_bundled_models()
        self.cache_dir = Path("models_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Model loading status
        self.loaded_models = {}
        self.loading_progress = {}
    
    def _find_bundled_models(self) -> Optional[Path]:
        """Find bundled models directory from installer"""
        possible_paths = [
            Path("models"),  # Bundled with installer
            Path("../models"),  # Relative to backend
            Path("installer/models_package/models"),  # Development
            Path("models_package/models"),  # Alternative
        ]
        
        for path in possible_paths:
            if path.exists() and (path / "model_manifest.json").exists():
                logger.info(f"Found bundled models at: {path}")
                return path
        
        logger.info("No bundled models found - will download as needed")
        return None
    
    def load_inlegalbert(self) -> Tuple[Optional[Any], Optional[Any]]:
        """Load InLegalBERT model (required for core functionality)"""
        try:
            model_name = "law-ai/InLegalBERT"
            
            # Try bundled model first
            if self.bundled_models_dir:
                bundled_path = self.bundled_models_dir / "inlegalbert"
                if bundled_path.exists():
                    logger.info("Loading InLegalBERT from bundled package...")
                    try:
                        tokenizer = AutoTokenizer.from_pretrained(str(bundled_path / "tokenizer"))
                        model = AutoModel.from_pretrained(str(bundled_path / "model"))
                        logger.info("✅ InLegalBERT loaded from bundled package")
                        return tokenizer, model
                    except Exception as e:
                        logger.warning(f"Bundled InLegalBERT failed: {e}, trying download...")
            
            # Fallback to download
            logger.info("Downloading InLegalBERT from Hugging Face...")
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=str(self.cache_dir / "inlegalbert")
            )
            model = AutoModel.from_pretrained(
                model_name,
                cache_dir=str(self.cache_dir / "inlegalbert")
            )
            
            logger.info("✅ InLegalBERT downloaded and loaded")
            return tokenizer, model
            
        except Exception as e:
            logger.error(f"Failed to load InLegalBERT: {e}")
            return None, None
    
    def load_t5_model(self) -> Tuple[Optional[Any], Optional[Any]]:
        """Load T5 model for structured generation"""
        try:
            model_name = "t5-small"
            
            # Try bundled model first
            if self.bundled_models_dir:
                bundled_path = self.bundled_models_dir / "t5-small"
                if bundled_path.exists():
                    logger.info("Loading T5 from bundled package...")
                    try:
                        tokenizer = T5Tokenizer.from_pretrained(str(bundled_path / "tokenizer"))
                        model = T5ForConditionalGeneration.from_pretrained(str(bundled_path / "model"))
                        logger.info("✅ T5 loaded from bundled package")
                        return tokenizer, model
                    except Exception as e:
                        logger.warning(f"Bundled T5 failed: {e}, trying download...")
            
            # Fallback to download
            logger.info("Downloading T5 model...")
            tokenizer = T5Tokenizer.from_pretrained(
                model_name,
                cache_dir=str(self.cache_dir / "t5")
            )
            model = T5ForConditionalGeneration.from_pretrained(
                model_name,
                cache_dir=str(self.cache_dir / "t5")
            )
            
            logger.info("✅ T5 downloaded and loaded")
            return tokenizer, model
            
        except Exception as e:
            logger.warning(f"T5 model unavailable: {e}")
            return None, None
    
    def load_xlnet_model(self) -> Tuple[Optional[Any], Optional[Any]]:
        """Load XLNet model for hybrid processing"""
        try:
            model_name = "xlnet-base-cased"
            
            # Try bundled model first
            if self.bundled_models_dir:
                bundled_path = self.bundled_models_dir / "xlnet-base"
                if bundled_path.exists():
                    logger.info("Loading XLNet from bundled package...")
                    try:
                        tokenizer = XLNetTokenizer.from_pretrained(str(bundled_path / "tokenizer"))
                        model = XLNetLMHeadModel.from_pretrained(str(bundled_path / "model"))
                        logger.info("✅ XLNet loaded from bundled package")
                        return tokenizer, model
                    except Exception as e:
                        logger.warning(f"Bundled XLNet failed: {e}, trying download...")
            
            # Fallback to download
            logger.info("Downloading XLNet model...")
            tokenizer = XLNetTokenizer.from_pretrained(
                model_name,
                cache_dir=str(self.cache_dir / "xlnet")
            )
            model = XLNetLMHeadModel.from_pretrained(
                model_name,
                cache_dir=str(self.cache_dir / "xlnet")
            )
            
            logger.info("✅ XLNet downloaded and loaded")
            return tokenizer, model
            
        except Exception as e:
            logger.warning(f"XLNet model unavailable: {e}")
            return None, None
    
    def get_bundled_model_info(self) -> Dict[str, Any]:
        """Get information about bundled models"""
        if not self.bundled_models_dir or not (self.bundled_models_dir / "model_manifest.json").exists():
            return {"bundled": False, "models": {}}
        
        try:
            with open(self.bundled_models_dir / "model_manifest.json", "r") as f:
                manifest = json.load(f)
            
            return {
                "bundled": True,
                "models": manifest.get("models", {}),
                "total_size_mb": manifest.get("total_size_mb", 0),
                "version": manifest.get("version", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Failed to read model manifest: {e}")
            return {"bundled": False, "error": str(e)}
    
    def initialize_all_models(self) -> Dict[str, bool]:
        """Initialize all available models"""
        results = {}
        
        print("🤖 Initializing AI Models...")
        
        # Load InLegalBERT (required)
        print("📋 Loading InLegalBERT...")
        tokenizer, model = self.load_inlegalbert()
        results["inlegalbert"] = (tokenizer is not None and model is not None)
        
        if results["inlegalbert"]:
            self.loaded_models["inlegalbert"] = {"tokenizer": tokenizer, "model": model}
            print("✅ InLegalBERT ready")
        else:
            print("❌ InLegalBERT failed - core functionality limited")
        
        # Load T5 (optional)
        print("📋 Loading T5...")
        tokenizer, model = self.load_t5_model()
        results["t5"] = (tokenizer is not None and model is not None)
        
        if results["t5"]:
            self.loaded_models["t5"] = {"tokenizer": tokenizer, "model": model}
            print("✅ T5 ready")
        else:
            print("⚠️  T5 unavailable - structured generation limited")
        
        # Load XLNet (optional)
        print("📋 Loading XLNet...")
        tokenizer, model = self.load_xlnet_model()
        results["xlnet"] = (tokenizer is not None and model is not None)
        
        if results["xlnet"]:
            self.loaded_models["xlnet"] = {"tokenizer": tokenizer, "model": model}
            print("✅ XLNet ready")
        else:
            print("⚠️  XLNet unavailable - hybrid processing limited")
        
        # Summary
        loaded_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        print(f"\n📊 Model Loading Summary: {loaded_count}/{total_count} models loaded")
        
        if results["inlegalbert"]:
            print("✅ Core functionality available")
        else:
            print("⚠️  Limited functionality - InLegalBERT required")
        
        return results

# Global instance
model_loader = OfflineModelLoader()