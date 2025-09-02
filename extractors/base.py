"""
Base class for vision-language model extractors
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import numpy as np
from loguru import logger

class BaseExtractor(ABC):
    """Base class for all vision-language extractors"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the extractor model"""
        pass
    
    @abstractmethod
    async def extract_text(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract text from image"""
        pass
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for the specific model"""
        # Default preprocessing - can be overridden
        if image is None:
            raise ValueError("Image is None")
        
        # Ensure image is in correct format
        if len(image.shape) == 3 and image.shape[2] == 3:
            # RGB image
            return image
        elif len(image.shape) == 2:
            # Grayscale image - convert to RGB
            return np.stack([image] * 3, axis=-1)
        else:
            raise ValueError(f"Unsupported image shape: {image.shape}")
    
    def _calculate_confidence(self, text: str, metadata: Dict[str, Any]) -> float:
        """Calculate confidence score for extracted text"""
        if not text or not text.strip():
            return 0.0
        
        # Basic confidence based on text length and character diversity
        text = text.strip()
        length_score = min(len(text) / 100, 1.0)  # Normalize to 0-1
        
        # Character diversity score
        unique_chars = len(set(text.lower()))
        diversity_score = min(unique_chars / 20, 1.0)  # Normalize to 0-1
        
        # Alphanumeric ratio
        alnum_count = sum(1 for c in text if c.isalnum())
        alnum_ratio = alnum_count / max(len(text), 1)
        
        # Combine scores
        confidence = (length_score * 0.3 + diversity_score * 0.3 + alnum_ratio * 0.4)
        return min(confidence, 1.0)
    
    def _postprocess_text(self, text: str) -> str:
        """Post-process extracted text"""
        if not text:
            return ""
        
        # Basic cleaning
        text = text.strip()
        
        # Remove excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    async def extract_with_fallback(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract text with error handling and fallback"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Preprocess image
            processed_image = self._preprocess_image(image)
            
            # Extract text
            result = await self.extract_text(processed_image)
            
            # Post-process text
            if "text" in result:
                result["text"] = self._postprocess_text(result["text"])
            
            # Calculate confidence if not provided
            if "confidence" not in result:
                result["confidence"] = self._calculate_confidence(
                    result.get("text", ""), 
                    result.get("metadata", {})
                )
            
            # Add extractor info
            result["extractor"] = self.name
            result["success"] = True
            
            return result
            
        except Exception as e:
            logger.error(f"{self.name} extraction failed: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "extractor": self.name,
                "success": False,
                "error": str(e)
            }