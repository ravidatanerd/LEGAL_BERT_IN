"""
Pix2Struct extractor for document understanding
"""

import torch
from transformers import Pix2StructProcessor, Pix2StructForConditionalGeneration
from PIL import Image
import logging
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)

class Pix2StructExtractor(BaseExtractor):
    """Pix2Struct model for document text extraction"""
    
    def __init__(self, model_name: str = "google/pix2struct-docvqa-base"):
        super().__init__("pix2struct")
        self.model_name = model_name
        self.processor = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._initialized = False
    
    def _initialize(self):
        """Initialize the model (lazy loading)"""
        if self._initialized:
            return
        
        try:
            logger.info(f"Loading Pix2Struct model: {self.model_name}")
            self.processor = Pix2StructProcessor.from_pretrained(self.model_name)
            self.model = Pix2StructForConditionalGeneration.from_pretrained(self.model_name)
            self.model.to(self.device)
            self._initialized = True
            logger.info("Pix2Struct model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Pix2Struct model: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Pix2Struct is available"""
        try:
            if not self._initialized:
                self._initialize()
            return self._initialized and self.model is not None
        except Exception as e:
            logger.error(f"Pix2Struct availability check failed: {e}")
            return False
    
    async def extract_text(self, image: Image.Image) -> ExtractionResult:
        """Extract text using Pix2Struct"""
        if not self.is_available():
            raise RuntimeError("Pix2Struct model not available")
        
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
            logger.error(f"Error in Pix2Struct extraction: {e}")
            return ExtractionResult(
                text="",
                confidence=0.0,
                method=self.name,
                metadata={"error": str(e)}
            )
    
    def _extract_text_sync(self, image: Image.Image) -> ExtractionResult:
        """Synchronous text extraction"""
        try:
            # Prepare inputs
            inputs = self.processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate text
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    num_beams=1,
                    do_sample=False,
                    early_stopping=True
                )
            
            # Decode output
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # Calculate confidence (simplified)
            confidence = min(1.0, len(generated_text.strip()) / 100.0)
            
            return ExtractionResult(
                text=generated_text.strip(),
                confidence=confidence,
                method=self.name,
                metadata={
                    "model": self.model_name,
                    "device": self.device,
                    "text_length": len(generated_text)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in sync Pix2Struct extraction: {e}")
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