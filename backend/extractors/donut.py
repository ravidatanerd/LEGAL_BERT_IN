"""
Donut extractor for document understanding
"""

import torch
from transformers import DonutProcessor, VisionEncoderDecoderModel
from PIL import Image
import logging
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)

class DonutExtractor(BaseExtractor):
    """Donut model for document text extraction"""
    
    def __init__(self, model_name: str = "naver-clova-ix/donut-base-finetuned-docvqa"):
        super().__init__("donut")
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
            logger.info(f"Loading Donut model: {self.model_name}")
            self.processor = DonutProcessor.from_pretrained(self.model_name)
            self.model = VisionEncoderDecoderModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self._initialized = True
            logger.info("Donut model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Donut model: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Donut is available"""
        try:
            if not self._initialized:
                self._initialize()
            return self._initialized and self.model is not None
        except Exception as e:
            logger.error(f"Donut availability check failed: {e}")
            return False
    
    async def extract_text(self, image: Image.Image) -> ExtractionResult:
        """Extract text using Donut"""
        if not self.is_available():
            raise RuntimeError("Donut model not available")
        
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
            logger.error(f"Error in Donut extraction: {e}")
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
            pixel_values = self.processor(image, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)
            
            # Generate text
            with torch.no_grad():
                task_prompt = "<s_docvqa><s_question>{user_input}</s_question><s_answer>"
                decoder_input_ids = self.processor.tokenizer(
                    task_prompt, 
                    return_tensors="pt", 
                    add_special_tokens=False
                ).input_ids
                decoder_input_ids = decoder_input_ids.to(self.device)
                
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
            
            # Calculate confidence (simplified)
            confidence = min(1.0, len(sequence.strip()) / 100.0)
            
            return ExtractionResult(
                text=sequence.strip(),
                confidence=confidence,
                method=self.name,
                metadata={
                    "model": self.model_name,
                    "device": self.device,
                    "sequence_length": len(sequence)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in sync Donut extraction: {e}")
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