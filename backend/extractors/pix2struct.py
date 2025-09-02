"""
Pix2Struct vision-language model extractor
"""
import logging
from typing import Dict, Any
from PIL import Image
import torch
from transformers import Pix2StructForConditionalGeneration, Pix2StructProcessor

from .base import BaseExtractor

logger = logging.getLogger(__name__)

class Pix2StructExtractor(BaseExtractor):
    """Pix2Struct-based document understanding extractor"""
    
    def __init__(self):
        super().__init__("pix2struct")
        self.processor = None
        self.model = None
    
    async def initialize(self) -> bool:
        """Initialize Pix2Struct model"""
        try:
            logger.info("Initializing Pix2Struct extractor...")
            
            # Use DocVQA fine-tuned model
            model_name = "google/pix2struct-docvqa-large"
            
            self.processor = Pix2StructProcessor.from_pretrained(model_name)
            self.model = Pix2StructForConditionalGeneration.from_pretrained(model_name)
            
            # Move to GPU if available
            if torch.cuda.is_available():
                self.model = self.model.cuda()
                logger.info("Pix2Struct model moved to GPU")
            
            self.initialized = True
            logger.info("Pix2Struct extractor initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Pix2Struct: {e}")
            return False
    
    async def extract_text(self, image: Image.Image, page_num: int = 0) -> Dict[str, Any]:
        """Extract text using Pix2Struct model"""
        if not self.initialized:
            return {
                "text": "",
                "confidence": 0.0,
                "metadata": {"extractor": self.name, "error": "Not initialized"},
                "errors": ["Pix2Struct extractor not initialized"]
            }
        
        try:
            # Convert image to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Prepare question for document text extraction
            question = "What is all the text content in this document?"
            
            # Process inputs
            inputs = self.processor(
                images=image,
                text=question,
                return_tensors="pt"
            )
            
            # Move to GPU if available
            if torch.cuda.is_available():
                inputs = {k: v.cuda() if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
            
            # Generate text
            predictions = self.model.generate(
                **inputs,
                max_length=1024,
                num_beams=3,
                early_stopping=True
            )
            
            # Decode the generated text
            text = self.processor.decode(predictions[0], skip_special_tokens=True)
            
            confidence = self.calculate_confidence(text)
            
            return {
                "text": text,
                "confidence": confidence,
                "metadata": {
                    "extractor": self.name,
                    "page_num": page_num,
                    "model": "pix2struct-docvqa-large"
                },
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"Pix2Struct extraction failed for page {page_num}: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "metadata": {"extractor": self.name, "page_num": page_num},
                "errors": [str(e)]
            }