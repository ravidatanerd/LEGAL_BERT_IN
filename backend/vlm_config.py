"""
Advanced VLM (Vision-Language Model) Configuration System
Provides user-friendly options for configuring document extraction models
"""
import os
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class VLMQuality(Enum):
    """VLM Quality levels with different speed/accuracy tradeoffs"""
    PREMIUM = "premium"      # Best quality, requires OpenAI API
    HIGH = "high"           # Good quality, mix of API and local models
    BALANCED = "balanced"   # Balance of speed and quality
    FAST = "fast"          # Prioritize speed over quality
    OFFLINE = "offline"    # No API calls, local models only
    BASIC = "basic"        # OCR only, fastest but lowest quality

class VLMPreset:
    """Predefined VLM configurations for different use cases"""
    
    PRESETS = {
        VLMQuality.PREMIUM: {
            "order": ["openai", "tesseract_fallback"],
            "description": "Best quality using OpenAI Vision API (requires API key)",
            "requirements": ["OPENAI_API_KEY"],
            "cost": "High (API calls)",
            "speed": "Fast",
            "accuracy": "Excellent"
        },
        
        VLMQuality.HIGH: {
            "order": ["openai", "donut", "pix2struct", "tesseract_fallback"],
            "description": "High quality with fallbacks (OpenAI first, then local models)",
            "requirements": ["OPENAI_API_KEY recommended"],
            "cost": "Medium (API + compute)",
            "speed": "Medium",
            "accuracy": "Very Good"
        },
        
        VLMQuality.BALANCED: {
            "order": ["donut", "openai", "pix2struct", "tesseract_fallback"],
            "description": "Balanced approach (local models first, API fallback)",
            "requirements": ["GPU recommended"],
            "cost": "Medium (mostly compute)",
            "speed": "Medium",
            "accuracy": "Good"
        },
        
        VLMQuality.FAST: {
            "order": ["tesseract_fallback", "openai"],
            "description": "Prioritize speed (OCR first, API fallback)",
            "requirements": ["Tesseract OCR"],
            "cost": "Low",
            "speed": "Very Fast",
            "accuracy": "Basic to Good"
        },
        
        VLMQuality.OFFLINE: {
            "order": ["donut", "pix2struct", "tesseract_fallback"],
            "description": "No API calls, local models only",
            "requirements": ["GPU recommended", "Local models"],
            "cost": "Low (compute only)",
            "speed": "Slow to Medium",
            "accuracy": "Good"
        },
        
        VLMQuality.BASIC: {
            "order": ["tesseract_fallback"],
            "description": "OCR only, fastest processing",
            "requirements": ["Tesseract OCR"],
            "cost": "Very Low",
            "speed": "Very Fast",
            "accuracy": "Basic"
        }
    }

