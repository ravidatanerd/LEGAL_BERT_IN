"""
PDF to image rendering utilities
"""
import asyncio
import logging
from typing import List
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

async def render_pdf_pages(file_path: str, dpi: int = 300) -> List[Image.Image]:
    """
    Render PDF pages to high-resolution images
    
    Args:
        file_path: Path to the PDF file
        dpi: Resolution for rendering (default 300 DPI)
        
    Returns:
        List of PIL Image objects, one per page
    """
    try:
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        images = await loop.run_in_executor(None, _render_pdf_sync, file_path, dpi)
        return images
        
    except Exception as e:
        logger.error(f"Failed to render PDF {file_path}: {e}")
        raise

def _render_pdf_sync(file_path: str, dpi: int) -> List[Image.Image]:
    """Synchronous PDF rendering function"""
    images = []
    
    try:
        # Open PDF
        doc = fitz.open(file_path)
        
        # Calculate zoom factor for desired DPI
        zoom = dpi / 72.0  # PDF default is 72 DPI
        mat = fitz.Matrix(zoom, zoom)
        
        for page_num in range(len(doc)):
            try:
                page = doc.load_page(page_num)
                
                # Render page to pixmap
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("ppm")
                image = Image.open(BytesIO(img_data))
                
                images.append(image)
                logger.debug(f"Rendered page {page_num + 1}/{len(doc)}")
                
            except Exception as e:
                logger.error(f"Failed to render page {page_num}: {e}")
                # Add a placeholder image or skip
                continue
        
        doc.close()
        logger.info(f"Successfully rendered {len(images)} pages from {Path(file_path).name}")
        
    except Exception as e:
        logger.error(f"Failed to open PDF {file_path}: {e}")
        raise
    
    return images