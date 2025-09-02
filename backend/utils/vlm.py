"""
Vision-Language Model utilities and pipeline
"""

import os
import logging
from typing import List, Optional
from PIL import Image

from extractors.base import ExtractorPipeline
from extractors.donut import DonutExtractor
from extractors.pix2struct import Pix2StructExtractor
from extractors.openai_vision import OpenAIVisionExtractor
from extractors.tesseract_fallback import TesseractFallbackExtractor

logger = logging.getLogger(__name__)

class VLMPipeline:
    """Vision-Language Model pipeline for document extraction"""
    
    def __init__(self):
        self.extractors = []
        self.pipeline = None
        self._initialize_extractors()
    
    def _initialize_extractors(self):
        """Initialize extractors based on configuration"""
        vlm_order = os.getenv("VLM_ORDER", "donut,pix2struct,openai,tesseract_fallback")
        enable_ocr_fallback = os.getenv("ENABLE_OCR_FALLBACK", "false").lower() == "true"
        tesseract_lang = os.getenv("TESSERACT_LANG", "hin+eng")
        
        extractor_configs = vlm_order.split(',')
        
        for config in extractor_configs:
            config = config.strip()
            
            if config == "donut":
                try:
                    extractor = DonutExtractor()
                    if extractor.is_available():
                        self.extractors.append(extractor)
                        logger.info("Donut extractor added to pipeline")
                    else:
                        logger.warning("Donut extractor not available")
                except Exception as e:
                    logger.error(f"Failed to initialize Donut: {e}")
            
            elif config == "pix2struct":
                try:
                    extractor = Pix2StructExtractor()
                    if extractor.is_available():
                        self.extractors.append(extractor)
                        logger.info("Pix2Struct extractor added to pipeline")
                    else:
                        logger.warning("Pix2Struct extractor not available")
                except Exception as e:
                    logger.error(f"Failed to initialize Pix2Struct: {e}")
            
            elif config == "openai":
                try:
                    api_key = os.getenv("OPENAI_API_KEY")
                    if api_key:
                        extractor = OpenAIVisionExtractor(api_key=api_key)
                        if extractor.is_available():
                            self.extractors.append(extractor)
                            logger.info("OpenAI Vision extractor added to pipeline")
                        else:
                            logger.warning("OpenAI Vision extractor not available")
                    else:
                        logger.warning("OpenAI API key not provided")
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI Vision: {e}")
            
            elif config == "tesseract_fallback":
                if enable_ocr_fallback:
                    try:
                        extractor = TesseractFallbackExtractor(language=tesseract_lang)
                        if extractor.is_available():
                            self.extractors.append(extractor)
                            logger.info("Tesseract fallback extractor added to pipeline")
                        else:
                            logger.warning("Tesseract fallback extractor not available")
                    except Exception as e:
                        logger.error(f"Failed to initialize Tesseract: {e}")
                else:
                    logger.info("Tesseract fallback disabled")
        
        if not self.extractors:
            logger.error("No extractors available!")
            raise RuntimeError("No vision-language extractors available")
        
        # Create pipeline
        self.pipeline = ExtractorPipeline(self.extractors)
        logger.info(f"VLM pipeline initialized with {len(self.extractors)} extractors")
    
    async def extract_text_from_image(self, image: Image.Image, min_confidence: float = 0.5):
        """Extract text from a single image"""
        if not self.pipeline:
            raise RuntimeError("VLM pipeline not initialized")
        
        return await self.pipeline.extract_text(image, min_confidence)
    
    async def extract_text_from_images(self, images: List[Image.Image], min_confidence: float = 0.5):
        """Extract text from multiple images"""
        if not self.pipeline:
            raise RuntimeError("VLM pipeline not initialized")
        
        return await self.pipeline.extract_batch(images, min_confidence)
    
    def get_available_extractors(self) -> List[str]:
        """Get list of available extractor names"""
        return [extractor.name for extractor in self.extractors if extractor.is_available()]