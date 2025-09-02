"""
OpenAI Vision API extractor
"""

import openai
import base64
import io
from PIL import Image
import logging
from typing import Optional
import asyncio

from .base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)

class OpenAIVisionExtractor(BaseExtractor):
    """OpenAI Vision API for document text extraction"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4-vision-preview"):
        super().__init__("openai_vision")
        self.api_key = api_key
        self.model = model
        self.client = None
        self._initialized = False
    
    def _initialize(self):
        """Initialize OpenAI client"""
        if self._initialized:
            return
        
        try:
            if not self.api_key:
                self.api_key = openai.api_key
            
            if not self.api_key:
                raise ValueError("OpenAI API key not provided")
            
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
            self._initialized = True
            logger.info("OpenAI Vision client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI Vision client: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if OpenAI Vision is available"""
        try:
            if not self._initialized:
                self._initialize()
            return self._initialized and self.client is not None
        except Exception as e:
            logger.error(f"OpenAI Vision availability check failed: {e}")
            return False
    
    async def extract_text(self, image: Image.Image) -> ExtractionResult:
        """Extract text using OpenAI Vision API"""
        if not self.is_available():
            raise RuntimeError("OpenAI Vision not available")
        
        try:
            # Convert image to base64
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Call OpenAI Vision API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text from this document image. Return only the extracted text without any additional commentary or formatting."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096,
                temperature=0.1
            )
            
            extracted_text = response.choices[0].message.content.strip()
            
            # Calculate confidence based on response length and structure
            confidence = min(1.0, len(extracted_text) / 200.0)
            
            return ExtractionResult(
                text=extracted_text,
                confidence=confidence,
                method=self.name,
                metadata={
                    "model": self.model,
                    "tokens_used": response.usage.total_tokens if response.usage else 0,
                    "text_length": len(extracted_text)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in OpenAI Vision extraction: {e}")
            return ExtractionResult(
                text="",
                confidence=0.0,
                method=self.name,
                metadata={"error": str(e)}
            )