"""
Tesseract OCR fallback extractor
"""

import os
import numpy as np
from PIL import Image
import pytesseract
from typing import Dict, Any
from loguru import logger

from .base import BaseExtractor

class TesseractExtractor(BaseExtractor):
    """Tesseract OCR as fallback extractor"""
    
    def __init__(self):
        super().__init__("Tesseract OCR")
        self.languages = "hin+eng"  # Hindi + English
        self.config = "--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,;:!?()[]{}\"'/-+*=&%$#@^~`|\\_<> "
    
    async def initialize(self) -> bool:
        """Initialize Tesseract OCR"""
        try:
            # Check if Tesseract is available
            pytesseract.get_tesseract_version()
            
            # Set language from environment
            self.languages = os.getenv("TESSERACT_LANG", "hin+eng")
            
            # Test OCR with a simple image
            test_image = Image.new('RGB', (100, 100), color='white')
            test_text = pytesseract.image_to_string(test_image, lang=self.languages)
            
            self.is_initialized = True
            logger.info(f"Tesseract OCR initialized with languages: {self.languages}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Tesseract OCR: {e}")
            return False
    
    async def extract_text(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract text using Tesseract OCR"""
        try:
            if not self.is_initialized:
                raise RuntimeError("Tesseract OCR not initialized")
            
            # Convert numpy array to PIL Image
            if image.dtype != np.uint8:
                image = (image * 255).astype(np.uint8)
            
            pil_image = Image.fromarray(image)
            
            # Preprocess image for better OCR
            processed_image = self._preprocess_for_ocr(pil_image)
            
            # Extract text with confidence scores
            data = pytesseract.image_to_data(
                processed_image, 
                lang=self.languages,
                config=self.config,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text
            text = pytesseract.image_to_string(
                processed_image, 
                lang=self.languages,
                config=self.config
            )
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / max(len(confidences), 1) / 100.0
            
            # Clean up text
            text = self._clean_ocr_text(text)
            
            return {
                "text": text,
                "confidence": avg_confidence,
                "metadata": {
                    "ocr_engine": "tesseract",
                    "languages": self.languages,
                    "word_count": len(data['text']),
                    "avg_word_confidence": avg_confidence
                }
            }
            
        except Exception as e:
            logger.error(f"Tesseract OCR extraction failed: {e}")
            raise
    
    def _preprocess_for_ocr(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        try:
            import cv2
            
            # Convert PIL to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert back to PIL Image
            processed_image = Image.fromarray(thresh)
            
            return processed_image
            
        except ImportError:
            # If OpenCV is not available, return original image
            logger.warning("OpenCV not available, skipping image preprocessing")
            return image
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}, using original image")
            return image
    
    def _clean_ocr_text(self, text: str) -> str:
        """Clean OCR output text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common OCR artifacts
        text = re.sub(r'[|]', 'I', text)  # Replace | with I
        text = re.sub(r'[0]', 'O', text)  # Replace 0 with O (context dependent)
        
        # Fix common OCR errors in legal documents
        ocr_fixes = {
            '§': 'Section',
            '¶': 'Paragraph',
            '†': 'Footnote',
            '‡': 'Footnote',
        }
        
        for wrong, correct in ocr_fixes.items():
            text = text.replace(wrong, correct)
        
        return text.strip()
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for Tesseract OCR"""
        # Tesseract works best with grayscale images
        if len(image.shape) == 3:
            # Convert RGB to grayscale
            gray = np.dot(image[...,:3], [0.2989, 0.5870, 0.1140])
            return gray.astype(np.uint8)
        elif len(image.shape) == 2:
            return image.astype(np.uint8)
        else:
            raise ValueError(f"Unsupported image shape for Tesseract: {image.shape}")