"""
Pix2Struct extractor for document understanding
"""

import torch
import numpy as np
from PIL import Image
from typing import Dict, Any
from transformers import Pix2StructProcessor, Pix2StructForConditionalGeneration
from loguru import logger

from .base import BaseExtractor

class Pix2StructExtractor(BaseExtractor):
    """Pix2Struct model for document text extraction"""
    
    def __init__(self):
        super().__init__("Pix2Struct")
        self.processor = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    async def initialize(self) -> bool:
        """Initialize Pix2Struct model"""
        try:
            logger.info("Initializing Pix2Struct model...")
            
            # Load processor and model for document understanding
            model_name = "google/pix2struct-docvqa-base"
            self.processor = Pix2StructProcessor.from_pretrained(model_name)
            self.model = Pix2StructForConditionalGeneration.from_pretrained(model_name)
            
            # Move to device
            self.model.to(self.device)
            self.model.eval()
            
            self.is_initialized = True
            logger.info(f"Pix2Struct model initialized on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Pix2Struct model: {e}")
            return False
    
    async def extract_text(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract text using Pix2Struct model"""
        try:
            if not self.is_initialized:
                raise RuntimeError("Pix2Struct model not initialized")
            
            # Convert numpy array to PIL Image
            if image.dtype != np.uint8:
                image = (image * 255).astype(np.uint8)
            
            pil_image = Image.fromarray(image)
            
            # Prepare input
            inputs = self.processor(images=pil_image, return_tensors="pt")
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate text
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    num_beams=3,
                    early_stopping=True,
                    pad_token_id=self.processor.tokenizer.pad_token_id,
                    eos_token_id=self.processor.tokenizer.eos_token_id
                )
            
            # Decode output
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # Clean up the extracted text
            text = generated_text.strip()
            
            # Calculate confidence
            confidence = self._calculate_pix2struct_confidence(generated_ids, inputs)
            
            return {
                "text": text,
                "confidence": confidence,
                "metadata": {
                    "model": "pix2struct",
                    "device": self.device,
                    "generated_length": len(generated_text)
                }
            }
            
        except Exception as e:
            logger.error(f"Pix2Struct extraction failed: {e}")
            raise
    
    def _calculate_pix2struct_confidence(self, generated_ids, inputs) -> float:
        """Calculate confidence score for Pix2Struct output"""
        try:
            # Get model outputs for confidence calculation
            with torch.no_grad():
                outputs = self.model(**inputs, labels=generated_ids)
                
                # Calculate perplexity as inverse confidence
                if hasattr(outputs, 'loss') and outputs.loss is not None:
                    perplexity = torch.exp(outputs.loss).item()
                    # Convert perplexity to confidence (lower perplexity = higher confidence)
                    confidence = max(0.0, min(1.0, 1.0 / (1.0 + perplexity)))
                    return confidence
                else:
                    return 0.7  # Default confidence for Pix2Struct
        except Exception:
            return 0.7
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for Pix2Struct model"""
        # Pix2Struct expects RGB images
        if len(image.shape) == 3 and image.shape[2] == 3:
            return image
        elif len(image.shape) == 2:
            # Convert grayscale to RGB
            return np.stack([image] * 3, axis=-1)
        else:
            raise ValueError(f"Unsupported image shape for Pix2Struct: {image.shape}")