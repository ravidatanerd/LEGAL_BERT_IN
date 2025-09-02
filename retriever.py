"""
Legal document retrieval system with InLegalBERT embeddings
"""

import os
import json
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import faiss
from rank_bm25 import BM25
from sentence_transformers import SentenceTransformer
from loguru import logger
import re

from utils.textnorm import TextNormalizer

class LegalRetriever:
    """Legal document retrieval with InLegalBERT embeddings"""
    
    def __init__(self):
        self.embed_model = None
        self.dense_index = None
        self.sparse_index = None
        self.documents = {}
        self.chunks = {}
        self.normalizer = TextNormalizer()
        
        # Initialize components
        asyncio.create_task(self._initialize())
    
    async def _initialize(self):
        """Initialize the retrieval system"""
        try:
            logger.info("Initializing Legal Retrieval System...")
            
            # Load InLegalBERT model
            model_name = os.getenv("EMBED_MODEL", "law-ai/InLegalBERT")
            self.embed_model = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
            
            # Initialize FAISS index
            self.dense_index = faiss.IndexFlatIP(768)  # InLegalBERT dimension
            
            # Initialize BM25
            self.sparse_index = BM25([])
            
            # Load existing documents and chunks
            await self._load_existing_data()
            
            logger.info("Legal Retrieval System initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize retrieval system: {e}")
            raise
    
    async def _load_existing_data(self):
        """Load existing documents and chunks from storage"""
        try:
            # Load documents
            docs_dir = Path("data/documents")
            if docs_dir.exists():
                for doc_file in docs_dir.glob("*.json"):
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                        self.documents[doc_data['document_id']] = doc_data
            
            # Load chunks and build indices
            chunks_dir = Path("data/chunks")
            if chunks_dir.exists():
                chunk_texts = []
                chunk_metadata = []
                
                for chunk_file in chunks_dir.glob("*.json"):
                    with open(chunk_file, 'r', encoding='utf-8') as f:
                        chunk_data = json.load(f)
                        chunk_id = chunk_data['chunk_id']
                        
                        self.chunks[chunk_id] = chunk_data
                        chunk_texts.append(chunk_data['text'])
                        chunk_metadata.append(chunk_data)
                
                # Build indices
                if chunk_texts:
                    await self._build_indices(chunk_texts, chunk_metadata)
            
            logger.info(f"Loaded {len(self.documents)} documents and {len(self.chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Failed to load existing data: {e}")
    
    async def _build_indices(self, texts: List[str], metadata: List[Dict[str, Any]]):
        """Build dense and sparse indices"""
        try:
            # Build dense embeddings
            logger.info("Building dense embeddings...")
            embeddings = self.embed_model.encode(texts, show_progress_bar=True)
            
            # Normalize embeddings for cosine similarity
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Add to FAISS index
            self.dense_index.add(embeddings.astype('float32'))
            
            # Build BM25 index
            logger.info("Building BM25 index...")
            tokenized_texts = [self._tokenize_for_bm25(text) for text in texts]
            self.sparse_index = BM25(tokenized_texts)
            
            # Store metadata
            self.chunk_metadata = metadata
            
            logger.info(f"Built indices for {len(texts)} chunks")
            
        except Exception as e:
            logger.error(f"Failed to build indices: {e}")
            raise
    
    def _tokenize_for_bm25(self, text: str) -> List[str]:
        """Tokenize text for BM25 indexing"""
        # Simple tokenization - can be improved with proper legal tokenizer
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    async def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Add new chunks to the retrieval system"""
        try:
            if not chunks:
                return
            
            # Extract texts and metadata
            texts = [chunk['text'] for chunk in chunks]
            metadata = chunks
            
            # Generate embeddings
            embeddings = self.embed_model.encode(texts, show_progress_bar=True)
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Add to FAISS index
            self.dense_index.add(embeddings.astype('float32'))
            
            # Update BM25 index
            tokenized_texts = [self._tokenize_for_bm25(text) for text in texts]
            self.sparse_index.add_documents(tokenized_texts)
            
            # Store chunks and metadata
            for chunk in chunks:
                self.chunks[chunk['chunk_id']] = chunk
            
            if not hasattr(self, 'chunk_metadata'):
                self.chunk_metadata = []
            self.chunk_metadata.extend(metadata)
            
            logger.info(f"Added {len(chunks)} chunks to retrieval system")
            
        except Exception as e:
            logger.error(f"Failed to add chunks: {e}")
            raise
    
    async def search(self, query: str, max_results: int = 10, 
                    language: str = "auto") -> List[Dict[str, Any]]:
        """Search for relevant legal documents"""
        try:
            if not query or not query.strip():
                return []
            
            # Normalize query
            normalized_query = self.normalizer.normalize(query)
            
            # Handle mixed-script queries
            if language == "auto" or self._is_mixed_script(normalized_query):
                results = await self._search_mixed_script(normalized_query, max_results)
            else:
                results = await self._search_single_script(normalized_query, max_results)
            
            # Rerank results
            reranked_results = await self._rerank_results(query, results)
            
            return reranked_results[:max_results]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _is_mixed_script(self, text: str) -> bool:
        """Check if text contains mixed scripts"""
        script_info = self.normalizer.extract_script_info(text)
        return script_info['is_mixed_script']
    
    async def _search_mixed_script(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search with mixed script handling"""
        # Split query by script
        query_parts = self.normalizer.split_by_script(query)
        
        all_results = []
        
        for part in query_parts:
            if part.strip():
                # Search each part separately
                part_results = await self._search_single_script(part, max_results)
                all_results.extend(part_results)
        
        # Remove duplicates and combine scores
        unique_results = self._merge_duplicate_results(all_results)
        
        return unique_results[:max_results]
    
    async def _search_single_script(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search with single script"""
        # Dense search
        dense_results = await self._dense_search(query, max_results * 2)
        
        # Sparse search
        sparse_results = await self._sparse_search(query, max_results * 2)
        
        # Combine results
        combined_results = self._combine_search_results(dense_results, sparse_results)
        
        return combined_results[:max_results]
    
    async def _dense_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Dense vector search using InLegalBERT"""
        try:
            # Generate query embedding
            query_embedding = self.embed_model.encode([query])
            query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
            
            # Search FAISS index
            scores, indices = self.dense_index.search(query_embedding.astype('float32'), max_results)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.chunk_metadata):
                    chunk_meta = self.chunk_metadata[idx]
                    results.append({
                        'chunk_id': chunk_meta['chunk_id'],
                        'text': chunk_meta['text'],
                        'metadata': chunk_meta['metadata'],
                        'dense_score': float(score),
                        'sparse_score': 0.0,
                        'combined_score': float(score)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Dense search failed: {e}")
            return []
    
    async def _sparse_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Sparse search using BM25"""
        try:
            # Tokenize query
            query_tokens = self._tokenize_for_bm25(query)
            
            # Get BM25 scores
            scores = self.sparse_index.get_scores(query_tokens)
            
            # Get top results
            top_indices = np.argsort(scores)[::-1][:max_results]
            
            results = []
            for idx in top_indices:
                if scores[idx] > 0 and idx < len(self.chunk_metadata):
                    chunk_meta = self.chunk_metadata[idx]
                    results.append({
                        'chunk_id': chunk_meta['chunk_id'],
                        'text': chunk_meta['text'],
                        'metadata': chunk_meta['metadata'],
                        'dense_score': 0.0,
                        'sparse_score': float(scores[idx]),
                        'combined_score': float(scores[idx])
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Sparse search failed: {e}")
            return []
    
    def _combine_search_results(self, dense_results: List[Dict[str, Any]], 
                              sparse_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine dense and sparse search results"""
        # Create a map of chunk_id to results
        result_map = {}
        
        # Add dense results
        for result in dense_results:
            chunk_id = result['chunk_id']
            result_map[chunk_id] = result
        
        # Add/merge sparse results
        for result in sparse_results:
            chunk_id = result['chunk_id']
            if chunk_id in result_map:
                # Merge scores
                result_map[chunk_id]['sparse_score'] = result['sparse_score']
                result_map[chunk_id]['combined_score'] = (
                    result_map[chunk_id]['dense_score'] * 0.7 + 
                    result['sparse_score'] * 0.3
                )
            else:
                result_map[chunk_id] = result
        
        # Convert to list and sort by combined score
        combined_results = list(result_map.values())
        combined_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return combined_results
    
    def _merge_duplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge duplicate results from different query parts"""
        result_map = {}
        
        for result in results:
            chunk_id = result['chunk_id']
            if chunk_id in result_map:
                # Take the higher score
                if result['combined_score'] > result_map[chunk_id]['combined_score']:
                    result_map[chunk_id] = result
            else:
                result_map[chunk_id] = result
        
        # Sort by combined score
        merged_results = list(result_map.values())
        merged_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return merged_results
    
    async def _rerank_results(self, original_query: str, 
                            results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rerank results based on legal relevance"""
        try:
            # Simple reranking based on legal keywords and context
            legal_keywords = [
                'section', 'article', 'act', 'rule', 'regulation',
                'judgment', 'order', 'decree', 'petition', 'appeal',
                'constitution', 'statute', 'precedent', 'case law'
            ]
            
            for result in results:
                text = result['text'].lower()
                query_lower = original_query.lower()
                
                # Boost score for legal keywords
                legal_boost = sum(1 for keyword in legal_keywords if keyword in text)
                result['legal_relevance_boost'] = legal_boost * 0.1
                
                # Boost score for query term matches
                query_terms = query_lower.split()
                term_matches = sum(1 for term in query_terms if term in text)
                result['query_term_boost'] = term_matches * 0.05
                
                # Update combined score
                result['combined_score'] += result['legal_relevance_boost'] + result['query_term_boost']
            
            # Sort by updated combined score
            results.sort(key=lambda x: x['combined_score'], reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return results
    
    async def search_judgment_context(self, facts: str, issues: List[str], 
                                    court_type: str) -> List[Dict[str, Any]]:
        """Search for relevant context for judgment generation"""
        try:
            # Create search queries
            queries = []
            
            # Add fact-based queries
            if facts:
                queries.append(f"facts: {facts}")
            
            # Add issue-based queries
            for issue in issues:
                queries.append(f"legal issue: {issue}")
            
            # Add court-type specific queries
            if court_type == "high_court":
                queries.append("high court judgment precedent")
            elif court_type == "supreme_court":
                queries.append("supreme court judgment precedent")
            
            # Search for each query
            all_results = []
            for query in queries:
                results = await self.search(query, max_results=5)
                all_results.extend(results)
            
            # Remove duplicates and return top results
            unique_results = self._merge_duplicate_results(all_results)
            return unique_results[:20]
            
        except Exception as e:
            logger.error(f"Judgment context search failed: {e}")
            return []
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID"""
        return self.documents.get(document_id)
    
    async def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get a chunk by ID"""
        return self.chunks.get(chunk_id)
    
    async def get_sources_status(self) -> Dict[str, Any]:
        """Get status of legal sources"""
        try:
            status = {
                "total_documents": len(self.documents),
                "total_chunks": len(self.chunks),
                "dense_index_size": self.dense_index.ntotal if self.dense_index else 0,
                "sparse_index_size": len(self.sparse_index.corpus) if self.sparse_index else 0,
                "embedding_model": os.getenv("EMBED_MODEL", "law-ai/InLegalBERT"),
                "documents_by_type": {},
                "recent_documents": []
            }
            
            # Analyze document types
            for doc in self.documents.values():
                doc_type = doc.get('metadata', {}).get('document_type', 'unknown')
                status["documents_by_type"][doc_type] = status["documents_by_type"].get(doc_type, 0) + 1
            
            # Get recent documents
            sorted_docs = sorted(
                self.documents.values(),
                key=lambda x: x.get('created_at', 0),
                reverse=True
            )
            status["recent_documents"] = [
                {
                    "document_id": doc['document_id'],
                    "source_file": doc.get('source_file', ''),
                    "created_at": doc.get('created_at', 0),
                    "text_length": len(doc.get('text', ''))
                }
                for doc in sorted_docs[:10]
            ]
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get sources status: {e}")
            return {"error": str(e)}