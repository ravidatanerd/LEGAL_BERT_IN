"""
Base class for vision-language model extractors
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from PIL import Image

class BaseExtractor(ABC):
    """Base class for all VLM extractors"""
    
    def __init__(self, name: str):
        self.name = name
        self.initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the extractor model"""
        pass
    
    @abstractmethod
    async def extract_text(self, image: Image.Image, page_num: int = 0) -> Dict[str, Any]:
        """
        Extract text from an image
        
        Args:
            image: PIL Image object
            page_num: Page number for context
            
        Returns:
            Dict with keys: text, confidence, metadata, errors
        """
        pass
    
    def calculate_confidence(self, text: str) -> float:
        """
        Calculate confidence score based on text quality heuristics
        
        Args:
            text: Extracted text
            
        Returns:
            Confidence score between 0 and 1
        """
        if not text or not text.strip():
            return 0.0
        
        # Basic heuristics for text quality
        text = text.strip()
        total_chars = len(text)
        
        if total_chars == 0:
            return 0.0
        
        # Count alphanumeric characters (including Hindi)
        alnum_chars = sum(1 for c in text if c.isalnum() or ord(c) >= 0x0900)
        alnum_ratio = alnum_chars / total_chars
        
        # Count words (basic splitting)
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Penalize very short or very long average word length
        length_score = 1.0
        if avg_word_length < 2:
            length_score = 0.5
        elif avg_word_length > 15:
            length_score = 0.7
        
        # Combine factors
        confidence = min(1.0, alnum_ratio * length_score * min(1.0, len(words) / 10))
        
        return confidence