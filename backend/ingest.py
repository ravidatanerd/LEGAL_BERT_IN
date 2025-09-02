"""
Document ingestion with vision-language models for OCR-free PDF extraction
"""
import os
import asyncio
import uuid
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import fitz  # PyMuPDF
from PIL import Image
import numpy as np

from utils.pdf_images import render_pdf_pages
from utils.textnorm import normalize_text
from utils.parallel import run_parallel_extraction
from extractors.base import BaseExtractor
from vlm_config import get_vlm_order_from_env, get_vlm_configuration_info
from extractors.donut import DonutExtractor
from extractors.pix2struct import Pix2StructExtractor
from extractors.openai_vision import OpenAIVisionExtractor
from extractors.tesseract_fallback import TesseractExtractor
from chunking import DocumentChunker
from retriever import LegalRetriever

logger = logging.getLogger(__name__)

class DocumentIngestor:
    """Handles document ingestion with multiple VLM backends"""
    
    def __init__(self):
        self.extractors = self._initialize_extractors()
        self.chunker = DocumentChunker()
        self.retriever = None  # Will be set after initialization
        
    def _initialize_extractors(self) -> Dict[str, BaseExtractor]:
        """Initialize VLM extractors based on advanced configuration"""
        extractors = {}
        
        # Get VLM order using advanced configuration system
        vlm_order = get_vlm_order_from_env()
        
        # Log configuration info
        config_info = get_vlm_configuration_info()
        logger.info(f"VLM Configuration: {config_info['configuration']['type']}")
        logger.info(f"VLM Order: {' → '.join(vlm_order)}")
        
        # Validate configuration
        validation = config_info['validation']
        for model, is_valid in validation.items():
            if model in vlm_order and not is_valid:
                logger.warning(f"VLM model '{model}' in order but not properly configured")
        
        # Initialize extractors in order
        for extractor_name in vlm_order:
            extractor_name = extractor_name.strip()
            try:
                if extractor_name == "donut":
                    extractors["donut"] = DonutExtractor()
                elif extractor_name == "pix2struct":
                    extractors["pix2struct"] = Pix2StructExtractor()
                elif extractor_name == "openai":
                    if os.getenv("OPENAI_API_KEY"):
                        extractors["openai"] = OpenAIVisionExtractor()
                    else:
                        logger.warning("OpenAI extractor requested but OPENAI_API_KEY not set")
                        continue
                elif extractor_name == "tesseract_fallback":
                    if os.getenv("ENABLE_OCR_FALLBACK", "true").lower() == "true":
                        extractors["tesseract_fallback"] = TesseractExtractor()
                    else:
                        logger.warning("Tesseract fallback requested but ENABLE_OCR_FALLBACK not enabled")
                        continue
                        
                logger.info(f"✅ Initialized {extractor_name} extractor")
            except Exception as e:
                logger.warning(f"❌ Failed to initialize {extractor_name}: {e}")
        
        if not extractors:
            logger.error("No VLM extractors successfully initialized!")
            # Fallback to basic OCR
            try:
                extractors["tesseract_fallback"] = TesseractExtractor()
                logger.info("✅ Fallback to Tesseract OCR")
            except Exception as e:
                logger.error(f"❌ Even Tesseract fallback failed: {e}")
                raise RuntimeError("No extractors could be initialized")
            
        return extractors
    
    async def ingest_document(self, file_path: str) -> str:
        """
        Ingest a PDF document with vision-language extraction
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Document ID for the ingested document
        """
        try:
            doc_id = str(uuid.uuid4())
            logger.info(f"Starting ingestion of {file_path} with ID {doc_id}")
            
            # Render PDF pages to images
            images = await self._render_pdf_pages(file_path)
            logger.info(f"Rendered {len(images)} pages from PDF")
            
            # Extract text from all pages in parallel
            extracted_pages = await self._extract_text_parallel(images, doc_id)
            
            # Combine and normalize text
            full_text = self._combine_page_texts(extracted_pages)
            normalized_text = normalize_text(full_text)
            
            # Chunk the document
            chunks = self.chunker.chunk_document(normalized_text, doc_id, file_path)
            
            # Store in retriever
            if self.retriever:
                await self.retriever.add_chunks(chunks)
            
            # Save metadata
            await self._save_document_metadata(doc_id, file_path, extracted_pages, chunks)
            
            logger.info(f"Successfully ingested document {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to ingest document {file_path}: {e}")
            raise
    
    async def _render_pdf_pages(self, file_path: str) -> List[Image.Image]:
        """Render PDF pages to high-resolution images"""
        return await render_pdf_pages(file_path, dpi=300)
    
    async def _extract_text_parallel(self, images: List[Image.Image], doc_id: str) -> List[Dict[str, Any]]:
        """Extract text from all pages in parallel using multiple VLM backends"""
        max_workers = int(os.getenv("MAX_WORKERS", 0)) or min(4, len(images))
        batch_size = int(os.getenv("VLM_BATCH_SIZE", 4))
        
        # Process pages in batches
        all_results = []
        for i in range(0, len(images), batch_size):
            batch_images = images[i:i + batch_size]
            batch_results = await run_parallel_extraction(
                images=batch_images,
                extractors=self.extractors,
                max_workers=max_workers,
                page_offset=i
            )
            all_results.extend(batch_results)
        
        return all_results
    
    def _combine_page_texts(self, extracted_pages: List[Dict[str, Any]]) -> str:
        """Combine text from all pages with best confidence scoring"""
        combined_text = []
        
        for page_data in extracted_pages:
            page_num = page_data["page_number"]
            extractions = page_data["extractions"]
            
            if not extractions:
                logger.warning(f"No successful extractions for page {page_num}")
                combined_text.append(f"[Page {page_num}: Extraction failed]")
                continue
            
            # Select best extraction based on confidence
            best_extraction = max(extractions, key=lambda x: x.get("confidence", 0))
            text = best_extraction.get("text", "").strip()
            
            if text:
                combined_text.append(f"[Page {page_num}]")
                combined_text.append(text)
            else:
                combined_text.append(f"[Page {page_num}: No text extracted]")
        
        return "\n\n".join(combined_text)
    
    async def _save_document_metadata(
        self, 
        doc_id: str, 
        file_path: str, 
        extracted_pages: List[Dict[str, Any]], 
        chunks: List[Dict[str, Any]]
    ):
        """Save document metadata for future reference"""
        metadata = {
            "doc_id": doc_id,
            "file_path": file_path,
            "filename": Path(file_path).name,
            "total_pages": len(extracted_pages),
            "total_chunks": len(chunks),
            "extraction_summary": {
                "successful_pages": sum(1 for p in extracted_pages if p["extractions"]),
                "failed_pages": sum(1 for p in extracted_pages if not p["extractions"]),
                "average_confidence": np.mean([
                    max((e.get("confidence", 0) for e in p["extractions"]), default=0)
                    for p in extracted_pages
                ])
            }
        }
        
        metadata_path = Path("data/documents") / f"{doc_id}.json"
        metadata_path.parent.mkdir(exist_ok=True)
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def set_retriever(self, retriever: LegalRetriever):
        """Set the retriever instance"""
        self.retriever = retriever