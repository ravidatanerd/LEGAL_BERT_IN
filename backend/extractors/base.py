"""
Base extractor interface for vision-language models
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class ExtractionResult:
    """Result from text extraction"""
    
    def __init__(
        self, 
        text: str, 
        confidence: float, 
        method: str,
        metadata: Dict[str, Any] = None
    ):
        self.text = text
        self.confidence = confidence
        self.method = method
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"ExtractionResult(text='{self.text[:50]}...', confidence={self.confidence:.3f}, method='{self.method}')"

class BaseExtractor(ABC):
    """Base class for all text extractors"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    async def extract_text(self, image: Image.Image) -> ExtractionResult:
        """Extract text from image"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if extractor is available"""
        pass
    
    async def extract_batch(self, images: List[Image.Image]) -> List[ExtractionResult]:
        """Extract text from multiple images"""
        results = []
        for i, image in enumerate(images):
            try:
                result = await self.extract_text(image)
                results.append(result)
                self.logger.debug(f"Extracted from image {i}: {result.confidence:.3f} confidence")
            except Exception as e:
                self.logger.error(f"Error extracting from image {i}: {e}")
                # Create error result
                error_result = ExtractionResult(
                    text="",
                    confidence=0.0,
                    method=self.name,
                    metadata={"error": str(e)}
                )
                results.append(error_result)
        
        return results

class ExtractorPipeline:
    """Pipeline for running multiple extractors with fallback"""
    
    def __init__(self, extractors: List[BaseExtractor]):
        self.extractors = extractors
        self.logger = logging.getLogger(__name__)
    
    async def extract_text(
        self, 
        image: Image.Image, 
        min_confidence: float = 0.5
    ) -> ExtractionResult:
        """Extract text using best available extractor"""
        
        for extractor in self.extractors:
            if not extractor.is_available():
                self.logger.warning(f"Extractor {extractor.name} not available, skipping")
                continue
            
            try:
                result = await extractor.extract_text(image)
                if result.confidence >= min_confidence:
                    self.logger.info(f"Using {extractor.name} with confidence {result.confidence:.3f}")
                    return result
                else:
                    self.logger.warning(f"{extractor.name} confidence {result.confidence:.3f} below threshold {min_confidence}")
            except Exception as e:
                self.logger.error(f"Error with {extractor.name}: {e}")
                continue
        
        # If no extractor succeeded, return empty result
        self.logger.error("All extractors failed")
        return ExtractionResult(
            text="",
            confidence=0.0,
            method="none",
            metadata={"error": "All extractors failed"}
        )
    
    async def extract_batch(
        self, 
        images: List[Image.Image], 
        min_confidence: float = 0.5
    ) -> List[ExtractionResult]:
        """Extract text from multiple images"""
        results = []
        for i, image in enumerate(images):
            self.logger.info(f"Processing image {i+1}/{len(images)}")
            result = await self.extract_text(image, min_confidence)
            results.append(result)
        
        return results