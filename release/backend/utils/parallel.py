"""
Parallel processing utilities for VLM extraction
"""
import asyncio
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

logger = logging.getLogger(__name__)

async def run_parallel_extraction(
    images: List[Image.Image],
    extractors: Dict[str, Any],
    max_workers: int = 4,
    page_offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Run parallel text extraction on multiple images using multiple extractors
    
    Args:
        images: List of PIL images to process
        extractors: Dict of initialized extractors
        max_workers: Maximum number of parallel workers
        page_offset: Page number offset for logging
        
    Returns:
        List of page extraction results
    """
    if not images or not extractors:
        return []
    
    try:
        # Process each page
        page_results = []
        
        for i, image in enumerate(images):
            page_num = i + page_offset
            
            # Run all extractors on this page
            page_extractions = await _extract_page_parallel(
                image, page_num, extractors, max_workers
            )
            
            page_results.append({
                "page_number": page_num,
                "extractions": page_extractions
            })
        
        return page_results
        
    except Exception as e:
        logger.error(f"Parallel extraction failed: {e}")
        raise

async def _extract_page_parallel(
    image: Image.Image,
    page_num: int,
    extractors: Dict[str, Any],
    max_workers: int
) -> List[Dict[str, Any]]:
    """Extract text from a single page using all available extractors"""
    
    # Create tasks for each extractor
    tasks = []
    for name, extractor in extractors.items():
        if extractor.initialized:
            task = asyncio.create_task(
                extractor.extract_text(image, page_num),
                name=f"{name}_page_{page_num}"
            )
            tasks.append((name, task))
    
    # Wait for all extractions to complete
    results = []
    for name, task in tasks:
        try:
            result = await task
            result["extractor_name"] = name
            results.append(result)
            
        except Exception as e:
            logger.error(f"Extractor {name} failed on page {page_num}: {e}")
            results.append({
                "text": "",
                "confidence": 0.0,
                "metadata": {"extractor": name, "page_num": page_num},
                "errors": [str(e)],
                "extractor_name": name
            })
    
    # Sort by confidence (best first)
    results.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    
    return results