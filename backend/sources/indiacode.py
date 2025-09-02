"""
IndiaCode source for downloading Indian statutes
"""

import os
import httpx
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
from urllib.parse import urlparse

from ingest import DocumentIngester

logger = logging.getLogger(__name__)

class IndiaCodeSource:
    """IndiaCode source for Indian statutes"""
    
    def __init__(self, download_dir: str = None):
        self.download_dir = Path(download_dir or os.getenv("DOWNLOAD_DIR", "data/downloads"))
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.user_agent = os.getenv("HTTP_USER_AGENT", "IndiaLawPro/1.0 (+contact@example.com)")
        self.timeout = int(os.getenv("HTTP_TIMEOUT", "30"))
        
        # Statute URLs
        self.statutes = {
            "IPC_1860": {
                "name": "Indian Penal Code, 1860",
                "url": "https://www.indiacode.nic.in/bitstream/123456789/11091/1/the_indian_penal_code%2C_1860.pdf",
                "filename": "IPC_1860.pdf"
            },
            "CrPC_1973": {
                "name": "Code of Criminal Procedure, 1973",
                "url": "https://www.indiacode.nic.in/bitstream/123456789/15272/1/the_code_of_criminal_procedure%2C_1973.pdf",
                "filename": "CrPC_1973.pdf"
            },
            "Evidence_1872": {
                "name": "Indian Evidence Act, 1872",
                "url": "https://www.indiacode.nic.in/bitstream/123456789/2263/1/A1872-1.pdf",
                "filename": "Evidence_1872.pdf"
            }
        }
        
        self.ingester = None
    
    async def download_and_ingest_statutes(self) -> List[str]:
        """Download and ingest all statutes"""
        try:
            if not self.ingester:
                self.ingester = DocumentIngester()
            
            downloaded_files = []
            
            for statute_id, statute_info in self.statutes.items():
                try:
                    file_path = await self._download_statute(statute_id, statute_info)
                    if file_path:
                        downloaded_files.append(file_path)
                        logger.info(f"Downloaded {statute_info['name']}")
                except Exception as e:
                    logger.error(f"Failed to download {statute_info['name']}: {e}")
            
            # Ingest downloaded files
            if downloaded_files:
                doc_ids = await self.ingester.ingest_multiple_documents(downloaded_files)
                logger.info(f"Ingested {len(doc_ids)} statutes")
                return doc_ids
            
            return []
            
        except Exception as e:
            logger.error(f"Error downloading and ingesting statutes: {e}")
            raise
    
    async def _download_statute(self, statute_id: str, statute_info: Dict[str, str]) -> Optional[Path]:
        """Download a single statute"""
        try:
            file_path = self.download_dir / statute_info["filename"]
            
            # Skip if already downloaded
            if file_path.exists():
                logger.info(f"Statute {statute_id} already exists, skipping download")
                return file_path
            
            # Download file
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent}
            ) as client:
                response = await client.get(statute_info["url"])
                response.raise_for_status()
                
                # Save file
                with open(file_path, "wb") as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded {statute_info['name']} to {file_path}")
                return file_path
                
        except Exception as e:
            logger.error(f"Error downloading statute {statute_id}: {e}")
            return None
    
    async def get_statute_info(self, statute_id: str) -> Optional[Dict[str, str]]:
        """Get information about a statute"""
        return self.statutes.get(statute_id)
    
    async def list_available_statutes(self) -> List[Dict[str, str]]:
        """List all available statutes"""
        return list(self.statutes.values())
    
    async def check_statute_status(self, statute_id: str) -> Dict[str, Any]:
        """Check if a statute is downloaded and ingested"""
        try:
            statute_info = self.statutes.get(statute_id)
            if not statute_info:
                return {"status": "not_found"}
            
            file_path = self.download_dir / statute_info["filename"]
            downloaded = file_path.exists()
            
            # Check if ingested (simplified check)
            ingested = False
            if self.ingester:
                # This is a simplified check - in production, you'd query the retriever
                ingested = True  # Assume ingested if ingester exists
            
            return {
                "statute_id": statute_id,
                "name": statute_info["name"],
                "downloaded": downloaded,
                "ingested": ingested,
                "file_path": str(file_path) if downloaded else None
            }
            
        except Exception as e:
            logger.error(f"Error checking statute status: {e}")
            return {"status": "error", "error": str(e)}