"""
Tesseract OCR fallback extractor
"""

import pytesseract
from PIL import Image
import logging
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os

from .base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)

class TesseractFallbackExtractor(BaseExtractor):
    """Tesseract OCR as fallback extractor"""
    
    def __init__(self, language: str = "hin+eng", tesseract_cmd: str = None):
        super().__init__("tesseract_fallback")
        self.language = language
        self.tesseract_cmd = tesseract_cmd
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._initialized = False
    
    def _initialize(self):
        """Initialize Tesseract"""
        if self._initialized:
            return
        
        try:
            # Set Tesseract command if provided
            if self.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            
            # Test Tesseract availability
            pytesseract.get_tesseract_version()
            
            # Test language availability
            available_langs = pytesseract.get_languages()
            required_langs = self.language.split('+')
            
            for lang in required_langs:
                if lang not in available_langs:
                    logger.warning(f"Language '{lang}' not available in Tesseract")
            
            self._initialized = True
            logger.info(f"Tesseract initialized with languages: {self.language}")
        except Exception as e:
            logger.error(f"Failed to initialize Tesseract: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Tesseract is available"""
        try:
            if not self._initialized:
                self._initialize()
            return self._initialized
        except Exception as e:
            logger.error(f"Tesseract availability check failed: {e}")
            return False
    
    async def extract_text(self, image: Image.Image) -> ExtractionResult:
        """Extract text using Tesseract OCR"""
        if not self.is_available():
            raise RuntimeError("Tesseract not available")
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._extract_text_sync,
                image
            )
            return result
        except Exception as e:
            logger.error(f"Error in Tesseract extraction: {e}")
            return ExtractionResult(
                text="",
                confidence=0.0,
                method=self.name,
                metadata={"error": str(e)}
            )
    
    def _extract_text_sync(self, image: Image.Image) -> ExtractionResult:
        """Synchronous text extraction"""
        try:
            # Configure Tesseract
            config = f'--oem 3 --psm 6 -l {self.language}'
            
            # Extract text with confidence
            data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
            
            # Combine text and calculate average confidence
            text_parts = []
            confidences = []
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                conf = int(data['conf'][i])
                
                if text and conf > 0:
                    text_parts.append(text)
                    confidences.append(conf)
            
            extracted_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            
            return ExtractionResult(
                text=extracted_text,
                confidence=avg_confidence,
                method=self.name,
                metadata={
                    "language": self.language,
                    "word_count": len(text_parts),
                    "avg_confidence": avg_confidence
                }
            )
            
        except Exception as e:
            logger.error(f"Error in sync Tesseract extraction: {e}")
            return ExtractionResult(
                text="",
                confidence=0.0,
                method=self.name,
                metadata={"error": str(e)}
            )
    
    def __del__(self):
        """Cleanup executor"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)