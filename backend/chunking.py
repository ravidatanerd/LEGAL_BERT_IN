"""
Document chunking and text processing utilities
"""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from utils.textnorm import normalize_text, get_text_confidence

logger = logging.getLogger(__name__)

@dataclass
class Chunk:
    """Document chunk with metadata"""
    text: str
    chunk_id: str
    document_id: str
    page_number: int
    start_char: int
    end_char: int
    confidence: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class DocumentChunker:
    """Chunk documents for embedding and retrieval"""
    
    def __init__(
        self, 
        chunk_size: int = 512, 
        chunk_overlap: int = 50,
        min_chunk_size: int = 100
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.logger = logging.getLogger(__name__)
    
    def chunk_document(
        self, 
        text: str, 
        document_id: str, 
        page_number: int = 0,
        confidence: float = 1.0
    ) -> List[Chunk]:
        """Chunk a document into overlapping segments"""
        
        if not text or not text.strip():
            return []
        
        # Normalize text
        normalized_text = normalize_text(text)
        
        # Skip if confidence is too low
        if confidence < 0.3:
            self.logger.warning(f"Skipping low confidence text (confidence: {confidence:.3f})")
            return []
        
        # Split into sentences for better chunking
        sentences = self._split_into_sentences(normalized_text)
        
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_id = 0
        
        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # Create chunk
                chunk_text = current_chunk.strip()
                if len(chunk_text) >= self.min_chunk_size:
                    chunk = Chunk(
                        text=chunk_text,
                        chunk_id=f"{document_id}_page{page_number}_chunk{chunk_id}",
                        document_id=document_id,
                        page_number=page_number,
                        start_char=current_start,
                        end_char=current_start + len(chunk_text),
                        confidence=confidence,
                        metadata={
                            "chunk_size": len(chunk_text),
                            "sentence_count": len(current_chunk.split('.'))
                        }
                    )
                    chunks.append(chunk)
                    chunk_id += 1
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + sentence
                current_start = current_start + len(current_chunk) - len(overlap_text) - len(sentence)
            else:
                current_chunk += sentence
        
        # Add final chunk
        if current_chunk.strip() and len(current_chunk.strip()) >= self.min_chunk_size:
            chunk = Chunk(
                text=current_chunk.strip(),
                chunk_id=f"{document_id}_page{page_number}_chunk{chunk_id}",
                document_id=document_id,
                page_number=page_number,
                start_char=current_start,
                end_char=current_start + len(current_chunk.strip()),
                confidence=confidence,
                metadata={
                    "chunk_size": len(current_chunk.strip()),
                    "sentence_count": len(current_chunk.split('.'))
                }
            )
            chunks.append(chunk)
        
        self.logger.info(f"Created {len(chunks)} chunks for document {document_id}, page {page_number}")
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting - can be improved with NLTK/spaCy
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() + '.' for s in sentences if s.strip()]
        return sentences
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of current chunk"""
        if len(text) <= self.chunk_overlap:
            return text
        
        # Find last complete sentence within overlap
        overlap_text = text[-self.chunk_overlap:]
        sentences = self._split_into_sentences(overlap_text)
        
        if len(sentences) > 1:
            # Return all but the last sentence
            return ' '.join(sentences[:-1])
        else:
            # Return the overlap text as is
            return overlap_text
    
    def chunk_multiple_pages(
        self, 
        pages: List[Dict[str, Any]], 
        document_id: str
    ) -> List[Chunk]:
        """Chunk multiple pages of a document"""
        all_chunks = []
        
        for page_data in pages:
            page_number = page_data.get('page_number', 0)
            text = page_data.get('text', '')
            confidence = page_data.get('confidence', 1.0)
            
            page_chunks = self.chunk_document(
                text=text,
                document_id=document_id,
                page_number=page_number,
                confidence=confidence
            )
            all_chunks.extend(page_chunks)
        
        self.logger.info(f"Total chunks created for document {document_id}: {len(all_chunks)}")
        return all_chunks
    
    def filter_chunks_by_confidence(self, chunks: List[Chunk], min_confidence: float = 0.5) -> List[Chunk]:
        """Filter chunks by confidence threshold"""
        filtered = [chunk for chunk in chunks if chunk.confidence >= min_confidence]
        self.logger.info(f"Filtered {len(chunks)} chunks to {len(filtered)} (min confidence: {min_confidence})")
        return filtered
    
    def get_chunk_statistics(self, chunks: List[Chunk]) -> Dict[str, Any]:
        """Get statistics about chunks"""
        if not chunks:
            return {}
        
        confidences = [chunk.confidence for chunk in chunks]
        sizes = [len(chunk.text) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "avg_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "avg_size": sum(sizes) / len(sizes),
            "min_size": min(sizes),
            "max_size": max(sizes),
            "total_text_length": sum(sizes)
        }