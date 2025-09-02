"""
Donut vision-language model extractor
"""
import logging
from typing import Dict, Any
from PIL import Image
import torch
from transformers import DonutProcessor, VisionEncoderDecoderModel

from .base import BaseExtractor

logger = logging.getLogger(__name__)

class DonutExtractor(BaseExtractor):
    """Donut-based document understanding extractor"""
    
    def __init__(self):
        super().__init__("donut")
        self.processor = None
        self.model = None
    
    async def initialize(self) -> bool:
        """Initialize Donut model"""
        try:
            logger.info("Initializing Donut extractor...")
            
            # Use a document understanding model
            model_name = "naver-clova-ix/donut-base-finetuned-docvqa"
            
            self.processor = DonutProcessor.from_pretrained(model_name)
            self.model = VisionEncoderDecoderModel.from_pretrained(model_name)
            
            # Move to GPU if available
            if torch.cuda.is_available():
                self.model = self.model.cuda()
                logger.info("Donut model moved to GPU")
            
            self.initialized = True
            logger.info("Donut extractor initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Donut: {e}")
            return False
    
    async def extract_text(self, image: Image.Image, page_num: int = 0) -> Dict[str, Any]:
        """Extract text using Donut model"""
        if not self.initialized:
            return {
                "text": "",
                "confidence": 0.0,
                "metadata": {"extractor": self.name, "error": "Not initialized"},
                "errors": ["Donut extractor not initialized"]
            }
        
        try:
            # Convert image to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Prepare inputs
            task_prompt = "<s_docvqa><s_question>What is the text content of this document?</s_question><s_answer>"
            decoder_input_ids = self.processor.tokenizer(
                task_prompt, 
                add_special_tokens=False, 
                return_tensors="pt"
            ).input_ids
            
            pixel_values = self.processor(image, return_tensors="pt").pixel_values
            
            # Move to GPU if available
            if torch.cuda.is_available():
                pixel_values = pixel_values.cuda()
                decoder_input_ids = decoder_input_ids.cuda()
            
            # Generate text
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
            
            # Decode the generated sequence
            sequence = outputs.sequences[0]
            decoded_text = self.processor.batch_decode([sequence], skip_special_tokens=True)[0]
            
            # Extract answer from the response
            if "<s_answer>" in decoded_text:
                text = decoded_text.split("<s_answer>")[-1].replace("</s_answer>", "").strip()
            else:
                text = decoded_text.strip()
            
            confidence = self.calculate_confidence(text)
            
            return {
                "text": text,
                "confidence": confidence,
                "metadata": {
                    "extractor": self.name,
                    "page_num": page_num,
                    "model": "donut-base-finetuned-docvqa"
                },
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"Donut extraction failed for page {page_num}: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "metadata": {"extractor": self.name, "page_num": page_num},
                "errors": [str(e)]
            }