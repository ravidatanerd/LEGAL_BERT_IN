"""
Document ingestion system with vision-language extraction
"""

import os
import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import numpy as np
from loguru import logger

from utils.pdf_images import PDFImageRenderer
from utils.textnorm import TextNormalizer
from utils.parallel import ParallelProcessor
from extractors.base import BaseExtractor
from extractors.donut import DonutExtractor
from extractors.pix2struct import Pix2StructExtractor
from extractors.openai_vision import OpenAIVisionExtractor
from extractors.tesseract_fallback import TesseractExtractor
from chunking import DocumentChunker

class DocumentIngester:
    """Main document ingestion orchestrator"""
    
    def __init__(self):
        self.renderer = PDFImageRenderer()
        self.normalizer = TextNormalizer()
        self.processor = ParallelProcessor()
        self.chunker = DocumentChunker()
        
        # Initialize extractors based on configuration
        self.extractors = self._initialize_extractors()
        
        # Create necessary directories
        os.makedirs("data/documents", exist_ok=True)
        os.makedirs("data/chunks", exist_ok=True)
        os.makedirs("temp", exist_ok=True)
    
    def _initialize_extractors(self) -> List[BaseExtractor]:
        """Initialize vision-language extractors in configured order"""
        extractors = []
        vlm_order = os.getenv("VLM_ORDER", "donut,pix2struct,openai,tesseract_fallback").split(",")
        
        for vlm_type in vlm_order:
            vlm_type = vlm_type.strip()
            try:
                if vlm_type == "donut":
                    extractors.append(DonutExtractor())
                elif vlm_type == "pix2struct":
                    extractors.append(Pix2StructExtractor())
                elif vlm_type == "openai":
                    if os.getenv("OPENAI_API_KEY"):
                        extractors.append(OpenAIVisionExtractor())
                elif vlm_type == "tesseract_fallback":
                    if os.getenv("ENABLE_OCR_FALLBACK", "false").lower() == "true":
                        extractors.append(TesseractExtractor())
            except Exception as e:
                logger.warning(f"Failed to initialize {vlm_type} extractor: {e}")
        
        logger.info(f"Initialized {len(extractors)} extractors: {[e.__class__.__name__ for e in extractors]}")
        return extractors
    
    async def ingest_document(self, pdf_path: str, metadata: Optional[str] = None) -> Dict[str, Any]:
        """Ingest a PDF document with vision-language extraction"""
        try:
            logger.info(f"Starting ingestion of {pdf_path}")
            
            # Parse metadata
            doc_metadata = self._parse_metadata(metadata) if metadata else {}
            doc_metadata["source_file"] = pdf_path
            doc_metadata["ingestion_timestamp"] = asyncio.get_event_loop().time()
            
            # Render PDF pages to images
            pages = await self.renderer.render_pdf(pdf_path)
            logger.info(f"Rendered {len(pages)} pages from {pdf_path}")
            
            # Extract text from each page using multiple backends
            extracted_pages = await self._extract_pages_parallel(pages)
            
            # Combine and normalize text
            full_text = self._combine_page_texts(extracted_pages)
            normalized_text = self.normalizer.normalize(full_text)
            
            # Chunk the document
            chunks = self.chunker.chunk_document(normalized_text, doc_metadata)
            
            # Save document and chunks
            doc_id = await self._save_document(pdf_path, normalized_text, doc_metadata, extracted_pages)
            await self._save_chunks(doc_id, chunks)
            
            logger.info(f"Successfully ingested document {doc_id} with {len(chunks)} chunks")
            
            return {
                "document_id": doc_id,
                "pages_processed": len(pages),
                "chunks_created": len(chunks),
                "extraction_errors": sum(len(page.get("errors", [])) for page in extracted_pages),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Document ingestion failed for {pdf_path}: {e}")
            raise
    
    async def _extract_pages_parallel(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract text from pages using multiple backends in parallel"""
        batch_size = int(os.getenv("VLM_BATCH_SIZE", "4"))
        max_workers = int(os.getenv("MAX_WORKERS", "0")) or None
        
        # Process pages in batches
        extracted_pages = []
        for i in range(0, len(pages), batch_size):
            batch = pages[i:i + batch_size]
            batch_results = await self.processor.process_batch(
                batch, 
                self._extract_single_page,
                max_workers=max_workers
            )
            extracted_pages.extend(batch_results)
        
        return extracted_pages
    
    async def _extract_single_page(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text from a single page using multiple backends"""
        page_num = page["page_number"]
        image = page["image"]
        
        results = {
            "page_number": page_num,
            "extractions": [],
            "errors": [],
            "confidence_scores": []
        }
        
        # Try each extractor in order
        for extractor in self.extractors:
            try:
                extraction = await extractor.extract_text(image)
                if extraction["text"].strip():
                    results["extractions"].append(extraction)
                    results["confidence_scores"].append(extraction.get("confidence", 0.0))
            except Exception as e:
                error_msg = f"{extractor.__class__.__name__} failed: {str(e)}"
                results["errors"].append(error_msg)
                logger.warning(f"Page {page_num} - {error_msg}")
        
        # Select best extraction based on confidence and text quality
        best_extraction = self._select_best_extraction(results["extractions"])
        results["best_text"] = best_extraction["text"] if best_extraction else ""
        results["best_confidence"] = best_extraction.get("confidence", 0.0) if best_extraction else 0.0
        
        return results
    
    def _select_best_extraction(self, extractions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Select the best extraction based on confidence and text quality"""
        if not extractions:
            return None
        
        # Score each extraction
        scored_extractions = []
        for extraction in extractions:
            text = extraction["text"]
            confidence = extraction.get("confidence", 0.0)
            
            # Heuristic scoring: alphanumeric density + confidence
            alnum_ratio = sum(c.isalnum() for c in text) / max(len(text), 1)
            quality_score = alnum_ratio * 0.7 + confidence * 0.3
            
            scored_extractions.append((quality_score, extraction))
        
        # Return highest scoring extraction
        scored_extractions.sort(key=lambda x: x[0], reverse=True)
        return scored_extractions[0][1] if scored_extractions else None
    
    def _combine_page_texts(self, extracted_pages: List[Dict[str, Any]]) -> str:
        """Combine extracted texts from all pages"""
        page_texts = []
        for page in extracted_pages:
            if page["best_text"]:
                page_texts.append(f"--- Page {page['page_number']} ---\n{page['best_text']}")
        
        return "\n\n".join(page_texts)
    
    def _parse_metadata(self, metadata_str: str) -> Dict[str, Any]:
        """Parse metadata JSON string"""
        try:
            return json.loads(metadata_str)
        except json.JSONDecodeError:
            return {"raw_metadata": metadata_str}
    
    async def _save_document(self, pdf_path: str, text: str, metadata: Dict[str, Any], 
                           extracted_pages: List[Dict[str, Any]]) -> str:
        """Save document to storage and return document ID"""
        import hashlib
        import aiofiles
        
        # Generate document ID
        doc_id = hashlib.sha256(f"{pdf_path}{metadata.get('ingestion_timestamp', '')}".encode()).hexdigest()[:16]
        
        # Save document data
        doc_data = {
            "document_id": doc_id,
            "source_file": pdf_path,
            "text": text,
            "metadata": metadata,
            "extraction_details": extracted_pages,
            "created_at": asyncio.get_event_loop().time()
        }
        
        doc_path = f"data/documents/{doc_id}.json"
        async with aiofiles.open(doc_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(doc_data, indent=2, ensure_ascii=False))
        
        return doc_id
    
    async def _save_chunks(self, doc_id: str, chunks: List[Dict[str, Any]]):
        """Save document chunks to storage"""
        import aiofiles
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            chunk["chunk_id"] = chunk_id
            chunk["document_id"] = doc_id
            
            chunk_path = f"data/chunks/{chunk_id}.json"
            async with aiofiles.open(chunk_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(chunk, indent=2, ensure_ascii=False))
    
    async def get_document_status(self, doc_id: str) -> Dict[str, Any]:
        """Get ingestion status of a document"""
        doc_path = f"data/documents/{doc_id}.json"
        if not os.path.exists(doc_path):
            return {"status": "not_found"}
        
        try:
            import aiofiles
            async with aiofiles.open(doc_path, "r", encoding="utf-8") as f:
                doc_data = json.loads(await f.read())
            
            return {
                "status": "completed",
                "document_id": doc_id,
                "pages_processed": len(doc_data.get("extraction_details", [])),
                "text_length": len(doc_data.get("text", "")),
                "created_at": doc_data.get("created_at")
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}