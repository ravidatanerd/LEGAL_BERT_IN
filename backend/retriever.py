"""
Document retrieval system with InLegalBERT embeddings, FAISS, and BM25
"""

import os
import json
import pickle
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from transformers import AutoTokenizer, AutoModel
import torch
import asyncio
from concurrent.futures import ThreadPoolExecutor

from chunking import Chunk
from utils.textnorm import split_mixed_script_query, normalize_text

logger = logging.getLogger(__name__)

class DocumentRetriever:
    """Document retrieval with dense and sparse search"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.embeddings_dir = self.data_dir / "embeddings"
        self.chunks_dir = self.data_dir / "chunks"
        
        # Create directories
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        
        # Model configuration
        self.model_name = os.getenv("EMBED_MODEL", "law-ai/InLegalBERT")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Initialize components
        self.tokenizer = None
        self.model = None
        self.faiss_index = None
        self.bm25 = None
        self.chunks = []
        self.chunk_metadata = {}
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        self._initialize_model()
        self._load_indexes()
    
    def _initialize_model(self):
        """Initialize InLegalBERT model"""
        try:
            logger.info(f"Loading InLegalBERT model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info("InLegalBERT model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load InLegalBERT model: {e}")
            raise
    
    def _load_indexes(self):
        """Load FAISS index and BM25 from disk"""
        try:
            # Load FAISS index
            faiss_path = self.embeddings_dir / "faiss_index.bin"
            if faiss_path.exists():
                self.faiss_index = faiss.read_index(str(faiss_path))
                logger.info(f"Loaded FAISS index with {self.faiss_index.ntotal} vectors")
            else:
                # Create new index
                self.faiss_index = faiss.IndexFlatIP(768)  # InLegalBERT embedding size
                logger.info("Created new FAISS index")
            
            # Load chunks and metadata
            chunks_path = self.chunks_dir / "chunks.json"
            if chunks_path.exists():
                with open(chunks_path, 'r', encoding='utf-8') as f:
                    chunks_data = json.load(f)
                    self.chunks = [Chunk(**chunk_data) for chunk_data in chunks_data]
                logger.info(f"Loaded {len(self.chunks)} chunks")
            
            # Load chunk metadata
            metadata_path = self.chunks_dir / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self.chunk_metadata = json.load(f)
            
            # Initialize BM25
            if self.chunks:
                self._initialize_bm25()
            
        except Exception as e:
            logger.error(f"Error loading indexes: {e}")
            raise
    
    def _initialize_bm25(self):
        """Initialize BM25 with current chunks"""
        try:
            # Tokenize chunks for BM25
            tokenized_chunks = []
            for chunk in self.chunks:
                # Normalize and tokenize
                normalized_text = normalize_text(chunk.text)
                tokens = normalized_text.lower().split()
                tokenized_chunks.append(tokens)
            
            self.bm25 = BM25Okapi(tokenized_chunks)
            logger.info("BM25 initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing BM25: {e}")
            raise
    
    async def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for texts using InLegalBERT"""
        try:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                self.executor,
                self._get_embeddings_sync,
                texts
            )
            return embeddings
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            raise
    
    def _get_embeddings_sync(self, texts: List[str]) -> np.ndarray:
        """Synchronous embedding generation"""
        try:
            # Tokenize texts
            inputs = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Mean pool with attention mask
                attention_mask = inputs['attention_mask']
                embeddings = outputs.last_hidden_state
                mask_expanded = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
                sum_embeddings = torch.sum(embeddings * mask_expanded, 1)
                sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
                mean_pooled = sum_embeddings / sum_mask
                
                # L2 normalize
                embeddings_norm = torch.nn.functional.normalize(mean_pooled, p=2, dim=1)
                
                return embeddings_norm.cpu().numpy()
                
        except Exception as e:
            logger.error(f"Error in sync embedding generation: {e}")
            raise
    
    async def add_chunks(self, chunks: List[Chunk]):
        """Add new chunks to the retrieval system"""
        try:
            if not chunks:
                return
            
            # Generate embeddings for new chunks
            texts = [chunk.text for chunk in chunks]
            embeddings = await self.get_embeddings(texts)
            
            # Add to FAISS index
            self.faiss_index.add(embeddings.astype('float32'))
            
            # Add to chunks list
            self.chunks.extend(chunks)
            
            # Update metadata
            for chunk in chunks:
                self.chunk_metadata[chunk.chunk_id] = {
                    "document_id": chunk.document_id,
                    "page_number": chunk.page_number,
                    "confidence": chunk.confidence,
                    "metadata": chunk.metadata
                }
            
            # Reinitialize BM25 with all chunks
            self._initialize_bm25()
            
            # Save to disk
            await self._save_indexes()
            
            logger.info(f"Added {len(chunks)} chunks to retrieval system")
            
        except Exception as e:
            logger.error(f"Error adding chunks: {e}")
            raise
    
    async def search(
        self, 
        query: str, 
        top_k: int = 10,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Search for relevant chunks using hybrid approach"""
        try:
            if not self.chunks:
                return []
            
            # Handle mixed script queries
            devanagari_query, other_query = split_mixed_script_query(query)
            
            results = []
            
            # Dense search (semantic)
            if dense_weight > 0:
                dense_results = await self._dense_search(query, top_k * 2)
                for i, (score, idx) in enumerate(dense_results):
                    results.append({
                        "chunk": self.chunks[idx],
                        "dense_score": score,
                        "sparse_score": 0.0,
                        "combined_score": score * dense_weight,
                        "rank": i
                    })
            
            # Sparse search (keyword)
            if sparse_weight > 0:
                sparse_results = await self._sparse_search(query, top_k * 2)
                for i, (score, idx) in enumerate(sparse_results):
                    # Find existing result or create new
                    existing = next((r for r in results if r["chunk"].chunk_id == self.chunks[idx].chunk_id), None)
                    if existing:
                        existing["sparse_score"] = score
                        existing["combined_score"] += score * sparse_weight
                    else:
                        results.append({
                            "chunk": self.chunks[idx],
                            "dense_score": 0.0,
                            "sparse_score": score,
                            "combined_score": score * sparse_weight,
                            "rank": len(results)
                        })
            
            # Sort by combined score and return top_k
            results.sort(key=lambda x: x["combined_score"], reverse=True)
            top_results = results[:top_k]
            
            # Format results
            formatted_results = []
            for result in top_results:
                chunk = result["chunk"]
                formatted_results.append({
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "document_id": chunk.document_id,
                    "page_number": chunk.page_number,
                    "confidence": chunk.confidence,
                    "dense_score": result["dense_score"],
                    "sparse_score": result["sparse_score"],
                    "combined_score": result["combined_score"],
                    "metadata": chunk.metadata
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            raise
    
    async def _dense_search(self, query: str, top_k: int) -> List[Tuple[float, int]]:
        """Dense semantic search using FAISS"""
        try:
            # Get query embedding
            query_embedding = await self.get_embeddings([query])
            
            # Search FAISS index
            scores, indices = self.faiss_index.search(query_embedding.astype('float32'), top_k)
            
            # Return results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.chunks):  # Valid index
                    results.append((float(score), int(idx)))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in dense search: {e}")
            return []
    
    async def _sparse_search(self, query: str, top_k: int) -> List[Tuple[float, int]]:
        """Sparse keyword search using BM25"""
        try:
            if not self.bm25:
                return []
            
            # Tokenize query
            query_tokens = normalize_text(query).lower().split()
            
            # Get BM25 scores
            scores = self.bm25.get_scores(query_tokens)
            
            # Get top_k results
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            # Return results
            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only non-zero scores
                    results.append((float(scores[idx]), int(idx)))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in sparse search: {e}")
            return []
    
    async def get_documents_by_ids(self, document_ids: List[str]) -> List[Dict[str, Any]]:
        """Get documents by their IDs"""
        try:
            documents = {}
            
            for chunk in self.chunks:
                if chunk.document_id in document_ids:
                    if chunk.document_id not in documents:
                        documents[chunk.document_id] = {
                            "document_id": chunk.document_id,
                            "pages": {},
                            "total_chunks": 0
                        }
                    
                    if chunk.page_number not in documents[chunk.document_id]["pages"]:
                        documents[chunk.document_id]["pages"][chunk.page_number] = []
                    
                    documents[chunk.document_id]["pages"][chunk.page_number].append({
                        "chunk_id": chunk.chunk_id,
                        "text": chunk.text,
                        "confidence": chunk.confidence,
                        "metadata": chunk.metadata
                    })
                    
                    documents[chunk.document_id]["total_chunks"] += 1
            
            return list(documents.values())
            
        except Exception as e:
            logger.error(f"Error getting documents by IDs: {e}")
            raise
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the system"""
        try:
            documents = {}
            
            for chunk in self.chunks:
                if chunk.document_id not in documents:
                    documents[chunk.document_id] = {
                        "document_id": chunk.document_id,
                        "total_chunks": 0,
                        "total_pages": set(),
                        "avg_confidence": 0.0
                    }
                
                documents[chunk.document_id]["total_chunks"] += 1
                documents[chunk.document_id]["total_pages"].add(chunk.page_number)
            
            # Calculate average confidence and convert sets to lists
            for doc_id, doc_info in documents.items():
                doc_chunks = [c for c in self.chunks if c.document_id == doc_id]
                doc_info["avg_confidence"] = sum(c.confidence for c in doc_chunks) / len(doc_chunks)
                doc_info["total_pages"] = len(doc_info["total_pages"])
            
            return list(documents.values())
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            raise
    
    async def delete_document(self, document_id: str):
        """Delete a document and all its chunks"""
        try:
            # Find chunks to remove
            chunks_to_remove = [c for c in self.chunks if c.document_id == document_id]
            
            if not chunks_to_remove:
                logger.warning(f"Document {document_id} not found")
                return
            
            # Remove from chunks list
            self.chunks = [c for c in self.chunks if c.document_id != document_id]
            
            # Remove from metadata
            for chunk in chunks_to_remove:
                self.chunk_metadata.pop(chunk.chunk_id, None)
            
            # Rebuild indexes
            await self._rebuild_indexes()
            
            logger.info(f"Deleted document {document_id} with {len(chunks_to_remove)} chunks")
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise
    
    async def get_document_count(self) -> int:
        """Get total number of documents"""
        return len(set(chunk.document_id for chunk in self.chunks))
    
    async def _save_indexes(self):
        """Save indexes to disk"""
        try:
            # Save FAISS index
            faiss_path = self.embeddings_dir / "faiss_index.bin"
            faiss.write_index(self.faiss_index, str(faiss_path))
            
            # Save chunks
            chunks_data = []
            for chunk in self.chunks:
                chunks_data.append({
                    "text": chunk.text,
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "page_number": chunk.page_number,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    "confidence": chunk.confidence,
                    "metadata": chunk.metadata
                })
            
            chunks_path = self.chunks_dir / "chunks.json"
            with open(chunks_path, 'w', encoding='utf-8') as f:
                json.dump(chunks_data, f, ensure_ascii=False, indent=2)
            
            # Save metadata
            metadata_path = self.chunks_dir / "metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.chunk_metadata, f, ensure_ascii=False, indent=2)
            
            logger.info("Indexes saved to disk")
            
        except Exception as e:
            logger.error(f"Error saving indexes: {e}")
            raise
    
    async def _rebuild_indexes(self):
        """Rebuild all indexes from current chunks"""
        try:
            if not self.chunks:
                # Create empty index
                self.faiss_index = faiss.IndexFlatIP(768)
                self.bm25 = None
                return
            
            # Generate embeddings for all chunks
            texts = [chunk.text for chunk in self.chunks]
            embeddings = await self.get_embeddings(texts)
            
            # Rebuild FAISS index
            self.faiss_index = faiss.IndexFlatIP(768)
            self.faiss_index.add(embeddings.astype('float32'))
            
            # Rebuild BM25
            self._initialize_bm25()
            
            # Save to disk
            await self._save_indexes()
            
            logger.info("Indexes rebuilt successfully")
            
        except Exception as e:
            logger.error(f"Error rebuilding indexes: {e}")
            raise
    
    def __del__(self):
        """Cleanup executor"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)