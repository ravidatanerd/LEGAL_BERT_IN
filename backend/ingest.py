"""
Document ingestion pipeline
"""

import os
import uuid
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

from utils.pdf_images import PDFImageExtractor
from utils.vlm import VLMPipeline
from chunking import DocumentChunker
from retriever import DocumentRetriever
from utils.parallel import safe_parallel_process

logger = logging.getLogger(__name__)

class DocumentIngester:
    """Document ingestion pipeline"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.uploads_dir = self.data_dir / "uploads"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.pdf_extractor = PDFImageExtractor(dpi=300)
        self.vlm_pipeline = VLMPipeline()
        self.chunker = DocumentChunker(
            chunk_size=512,
            chunk_overlap=50,
            min_chunk_size=100
        )
        self.retriever = DocumentRetriever(data_dir)
        
        # Configuration
        self.max_workers = int(os.getenv("MAX_WORKERS", "0")) or os.cpu_count() or 4
        self.batch_size = int(os.getenv("VLM_BATCH_SIZE", "4"))
        
        logger.info(f"Document ingester initialized with {self.max_workers} workers")
    
    async def ingest_document(self, file_path: Path) -> str:
        """Ingest a document and return document ID"""
        try:
            # Generate document ID
            doc_id = str(uuid.uuid4())
            
            logger.info(f"Starting ingestion of {file_path} as {doc_id}")
            
            # Extract images from PDF
            images = await self.pdf_extractor.extract_page_images(str(file_path))
            logger.info(f"Extracted {len(images)} pages from PDF")
            
            if not images:
                raise ValueError("No pages extracted from PDF")
            
            # Extract text from images using VLM pipeline
            extraction_results = await self.vlm_pipeline.extract_text_from_images(images)
            logger.info(f"Extracted text from {len(extraction_results)} pages")
            
            # Process pages in parallel
            pages_data = []
            for i, (image, result) in enumerate(zip(images, extraction_results)):
                pages_data.append({
                    "page_number": i,
                    "text": result.text,
                    "confidence": result.confidence,
                    "method": result.method,
                    "metadata": result.metadata
                })
            
            # Chunk the document
            chunks = self.chunker.chunk_multiple_pages(pages_data, doc_id)
            logger.info(f"Created {len(chunks)} chunks")
            
            # Filter chunks by confidence
            filtered_chunks = self.chunker.filter_chunks_by_confidence(chunks, min_confidence=0.3)
            logger.info(f"Filtered to {len(filtered_chunks)} chunks after confidence filtering")
            
            if not filtered_chunks:
                logger.warning(f"No chunks passed confidence filtering for {doc_id}")
                return doc_id
            
            # Add chunks to retriever
            await self.retriever.add_chunks(filtered_chunks)
            
            # Save document metadata
            await self._save_document_metadata(doc_id, file_path, pages_data, filtered_chunks)
            
            logger.info(f"Successfully ingested document {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error ingesting document {file_path}: {e}")
            raise
    
    async def ingest_multiple_documents(self, file_paths: List[Path]) -> List[str]:
        """Ingest multiple documents in parallel"""
        try:
            # Process documents in parallel
            results = await safe_parallel_process(
                file_paths,
                self._ingest_single_document,
                max_workers=self.max_workers,
                batch_size=self.batch_size
            )
            
            # Extract successful document IDs
            doc_ids = []
            for file_path, result in results:
                if isinstance(result, Exception):
                    logger.error(f"Failed to ingest {file_path}: {result}")
                else:
                    doc_ids.append(result)
            
            logger.info(f"Successfully ingested {len(doc_ids)} out of {len(file_paths)} documents")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Error ingesting multiple documents: {e}")
            raise
    
    async def _ingest_single_document(self, file_path: Path) -> str:
        """Ingest a single document (for parallel processing)"""
        return await self.ingest_document(file_path)
    
    async def _save_document_metadata(
        self, 
        doc_id: str, 
        file_path: Path, 
        pages_data: List[Dict[str, Any]], 
        chunks: List
    ):
        """Save document metadata"""
        try:
            metadata = {
                "document_id": doc_id,
                "filename": file_path.name,
                "file_path": str(file_path),
                "total_pages": len(pages_data),
                "total_chunks": len(chunks),
                "ingestion_timestamp": asyncio.get_event_loop().time(),
                "pages": pages_data,
                "chunk_statistics": self.chunker.get_chunk_statistics(chunks)
            }
            
            metadata_path = self.data_dir / "metadata" / f"{doc_id}.json"
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved metadata for document {doc_id}")
            
        except Exception as e:
            logger.error(f"Error saving document metadata: {e}")
    
    async def get_document_status(self, doc_id: str) -> Dict[str, Any]:
        """Get status of a document"""
        try:
            metadata_path = self.data_dir / "metadata" / f"{doc_id}.json"
            
            if not metadata_path.exists():
                return {"status": "not_found"}
            
            import json
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            return {
                "status": "ingested",
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting document status: {e}")
            return {"status": "error", "error": str(e)}
    
    async def delete_document(self, doc_id: str):
        """Delete a document and all its data"""
        try:
            # Remove from retriever
            await self.retriever.delete_document(doc_id)
            
            # Remove metadata file
            metadata_path = self.data_dir / "metadata" / f"{doc_id}.json"
            if metadata_path.exists():
                metadata_path.unlink()
            
            logger.info(f"Deleted document {doc_id}")
            
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            raise