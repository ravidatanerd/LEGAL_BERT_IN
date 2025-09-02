"""
PDF to image conversion utilities
"""

import fitz  # PyMuPDF
from PIL import Image
import io
import logging
from typing import List, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class PDFImageExtractor:
    """Extract images from PDF pages at high DPI"""
    
    def __init__(self, dpi: int = 300):
        self.dpi = dpi
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def extract_page_images(self, pdf_path: str) -> List[Image.Image]:
        """Extract all pages as PIL Images"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor, 
                self._extract_pages_sync, 
                pdf_path
            )
        except Exception as e:
            logger.error(f"Error extracting PDF images: {e}")
            raise
    
    def _extract_pages_sync(self, pdf_path: str) -> List[Image.Image]:
        """Synchronous PDF page extraction"""
        images = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Create transformation matrix for DPI
                mat = fitz.Matrix(self.dpi/72, self.dpi/72)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)
            
            doc.close()
            return images
            
        except Exception as e:
            logger.error(f"Error in sync PDF extraction: {e}")
            raise
    
    async def extract_single_page(self, pdf_path: str, page_num: int) -> Image.Image:
        """Extract a single page as PIL Image"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                self._extract_single_page_sync,
                pdf_path,
                page_num
            )
        except Exception as e:
            logger.error(f"Error extracting single page: {e}")
            raise
    
    def _extract_single_page_sync(self, pdf_path: str, page_num: int) -> Image.Image:
        """Synchronous single page extraction"""
        try:
            doc = fitz.open(pdf_path)
            page = doc.load_page(page_num)
            
            # Create transformation matrix for DPI
            mat = fitz.Matrix(self.dpi/72, self.dpi/72)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            doc.close()
            return img
            
        except Exception as e:
            logger.error(f"Error in sync single page extraction: {e}")
            raise