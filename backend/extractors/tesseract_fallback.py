"""
Tesseract OCR fallback extractor
"""
import logging
import os
from typing import Dict, Any
from PIL import Image
import pytesseract
import cv2
import numpy as np

from .base import BaseExtractor

logger = logging.getLogger(__name__)

class TesseractExtractor(BaseExtractor):
    """Tesseract OCR fallback extractor"""
    
    def __init__(self):
        super().__init__("tesseract_fallback")
        self.lang = os.getenv("TESSERACT_LANG", "hin+eng")
    
    async def initialize(self) -> bool:
        """Initialize Tesseract"""
        try:
            # Test if tesseract is available
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Tesseract: {e}")
            return False
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        try:
            # Convert PIL to OpenCV
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert back to PIL
            return Image.fromarray(thresh)
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image
    
    async def extract_text(self, image: Image.Image, page_num: int = 0) -> Dict[str, Any]:
        """Extract text using Tesseract OCR"""
        if not self.initialized:
            return {
                "text": "",
                "confidence": 0.0,
                "metadata": {"extractor": self.name, "error": "Not initialized"},
                "errors": ["Tesseract extractor not initialized"]
            }
        
        try:
            # Preprocess image
            processed_image = self._preprocess_image(image)
            
            # Configure Tesseract
            config = f"--oem 3 --psm 6 -l {self.lang}"
            
            # Extract text
            text = pytesseract.image_to_string(processed_image, config=config)
            
            # Get confidence data
            try:
                data = pytesseract.image_to_data(
                    processed_image, 
                    config=config, 
                    output_type=pytesseract.Output.DICT
                )
                
                # Calculate average confidence
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                normalized_confidence = avg_confidence / 100.0  # Tesseract gives 0-100
                
            except Exception:
                normalized_confidence = self.calculate_confidence(text)
            
            return {
                "text": text.strip(),
                "confidence": normalized_confidence,
                "metadata": {
                    "extractor": self.name,
                    "page_num": page_num,
                    "language": self.lang,
                    "tesseract_confidence": avg_confidence if 'avg_confidence' in locals() else None
                },
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"Tesseract extraction failed for page {page_num}: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "metadata": {"extractor": self.name, "page_num": page_num},
                "errors": [str(e)]
            }