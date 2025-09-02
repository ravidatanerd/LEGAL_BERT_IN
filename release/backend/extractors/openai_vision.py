"""
OpenAI Vision API extractor
"""
import os
import base64
import logging
from typing import Dict, Any
from io import BytesIO
from PIL import Image
import httpx

from .base import BaseExtractor

logger = logging.getLogger(__name__)

class OpenAIVisionExtractor(BaseExtractor):
    """OpenAI Vision API based extractor"""
    
    def __init__(self):
        super().__init__("openai_vision")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = None
    
    async def initialize(self) -> bool:
        """Initialize OpenAI client"""
        try:
            if not self.api_key:
                logger.warning("OpenAI API key not provided")
                return False
            
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0),
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            self.initialized = True
            logger.info("OpenAI Vision extractor initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI Vision: {e}")
            return False
    
    def _encode_image(self, image: Image.Image) -> str:
        """Encode PIL Image to base64"""
        buffer = BytesIO()
        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(buffer, format="JPEG", quality=95)
        return base64.b64encode(buffer.getvalue()).decode()
    
    async def extract_text(self, image: Image.Image, page_num: int = 0) -> Dict[str, Any]:
        """Extract text using OpenAI Vision API"""
        if not self.initialized:
            return {
                "text": "",
                "confidence": 0.0,
                "metadata": {"extractor": self.name, "error": "Not initialized"},
                "errors": ["OpenAI Vision extractor not initialized"]
            }
        
        try:
            # Encode image
            base64_image = self._encode_image(image)
            
            # Prepare request
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text content from this document image. Preserve the original formatting, structure, and language (including Hindi/Devanagari text). Return only the extracted text without any additional commentary."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            # Make API call
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
            
            result = response.json()
            text = result["choices"][0]["message"]["content"].strip()
            
            confidence = self.calculate_confidence(text)
            
            return {
                "text": text,
                "confidence": confidence,
                "metadata": {
                    "extractor": self.name,
                    "page_num": page_num,
                    "model": self.model,
                    "usage": result.get("usage", {})
                },
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"OpenAI Vision extraction failed for page {page_num}: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "metadata": {"extractor": self.name, "page_num": page_num},
                "errors": [str(e)]
            }