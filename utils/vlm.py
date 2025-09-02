"""
Vision-Language Model utilities
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
import numpy as np
from loguru import logger

from .base import BaseExtractor

class VLMProcessor:
    """Vision-Language Model processor coordinator"""
    
    def __init__(self):
        self.extractors = []
        self._initialize_extractors()
    
    def _initialize_extractors(self):
        """Initialize available extractors"""
        vlm_order = os.getenv("VLM_ORDER", "donut,pix2struct,openai,tesseract_fallback").split(",")
        
        for vlm_type in vlm_order:
            vlm_type = vlm_type.strip()
            try:
                if vlm_type == "donut":
                    from extractors.donut import DonutExtractor
                    self.extractors.append(DonutExtractor())
                elif vlm_type == "pix2struct":
                    from extractors.pix2struct import Pix2StructExtractor
                    self.extractors.append(Pix2StructExtractor())
                elif vlm_type == "openai":
                    if os.getenv("OPENAI_API_KEY"):
                        from extractors.openai_vision import OpenAIVisionExtractor
                        self.extractors.append(OpenAIVisionExtractor())
                elif vlm_type == "tesseract_fallback":
                    if os.getenv("ENABLE_OCR_FALLBACK", "false").lower() == "true":
                        from extractors.tesseract_fallback import TesseractExtractor
                        self.extractors.append(TesseractExtractor())
            except Exception as e:
                logger.warning(f"Failed to initialize {vlm_type} extractor: {e}")
        
        logger.info(f"Initialized {len(self.extractors)} VLM extractors")
    
    async def extract_text(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract text using available extractors"""
        results = {
            "extractions": [],
            "best_text": "",
            "best_confidence": 0.0,
            "errors": []
        }
        
        for extractor in self.extractors:
            try:
                extraction = await extractor.extract_with_fallback(image)
                if extraction["success"] and extraction["text"].strip():
                    results["extractions"].append(extraction)
            except Exception as e:
                error_msg = f"{extractor.__class__.__name__} failed: {str(e)}"
                results["errors"].append(error_msg)
                logger.warning(error_msg)
        
        # Select best extraction
        if results["extractions"]:
            best_extraction = max(results["extractions"], key=lambda x: x.get("confidence", 0.0))
            results["best_text"] = best_extraction["text"]
            results["best_confidence"] = best_extraction.get("confidence", 0.0)
        
        return results