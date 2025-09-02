"""
API client for communicating with the FastAPI backend
"""
import os
import logging
from typing import Dict, Any, List, Optional
import httpx
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

class LegalAPIClient:
    """Client for interacting with the legal research backend API"""
    
    def __init__(self):
        self.base_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8877")
        self.client = None
        self.timeout = httpx.Timeout(120.0)
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                base_url=self.base_url
            )
        return self.client
    
    async def health_check(self) -> Dict[str, Any]:
        """Check backend health"""
        try:
            client = await self._get_client()
            response = await client.get("/health")
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise
    
    async def ask_question(
        self, 
        question: str, 
        language: str = "auto", 
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Ask a legal question
        
        Args:
            question: Legal question to ask
            language: Response language (auto, en, hi)
            max_results: Maximum number of sources to retrieve
            
        Returns:
            Response with answer and sources
        """
        try:
            client = await self._get_client()
            
            payload = {
                "question": question,
                "language": language,
                "max_results": max_results
            }
            
            response = await client.post("/ask", json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Ask question failed: {e}")
            raise
    
    async def generate_judgment(
        self,
        case_facts: str,
        legal_issues: List[str],
        language: str = "auto"
    ) -> Dict[str, Any]:
        """
        Generate a legal judgment
        
        Args:
            case_facts: Facts of the case
            legal_issues: List of legal issues to address
            language: Response language (auto, en, hi)
            
        Returns:
            Structured judgment response
        """
        try:
            client = await self._get_client()
            
            payload = {
                "case_facts": case_facts,
                "legal_issues": legal_issues,
                "language": language
            }
            
            response = await client.post("/judgment", json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Generate judgment failed: {e}")
            raise
    
    async def upload_document(self, file_path: str) -> Dict[str, Any]:
        """
        Upload a PDF document for ingestion
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Upload response with document ID
        """
        try:
            client = await self._get_client()
            
            with open(file_path, "rb") as f:
                files = {"file": (Path(file_path).name, f, "application/pdf")}
                response = await client.post("/documents/upload", files=files)
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Upload document failed: {e}")
            raise
    
    async def add_statutes(self) -> Dict[str, Any]:
        """
        Download and ingest Indian statutes
        
        Returns:
            Ingestion results
        """
        try:
            client = await self._get_client()
            response = await client.post("/sources/add_statutes")
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Add statutes failed: {e}")
            raise
    
    async def get_sources_status(self) -> Dict[str, Any]:
        """
        Get status of ingested sources
        
        Returns:
            Sources status information
        """
        try:
            client = await self._get_client()
            response = await client.get("/sources/status")
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Get sources status failed: {e}")
            raise
    
    async def summarize_document(self, document_id: str, language: str = "auto") -> Dict[str, Any]:
        """
        Generate structured summary of a document
        
        Args:
            document_id: ID of the document to summarize
            language: Response language (auto, en, hi)
            
        Returns:
            Structured summary
        """
        try:
            client = await self._get_client()
            
            payload = {
                "document_id": document_id,
                "language": language
            }
            
            response = await client.post("/summarize", json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Summarize document failed: {e}")
            raise
    
    def close(self):
        """Close the HTTP client"""
        if self.client:
            asyncio.create_task(self.client.aclose())