"""
API client for communicating with the backend
"""

import os
import json
import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)

class APIClient:
    """Client for backend API communication"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("BACKEND_URL", "http://127.0.0.1:8877")
        self.session = None
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check backend health"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def get_sources_status(self) -> Dict[str, Any]:
        """Get sources status"""
        try:
            async with self.session.get(f"{self.base_url}/sources/status") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(f"Sources status failed: {e}")
            return {"error": str(e)}
    
    async def add_statutes(self) -> Dict[str, Any]:
        """Add Indian statutes"""
        try:
            async with self.session.post(f"{self.base_url}/sources/add_statutes") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(f"Add statutes failed: {e}")
            return {"error": str(e)}
    
    async def sync_sources(self) -> Dict[str, Any]:
        """Sync all sources"""
        try:
            async with self.session.post(f"{self.base_url}/sources/sync") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(f"Sync sources failed: {e}")
            return {"error": str(e)}
    
    async def upload_document(self, file_path: Path) -> Dict[str, Any]:
        """Upload a document"""
        try:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=file_path.name)
                
                async with self.session.post(f"{self.base_url}/upload", data=data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(f"Upload document failed: {e}")
            return {"error": str(e)}
    
    async def ask_question(
        self, 
        question: str, 
        language: str = "auto", 
        max_sources: int = 5
    ) -> Dict[str, Any]:
        """Ask a question"""
        try:
            payload = {
                "question": question,
                "language": language,
                "max_sources": max_sources
            }
            
            async with self.session.post(
                f"{self.base_url}/ask", 
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(f"Ask question failed: {e}")
            return {"error": str(e)}
    
    async def summarize_documents(
        self, 
        document_ids: List[str], 
        language: str = "auto"
    ) -> Dict[str, Any]:
        """Summarize documents"""
        try:
            payload = {
                "document_ids": document_ids,
                "language": language
            }
            
            async with self.session.post(
                f"{self.base_url}/summarize", 
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(f"Summarize documents failed: {e}")
            return {"error": str(e)}
    
    async def generate_judgment(
        self, 
        case_facts: str, 
        issues: List[str], 
        language: str = "auto"
    ) -> Dict[str, Any]:
        """Generate judgment"""
        try:
            payload = {
                "case_facts": case_facts,
                "issues": issues,
                "language": language
            }
            
            async with self.session.post(
                f"{self.base_url}/judgment", 
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(f"Generate judgment failed: {e}")
            return {"error": str(e)}
    
    async def list_documents(self) -> Dict[str, Any]:
        """List all documents"""
        try:
            async with self.session.get(f"{self.base_url}/documents") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(f"List documents failed: {e}")
            return {"error": str(e)}
    
    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Delete a document"""
        try:
            async with self.session.delete(f"{self.base_url}/documents/{document_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(f"Delete document failed: {e}")
            return {"error": str(e)}