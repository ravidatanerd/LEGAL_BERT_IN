"""
API client for communicating with the legal research backend
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional
from loguru import logger

class LegalAPIClient:
    """Client for Legal Research API"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8877"):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.connected = False
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
        except aiohttp.ClientError as e:
            raise Exception(f"Connection error: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        try:
            return await self._make_request("GET", "/health")
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def ask_question(self, question: str, language: str = "auto", 
                          max_results: int = 10) -> Dict[str, Any]:
        """Ask a legal question"""
        payload = {
            "question": question,
            "language": language,
            "max_results": max_results
        }
        
        try:
            return await self._make_request(
                "POST", "/ask",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            logger.error(f"Question asking failed: {e}")
            return {"error": str(e)}
    
    async def generate_summary(self, document_id: str, language: str = "auto") -> Dict[str, Any]:
        """Generate document summary"""
        payload = {
            "document_id": document_id,
            "language": language
        }
        
        try:
            return await self._make_request(
                "POST", "/summarize",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return {"error": str(e)}
    
    async def generate_judgment(self, facts: str, issues: List[str], 
                               language: str = "auto", court_type: str = "high_court") -> Dict[str, Any]:
        """Generate legal judgment"""
        payload = {
            "case_facts": facts,
            "legal_issues": issues,
            "language": language,
            "court_type": court_type
        }
        
        try:
            return await self._make_request(
                "POST", "/judgment",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            logger.error(f"Judgment generation failed: {e}")
            return {"error": str(e)}
    
    async def ingest_document(self, file_path: str, metadata: Optional[str] = None) -> Dict[str, Any]:
        """Ingest a document"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {}
                if metadata:
                    data['metadata'] = metadata
                
                return await self._make_request(
                    "POST", "/ingest",
                    data=data,
                    files=files
                )
        except Exception as e:
            logger.error(f"Document ingestion failed: {e}")
            return {"error": str(e)}
    
    async def add_statutes(self) -> Dict[str, Any]:
        """Add legal statutes"""
        try:
            return await self._make_request("POST", "/sources/add_statutes")
        except Exception as e:
            logger.error(f"Statutes addition failed: {e}")
            return {"error": str(e)}
    
    async def sync_sources(self, source_type: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Sync legal sources"""
        payload = {
            "source_type": source_type,
            "parameters": parameters or {}
        }
        
        try:
            return await self._make_request(
                "POST", "/sources/sync",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            logger.error(f"Source sync failed: {e}")
            return {"error": str(e)}
    
    async def get_sources_status(self) -> Dict[str, Any]:
        """Get sources status"""
        try:
            return await self._make_request("GET", "/sources/status")
        except Exception as e:
            logger.error(f"Sources status check failed: {e}")
            return {"error": str(e)}
    
    async def export_chat(self, chat_id: str, format: str = "markdown") -> Dict[str, Any]:
        """Export chat transcript"""
        try:
            return await self._make_request(
                "GET", f"/export/chat/{chat_id}",
                params={"format": format}
            )
        except Exception as e:
            logger.error(f"Chat export failed: {e}")
            return {"error": str(e)}
    
    def is_connected(self) -> bool:
        """Check if client is connected (synchronous)"""
        try:
            # This is a simplified check - in a real implementation,
            # you might want to use a proper async check
            import requests
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    async def test_connection(self) -> bool:
        """Test connection to API"""
        try:
            async with self:
                health = await self.health_check()
                return health.get("status") == "healthy"
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False