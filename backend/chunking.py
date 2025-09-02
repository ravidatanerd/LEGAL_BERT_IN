"""
Document chunking for legal text processing
"""
import re
import logging
from typing import List, Dict, Any
from pathlib import Path

from utils.textnorm import normalize_text, is_devanagari_text

logger = logging.getLogger(__name__)

class DocumentChunker:
    """Handles intelligent chunking of legal documents"""
    
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_document(
        self, 
        text: str, 
        doc_id: str, 
        file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Chunk a document into overlapping segments
        
        Args:
            text: Normalized document text
            doc_id: Unique document identifier
            file_path: Original file path
            
        Returns:
            List of chunk dictionaries
        """
        try:
            if not text or not text.strip():
                logger.warning(f"Empty text for document {doc_id}")
                return []
            
            # Split into sentences for better chunking
            sentences = self._split_into_sentences(text)
            
            # Create overlapping chunks
            chunks = self._create_overlapping_chunks(sentences)
            
            # Create chunk objects
            chunk_objects = []
            for i, chunk_text in enumerate(chunks):
                chunk_objects.append({
                    "chunk_id": f"{doc_id}_chunk_{i}",
                    "doc_id": doc_id,
                    "text": chunk_text,
                    "chunk_index": i,
                    "file_path": file_path,
                    "filename": Path(file_path).name,
                    "is_devanagari": is_devanagari_text(chunk_text),
                    "word_count": len(chunk_text.split()),
                    "char_count": len(chunk_text)
                })
            
            logger.info(f"Created {len(chunk_objects)} chunks for document {doc_id}")
            return chunk_objects
            
        except Exception as e:
            logger.error(f"Failed to chunk document {doc_id}: {e}")
            raise
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences, handling legal text patterns"""
        
        # Legal document sentence patterns
        # Handle numbered sections, subsections, etc.
        sentence_endings = r'[.!?](?:\s+|$)'
        
        # Split on sentence endings but preserve legal numbering
        sentences = re.split(sentence_endings, text)
        
        # Clean and filter sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Filter very short fragments
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def _create_overlapping_chunks(self, sentences: List[str]) -> List[str]:
        """Create overlapping chunks from sentences"""
        if not sentences:
            return []
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            sentence_length = len(sentence.split())
            
            # If adding this sentence would exceed chunk size
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Finalize current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)
                
                # Start new chunk with overlap
                overlap_sentences = []
                overlap_length = 0
                
                # Add sentences from the end of current chunk for overlap
                for j in range(len(current_chunk) - 1, -1, -1):
                    overlap_sent = current_chunk[j]
                    overlap_sent_length = len(overlap_sent.split())
                    
                    if overlap_length + overlap_sent_length <= self.overlap:
                        overlap_sentences.insert(0, overlap_sent)
                        overlap_length += overlap_sent_length
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_length = overlap_length
            
            # Add current sentence
            current_chunk.append(sentence)
            current_length += sentence_length
            i += 1
        
        # Add final chunk if any content remains
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)
        
        return chunks