"""
Donut (Document Understanding Transformer) extractor
"""

import torch
import numpy as np
from PIL import Image
from typing import Dict, Any
from transformers import DonutProcessor, VisionEncoderDecoderModel
from loguru import logger

from .base import BaseExtractor

class DonutExtractor(BaseExtractor):
    """Donut model for document text extraction"""
    
    def __init__(self):
        super().__init__("Donut")
        self.processor = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    async def initialize(self) -> bool:
        """Initialize Donut model"""
        try:
            logger.info("Initializing Donut model...")
            
            # Load processor and model
            model_name = "naver-clova-ix/donut-base-finetuned-docvqa"
            self.processor = DonutProcessor.from_pretrained(model_name)
            self.model = VisionEncoderDecoderModel.from_pretrained(model_name)
            
            # Move to device
            self.model.to(self.device)
            self.model.eval()
            
            self.is_initialized = True
            logger.info(f"Donut model initialized on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Donut model: {e}")
            return False
    
    async def extract_text(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract text using Donut model"""
        try:
            if not self.is_initialized:
                raise RuntimeError("Donut model not initialized")
            
            # Convert numpy array to PIL Image
            if image.dtype != np.uint8:
                image = (image * 255).astype(np.uint8)
            
            pil_image = Image.fromarray(image)
            
            # Prepare task prompt
            task_prompt = "<s_docvqa><s_question>{user_input}</s_question><s_answer>"
            user_input = "What is the text content of this document?"
            
            # Process image and text
            decoder_input_ids = self.processor.tokenizer(
                task_prompt.replace("{user_input}", user_input),
                return_tensors="pt",
                add_special_tokens=False
            ).input_ids
            
            pixel_values = self.processor(pil_image, return_tensors="pt").pixel_values
            
            # Move to device
            pixel_values = pixel_values.to(self.device)
            decoder_input_ids = decoder_input_ids.to(self.device)
            
            # Generate text
            with torch.no_grad():
                outputs = self.model.generate(
                    pixel_values,
                    decoder_input_ids=decoder_input_ids,
                    max_length=self.model.decoder.config.max_position_embeddings,
                    early_stopping=True,
                    pad_token_id=self.processor.tokenizer.pad_token_id,
                    eos_token_id=self.processor.tokenizer.eos_token_id,
                    use_cache=True,
                    num_beams=1,
                    bad_words_ids=[[self.processor.tokenizer.unk_token_id]],
                    return_dict_in_generate=True,
                )
            
            # Decode output
            sequence = self.processor.batch_decode(outputs.sequences)[0]
            sequence = sequence.replace(self.processor.tokenizer.eos_token, "").replace(self.processor.tokenizer.pad_token, "")
            sequence = sequence.split("<s_answer>")[-1].split("</s_answer>")[0]
            
            # Clean up the extracted text
            text = sequence.strip()
            
            # Calculate confidence based on sequence probability
            confidence = self._calculate_donut_confidence(outputs)
            
            return {
                "text": text,
                "confidence": confidence,
                "metadata": {
                    "model": "donut",
                    "device": self.device,
                    "sequence_length": len(sequence)
                }
            }
            
        except Exception as e:
            logger.error(f"Donut extraction failed: {e}")
            raise
    
    def _calculate_donut_confidence(self, outputs) -> float:
        """Calculate confidence score for Donut output"""
        try:
            # Use sequence scores if available
            if hasattr(outputs, 'sequences_scores') and outputs.sequences_scores is not None:
                # Convert log probability to probability
                confidence = torch.exp(outputs.sequences_scores[0]).item()
                return min(confidence, 1.0)
            else:
                # Fallback to basic confidence
                return 0.8  # Donut is generally reliable
        except Exception:
            return 0.8
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for Donut model"""
        # Donut expects RGB images
        if len(image.shape) == 3 and image.shape[2] == 3:
            return image
        elif len(image.shape) == 2:
            # Convert grayscale to RGB
            return np.stack([image] * 3, axis=-1)
        else:
            raise ValueError(f"Unsupported image shape for Donut: {image.shape}")