class VLMConfigurator:
    """Advanced VLM configuration with user-friendly options"""
    
    def __init__(self):
        self.current_preset = None
        self.custom_order = None
        
    def get_available_models(self) -> Dict[str, Dict]:
        """Get information about available VLM models"""
        return {
            "openai": {
                "name": "OpenAI Vision API",
                "description": "GPT-4 Vision for document understanding",
                "requirements": ["OPENAI_API_KEY"],
                "quality": "Excellent",
                "speed": "Fast",
                "cost": "API calls ($0.01-0.02 per image)",
                "offline": False
            },
            "donut": {
                "name": "Donut (Document Understanding)",
                "description": "Transformer-based document AI model",
                "requirements": ["GPU recommended", "~2GB VRAM"],
                "quality": "Very Good",
                "speed": "Medium",
                "cost": "Free (compute)",
                "offline": True
            },
            "pix2struct": {
                "name": "Pix2Struct",
                "description": "Google's image-to-text model",
                "requirements": ["GPU recommended", "~1GB VRAM"],
                "quality": "Good",
                "speed": "Medium",
                "cost": "Free (compute)",
                "offline": True
            },
            "tesseract_fallback": {
                "name": "Tesseract OCR",
                "description": "Traditional OCR with basic text extraction",
                "requirements": ["Tesseract installation"],
                "quality": "Basic",
                "speed": "Very Fast",
                "cost": "Free",
                "offline": True
            }
        }
    
    def get_preset_info(self, quality: VLMQuality) -> Dict:
        """Get detailed information about a quality preset"""
        return self.PRESETS.get(quality, {})
    
    def set_preset(self, quality: VLMQuality) -> List[str]:
        """Set VLM configuration using a quality preset"""
        preset = self.PRESETS.get(quality)
        if not preset:
            raise ValueError(f"Unknown quality preset: {quality}")
        
        self.current_preset = quality
        self.custom_order = None
        
        logger.info(f"VLM preset set to {quality.value}: {preset['description']}")
        return preset["order"]
    
    def set_custom_order(self, model_order: List[str]) -> List[str]:
        """Set custom VLM model order"""
        available_models = set(self.get_available_models().keys())
        invalid_models = [m for m in model_order if m not in available_models]
        
        if invalid_models:
            raise ValueError(f"Invalid models: {invalid_models}. Available: {list(available_models)}")
        
        self.current_preset = None
        self.custom_order = model_order
        
        logger.info(f"Custom VLM order set: {' → '.join(model_order)}")
        return model_order
    
    def get_current_configuration(self) -> Tuple[List[str], Dict]:
        """Get current VLM configuration with details"""
        if self.custom_order:
            return self.custom_order, {"type": "custom", "order": self.custom_order}
        elif self.current_preset:
            preset = self.PRESETS[self.current_preset]
            return preset["order"], {"type": "preset", "preset": self.current_preset.value, **preset}
        else:
            # Default configuration
            default_order = self._get_default_order()
            return default_order, {"type": "default", "order": default_order}
    
    def _get_default_order(self) -> List[str]:
        """Get default VLM order based on available resources"""
        # Check if OpenAI API key is available
        if os.getenv("OPENAI_API_KEY"):
            return ["openai", "donut", "pix2struct", "tesseract_fallback"]
        else:
            return ["donut", "pix2struct", "tesseract_fallback"]
    
    def validate_configuration(self, model_order: List[str]) -> Dict[str, bool]:
        """Validate if the VLM configuration can work with current environment"""
        validation = {}
        
        for model in model_order:
            if model == "openai":
                validation[model] = bool(os.getenv("OPENAI_API_KEY"))
            elif model == "tesseract_fallback":
                validation[model] = bool(os.getenv("ENABLE_OCR_FALLBACK", "true").lower() == "true")
            elif model in ["donut", "pix2struct"]:
                # These require transformers and torch
                try:
                    import torch
                    import transformers
                    validation[model] = True
                except ImportError:
                    validation[model] = False
            else:
                validation[model] = False
        
        return validation
    
    def get_recommendations(self) -> Dict[str, str]:
        """Get VLM configuration recommendations based on environment"""
        recommendations = {}
        
        # Check available resources
        has_openai_key = bool(os.getenv("OPENAI_API_KEY"))
        has_gpu = self._check_gpu_availability()
        has_transformers = self._check_transformers_availability()
        
        if has_openai_key:
            if has_transformers:
                recommendations["recommended"] = "HIGH quality preset (OpenAI + local models)"
                recommendations["preset"] = VLMQuality.HIGH.value
            else:
                recommendations["recommended"] = "PREMIUM quality preset (OpenAI only)"
                recommendations["preset"] = VLMQuality.PREMIUM.value
        elif has_transformers:
            if has_gpu:
                recommendations["recommended"] = "OFFLINE quality preset (local models with GPU)"
                recommendations["preset"] = VLMQuality.OFFLINE.value
            else:
                recommendations["recommended"] = "BALANCED quality preset (local models, CPU)"
                recommendations["preset"] = VLMQuality.BALANCED.value
        else:
            recommendations["recommended"] = "BASIC quality preset (OCR only)"
            recommendations["preset"] = VLMQuality.BASIC.value
        
        return recommendations
    
    def _check_gpu_availability(self) -> bool:
        """Check if GPU is available for local models"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _check_transformers_availability(self) -> bool:
        """Check if transformers library is available"""
        try:
            import transformers
            return True
        except ImportError:
            return False

# Global configurator instance
vlm_configurator = VLMConfigurator()

def get_vlm_order_from_env() -> List[str]:
    """Get VLM order from environment with advanced configuration support"""
    # Check for preset configuration first
    preset_name = os.getenv("VLM_PRESET")
    if preset_name:
        try:
            preset = VLMQuality(preset_name.lower())
            order = vlm_configurator.set_preset(preset)
            logger.info(f"Using VLM preset '{preset_name}': {' → '.join(order)}")
            return order
        except ValueError:
            logger.warning(f"Invalid VLM preset: {preset_name}, falling back to VLM_ORDER")
    
    # Check for custom order
    vlm_order_env = os.getenv("VLM_ORDER")
    if vlm_order_env:
        custom_order = [model.strip() for model in vlm_order_env.split(",")]
        try:
            order = vlm_configurator.set_custom_order(custom_order)
            logger.info(f"Using custom VLM order: {' → '.join(order)}")
            return order
        except ValueError as e:
            logger.warning(f"Invalid VLM_ORDER: {e}, using default")
    
    # Use default based on available resources
    default_order = vlm_configurator._get_default_order()
    logger.info(f"Using default VLM order: {' → '.join(default_order)}")
    return default_order

def get_vlm_configuration_info() -> Dict:
    """Get comprehensive VLM configuration information for users"""
    order, config = vlm_configurator.get_current_configuration()
    validation = vlm_configurator.validate_configuration(order)
    recommendations = vlm_configurator.get_recommendations()
    available_models = vlm_configurator.get_available_models()
    
    return {
        "current_order": order,
        "configuration": config,
        "validation": validation,
        "recommendations": recommendations,
        "available_models": available_models,
        "presets": {quality.value: preset for quality, preset in VLMPreset.PRESETS.items()}
    }