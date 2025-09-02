"""
PDF to image rendering utilities
"""

import io
import fitz  # PyMuPDF
import asyncio
from typing import List, Dict, Any
from PIL import Image
import numpy as np
from loguru import logger

class PDFImageRenderer:
    """High-quality PDF to image renderer"""
    
    def __init__(self, dpi: int = 300):
        self.dpi = dpi
        self.zoom = dpi / 72.0  # PyMuPDF uses 72 DPI as base
    
    async def render_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Render PDF pages to high-quality images"""
        try:
            # Open PDF document
            doc = fitz.open(pdf_path)
            pages = []
            
            for page_num in range(len(doc)):
                try:
                    # Get page
                    page = doc[page_num]
                    
                    # Create transformation matrix for high DPI
                    mat = fitz.Matrix(self.zoom, self.zoom)
                    
                    # Render page to pixmap
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    
                    # Convert to PIL Image
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    
                    # Convert to RGB if necessary
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    # Convert to numpy array for processing
                    img_array = np.array(image)
                    
                    pages.append({
                        "page_number": page_num + 1,
                        "image": img_array,
                        "width": image.width,
                        "height": image.height,
                        "dpi": self.dpi
                    })
                    
                    logger.debug(f"Rendered page {page_num + 1} ({image.width}x{image.height})")
                    
                except Exception as e:
                    logger.error(f"Failed to render page {page_num + 1}: {e}")
                    # Add empty page to maintain page numbering
                    pages.append({
                        "page_number": page_num + 1,
                        "image": None,
                        "error": str(e)
                    })
            
            doc.close()
            logger.info(f"Successfully rendered {len(pages)} pages from {pdf_path}")
            return pages
            
        except Exception as e:
            logger.error(f"Failed to render PDF {pdf_path}: {e}")
            raise
    
    async def render_page_range(self, pdf_path: str, start_page: int, end_page: int) -> List[Dict[str, Any]]:
        """Render specific page range from PDF"""
        try:
            doc = fitz.open(pdf_path)
            pages = []
            
            for page_num in range(start_page - 1, min(end_page, len(doc))):
                try:
                    page = doc[page_num]
                    mat = fitz.Matrix(self.zoom, self.zoom)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    img_array = np.array(image)
                    
                    pages.append({
                        "page_number": page_num + 1,
                        "image": img_array,
                        "width": image.width,
                        "height": image.height,
                        "dpi": self.dpi
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to render page {page_num + 1}: {e}")
                    pages.append({
                        "page_number": page_num + 1,
                        "image": None,
                        "error": str(e)
                    })
            
            doc.close()
            return pages
            
        except Exception as e:
            logger.error(f"Failed to render page range {start_page}-{end_page} from {pdf_path}: {e}")
            raise