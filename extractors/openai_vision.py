"""
OpenAI Vision API extractor
"""

import os
import base64
import io
import numpy as np
from PIL import Image
from typing import Dict, Any
import openai
from loguru import logger

from .base import BaseExtractor

class OpenAIVisionExtractor(BaseExtractor):
    """OpenAI Vision API for document text extraction"""
    
    def __init__(self):
        super().__init__("OpenAI Vision")
        self.client = None
        self.model = "gpt-4-vision-preview"
    
    async def initialize(self) -> bool:
        """Initialize OpenAI client"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OpenAI API key not found")
                return False
            
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            
            self.client = openai.AsyncOpenAI(
                api_key=api_key,
                base_url=base_url
            )
            
            self.is_initialized = True
            logger.info("OpenAI Vision client initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI Vision client: {e}")
            return False
    
    async def extract_text(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract text using OpenAI Vision API"""
        try:
            if not self.is_initialized:
                raise RuntimeError("OpenAI Vision client not initialized")
            
            # Convert numpy array to base64 encoded image
            image_base64 = self._encode_image(image)
            
            # Prepare the prompt for legal document extraction
            prompt = """Extract all text content from this legal document image. 
            Preserve the original formatting, structure, and layout as much as possible.
            Include all text including headers, footers, page numbers, and any annotations.
            If the document contains mixed Hindi and English text, preserve both languages.
            Return only the extracted text without any additional commentary."""
            
            # Make API call
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096,
                temperature=0.1  # Low temperature for consistent extraction
            )
            
            # Extract text from response
            text = response.choices[0].message.content.strip()
            
            # Calculate confidence based on response characteristics
            confidence = self._calculate_openai_confidence(response, text)
            
            return {
                "text": text,
                "confidence": confidence,
                "metadata": {
                    "model": self.model,
                    "usage": response.usage.dict() if response.usage else {},
                    "finish_reason": response.choices[0].finish_reason
                }
            }
            
        except Exception as e:
            logger.error(f"OpenAI Vision extraction failed: {e}")
            raise
    
    def _encode_image(self, image: np.ndarray) -> str:
        """Convert numpy array to base64 encoded JPEG"""
        try:
            # Convert numpy array to PIL Image
            if image.dtype != np.uint8:
                image = (image * 255).astype(np.uint8)
            
            pil_image = Image.fromarray(image)
            
            # Convert to JPEG bytes
            buffer = io.BytesIO()
            pil_image.save(buffer, format='JPEG', quality=95)
            image_bytes = buffer.getvalue()
            
            # Encode to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            return image_base64
            
        except Exception as e:
            logger.error(f"Image encoding failed: {e}")
            raise
    
    def _calculate_openai_confidence(self, response, text: str) -> float:
        """Calculate confidence score for OpenAI Vision output"""
        try:
            # Base confidence for OpenAI Vision
            confidence = 0.9
            
            # Adjust based on finish reason
            if response.choices[0].finish_reason == "stop":
                confidence = 0.95
            elif response.choices[0].finish_reason == "length":
                confidence = 0.8  # May be truncated
            
            # Adjust based on text length and quality
            if len(text) < 50:
                confidence *= 0.8  # Very short text might be incomplete
            
            # Check for common error patterns
            error_patterns = [
                "I cannot see",
                "I'm unable to",
                "I don't see",
                "No text found",
                "Unable to extract"
            ]
            
            if any(pattern in text.lower() for pattern in error_patterns):
                confidence *= 0.3
            
            return min(confidence, 1.0)
            
        except Exception:
            return 0.9  # Default high confidence for OpenAI Vision
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for OpenAI Vision API"""
        # OpenAI Vision can handle various image formats
        if len(image.shape) == 3 and image.shape[2] == 3:
            return image
        elif len(image.shape) == 2:
            # Convert grayscale to RGB
            return np.stack([image] * 3, axis=-1)
        else:
            raise ValueError(f"Unsupported image shape for OpenAI Vision: {image.shape}")