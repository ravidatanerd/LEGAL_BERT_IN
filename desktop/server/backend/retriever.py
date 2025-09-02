"""
Legal document retrieval using InLegalBERT embeddings and BM25
"""
import os
import json
import logging
import pickle
from typing import List, Dict, Any, Optional
from pathlib import Path

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
import faiss
from rank_bm25 import BM25Okapi

from utils.textnorm import normalize_text, is_devanagari_text, split_mixed_script_query

logger = logging.getLogger(__name__)

class LegalRetriever:
    """Retrieval system using InLegalBERT embeddings and BM25"""
    
    def __init__(self):
        self.embed_model_name = os.getenv("EMBED_MODEL", "law-ai/InLegalBERT")
        self.tokenizer = None
        self.model = None
        
        # Storage
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.faiss_index: Optional[faiss.Index] = None
        self.bm25: Optional[BM25Okapi] = None
        
        # Paths
        self.embeddings_dir = Path("data/embeddings")
        self.embeddings_dir.mkdir(exist_ok=True)
    
    async def initialize(self):
        """Initialize InLegalBERT model and load existing data"""
        try:
            logger.info(f"Initializing retriever with {self.embed_model_name}")
            
            # Load InLegalBERT
            self.tokenizer = AutoTokenizer.from_pretrained(self.embed_model_name)
            self.model = AutoModel.from_pretrained(self.embed_model_name)
            
            # Move to GPU if available
            if torch.cuda.is_available():
                self.model = self.model.cuda()
                logger.info("InLegalBERT model moved to GPU")
            
            # Load existing embeddings if available
            await self._load_existing_data()
            
            logger.info("Legal retriever initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize retriever: {e}")
            raise
    
    async def _load_existing_data(self):
        """Load existing chunks and embeddings"""
        try:
            chunks_path = self.embeddings_dir / "chunks.json"
            embeddings_path = self.embeddings_dir / "embeddings.npy"
            index_path = self.embeddings_dir / "faiss.index"
            bm25_path = self.embeddings_dir / "bm25.pkl"
            
            if all(p.exists() for p in [chunks_path, embeddings_path, index_path, bm25_path]):
                # Load chunks
                with open(chunks_path, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                
                # Load embeddings
                self.embeddings = np.load(embeddings_path)
                
                # Load FAISS index
                self.faiss_index = faiss.read_index(str(index_path))
                
                # Load BM25
                with open(bm25_path, "rb") as f:
                    self.bm25 = pickle.load(f)
                
                logger.info(f"Loaded {len(self.chunks)} existing chunks")
            else:
                logger.info("No existing embeddings found, starting fresh")
                self.chunks = []
                
        except Exception as e:
            logger.warning(f"Failed to load existing data: {e}")
            self.chunks = []
    
    async def add_chunks(self, new_chunks: List[Dict[str, Any]]):
        """Add new chunks and update embeddings"""
        try:
            if not new_chunks:
                return
            
            logger.info(f"Adding {len(new_chunks)} new chunks")
            
            # Generate embeddings for new chunks
            new_embeddings = await self._generate_embeddings([chunk["text"] for chunk in new_chunks])
            
            # Add to existing data
            self.chunks.extend(new_chunks)
            
            if self.embeddings is None:
                self.embeddings = new_embeddings
            else:
                self.embeddings = np.vstack([self.embeddings, new_embeddings])
            
            # Rebuild FAISS index
            self._build_faiss_index()
            
            # Rebuild BM25 index
            self._build_bm25_index()
            
            # Save updated data
            await self._save_data()
            
            logger.info(f"Successfully added {len(new_chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Failed to add chunks: {e}")
            raise
    
    async def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate InLegalBERT embeddings for texts"""
        try:
            embeddings = []
            batch_size = 32
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                # Tokenize
                inputs = self.tokenizer(
                    batch_texts,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt"
                )
                
                # Move to GPU if available
                if torch.cuda.is_available():
                    inputs = {k: v.cuda() for k, v in inputs.items()}
                
                # Generate embeddings
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    
                    # Mean pooling with attention mask
                    last_hidden_states = outputs.last_hidden_state
                    attention_mask = inputs["attention_mask"]
                    
                    # Expand attention mask to match hidden states
                    mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_states.size()).float()
                    
                    # Apply mask and compute mean
                    sum_embeddings = torch.sum(last_hidden_states * mask_expanded, 1)
                    sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
                    mean_embeddings = sum_embeddings / sum_mask
                    
                    # L2 normalize
                    embeddings_batch = torch.nn.functional.normalize(mean_embeddings, p=2, dim=1)
                    
                    embeddings.append(embeddings_batch.cpu().numpy())
            
            # Concatenate all batches
            all_embeddings = np.vstack(embeddings)
            logger.info(f"Generated embeddings for {len(texts)} texts")
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def _build_faiss_index(self):
        """Build FAISS index for dense retrieval"""
        try:
            if self.embeddings is None or len(self.embeddings) == 0:
                return
            
            # Create IndexFlatIP for cosine similarity (inner product on normalized vectors)
            dimension = self.embeddings.shape[1]
            self.faiss_index = faiss.IndexFlatIP(dimension)
            
            # Add embeddings
            self.faiss_index.add(self.embeddings.astype(np.float32))
            
            logger.info(f"Built FAISS index with {self.faiss_index.ntotal} vectors")
            
        except Exception as e:
            logger.error(f"Failed to build FAISS index: {e}")
            raise
    
    def _build_bm25_index(self):
        """Build BM25 index for sparse retrieval"""
        try:
            if not self.chunks:
                return
            
            # Tokenize texts for BM25
            tokenized_corpus = [chunk["text"].lower().split() for chunk in self.chunks]
            self.bm25 = BM25Okapi(tokenized_corpus)
            
            logger.info(f"Built BM25 index with {len(tokenized_corpus)} documents")
            
        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}")
            raise
    
    async def search(
        self, 
        query: str, 
        max_results: int = 5,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks using hybrid dense + sparse retrieval
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            dense_weight: Weight for dense (FAISS) scores
            sparse_weight: Weight for sparse (BM25) scores
            
        Returns:
            List of relevant chunks with scores
        """
        try:
            if not self.chunks:
                return []
            
            # Normalize query
            normalized_query = normalize_text(query)
            
            # Handle mixed script queries
            query_parts = split_mixed_script_query(normalized_query)
            
            # Get dense retrieval results
            dense_results = await self._dense_search(normalized_query, max_results * 2)
            
            # Get sparse retrieval results
            sparse_results = self._sparse_search(normalized_query, max_results * 2)
            
            # Combine and rerank results
            combined_results = self._combine_results(
                dense_results, sparse_results, dense_weight, sparse_weight
            )
            
            # Return top results
            return combined_results[:max_results]
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []
    
    async def _dense_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Dense retrieval using FAISS and InLegalBERT"""
        try:
            if self.faiss_index is None or self.faiss_index.ntotal == 0:
                return []
            
            # Generate query embedding
            query_embedding = await self._generate_embeddings([query])
            
            # Search FAISS index
            scores, indices = self.faiss_index.search(
                query_embedding.astype(np.float32), 
                min(k, self.faiss_index.ntotal)
            )
            
            # Format results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.chunks):
                    chunk = self.chunks[idx].copy()
                    chunk["dense_score"] = float(score)
                    results.append(chunk)
            
            return results
            
        except Exception as e:
            logger.error(f"Dense search failed: {e}")
            return []
    
    def _sparse_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Sparse retrieval using BM25"""
        try:
            if self.bm25 is None:
                return []
            
            # Tokenize query
            query_tokens = query.lower().split()
            
            # Get BM25 scores
            scores = self.bm25.get_scores(query_tokens)
            
            # Get top k indices
            top_indices = np.argsort(scores)[::-1][:k]
            
            # Format results
            results = []
            for idx in top_indices:
                if idx < len(self.chunks):
                    chunk = self.chunks[idx].copy()
                    chunk["sparse_score"] = float(scores[idx])
                    results.append(chunk)
            
            return results
            
        except Exception as e:
            logger.error(f"Sparse search failed: {e}")
            return []
    
    def _combine_results(
        self, 
        dense_results: List[Dict[str, Any]], 
        sparse_results: List[Dict[str, Any]],
        dense_weight: float,
        sparse_weight: float
    ) -> List[Dict[str, Any]]:
        """Combine and rerank dense and sparse results"""
        
        # Create a map of chunk_id to results
        result_map = {}
        
        # Add dense results
        for result in dense_results:
            chunk_id = result["chunk_id"]
            result_map[chunk_id] = result
            result_map[chunk_id]["combined_score"] = result.get("dense_score", 0) * dense_weight
        
        # Add sparse results
        for result in sparse_results:
            chunk_id = result["chunk_id"]
            if chunk_id in result_map:
                # Combine scores
                result_map[chunk_id]["combined_score"] += result.get("sparse_score", 0) * sparse_weight
                result_map[chunk_id]["sparse_score"] = result.get("sparse_score", 0)
            else:
                # New result from sparse only
                result["combined_score"] = result.get("sparse_score", 0) * sparse_weight
                result["dense_score"] = 0.0
                result_map[chunk_id] = result
        
        # Sort by combined score
        combined_results = list(result_map.values())
        combined_results.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
        
        return combined_results
    
    async def get_document_content(self, doc_id: str) -> str:
        """Get full content of a document by ID"""
        try:
            doc_chunks = [chunk for chunk in self.chunks if chunk["doc_id"] == doc_id]
            
            if not doc_chunks:
                raise ValueError(f"Document {doc_id} not found")
            
            # Sort chunks by index
            doc_chunks.sort(key=lambda x: x.get("chunk_index", 0))
            
            # Combine chunk texts
            full_text = "\n\n".join(chunk["text"] for chunk in doc_chunks)
            return full_text
            
        except Exception as e:
            logger.error(f"Failed to get document content for {doc_id}: {e}")
            raise
    
    async def get_sources_status(self) -> Dict[str, Any]:
        """Get status of ingested sources"""
        try:
            # Group chunks by document
            doc_groups = {}
            for chunk in self.chunks:
                doc_id = chunk["doc_id"]
                if doc_id not in doc_groups:
                    doc_groups[doc_id] = {
                        "doc_id": doc_id,
                        "filename": chunk.get("filename", "Unknown"),
                        "chunk_count": 0,
                        "total_chars": 0,
                        "has_devanagari": False
                    }
                
                doc_groups[doc_id]["chunk_count"] += 1
                doc_groups[doc_id]["total_chars"] += chunk.get("char_count", 0)
                if chunk.get("is_devanagari", False):
                    doc_groups[doc_id]["has_devanagari"] = True
            
            return {
                "total_documents": len(doc_groups),
                "total_chunks": len(self.chunks),
                "embedding_dimension": self.embeddings.shape[1] if self.embeddings is not None else 0,
                "faiss_index_size": self.faiss_index.ntotal if self.faiss_index else 0,
                "bm25_initialized": self.bm25 is not None,
                "documents": list(doc_groups.values())
            }
            
        except Exception as e:
            logger.error(f"Failed to get sources status: {e}")
            return {"error": str(e)}
    
    async def _save_data(self):
        """Save chunks and embeddings to disk"""
        try:
            # Save chunks
            with open(self.embeddings_dir / "chunks.json", "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, indent=2, ensure_ascii=False)
            
            # Save embeddings
            if self.embeddings is not None:
                np.save(self.embeddings_dir / "embeddings.npy", self.embeddings)
            
            # Save FAISS index
            if self.faiss_index is not None:
                faiss.write_index(self.faiss_index, str(self.embeddings_dir / "faiss.index"))
            
            # Save BM25
            if self.bm25 is not None:
                with open(self.embeddings_dir / "bm25.pkl", "wb") as f:
                    pickle.dump(self.bm25, f)
            
            logger.info("Successfully saved retrieval data")
            
        except Exception as e:
            logger.error(f"Failed to save retrieval data: {e}")
            raise