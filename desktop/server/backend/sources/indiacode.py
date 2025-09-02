"""
IndiaCode statute downloader and ingestor
"""
import os
import logging
import asyncio
from typing import Dict, List, Any
from pathlib import Path
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

class IndiaCodeDownloader:
    """Downloads and ingests Indian statutes from IndiaCode"""
    
    # Predefined statute URLs
    STATUTES = {
        "IPC_1860": {
            "name": "Indian Penal Code, 1860",
            "url": "https://www.indiacode.nic.in/bitstream/123456789/11091/1/the_indian_penal_code%2C_1860.pdf"
        },
        "CrPC_1973": {
            "name": "Code of Criminal Procedure, 1973", 
            "url": "https://www.indiacode.nic.in/bitstream/123456789/15272/1/the_code_of_criminal_procedure%2C_1973.pdf"
        },
        "Evidence_1872": {
            "name": "Indian Evidence Act, 1872",
            "url": "https://www.indiacode.nic.in/bitstream/123456789/2263/1/A1872-1.pdf"
        }
    }
    
    def __init__(self):
        self.download_dir = Path(os.getenv("DOWNLOAD_DIR", "data/downloads"))
        self.download_dir.mkdir(exist_ok=True)
        
        self.user_agent = os.getenv("HTTP_USER_AGENT", "IndiaLawPro/1.0 (+contact@example.com)")
        self.timeout = int(os.getenv("HTTP_TIMEOUT", 30))
    
    async def download_and_ingest(self) -> Dict[str, Any]:
        """Download all statutes and ingest them"""
        results = {}
        
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={"User-Agent": self.user_agent}
        ) as client:
            
            for statute_id, statute_info in self.STATUTES.items():
                try:
                    logger.info(f"Processing {statute_info['name']}")
                    
                    # Download PDF
                    file_path = await self._download_statute(
                        client, statute_id, statute_info
                    )
                    
                    if file_path:
                        # Import here to avoid circular imports
                        from ingest import DocumentIngestor
                        
                        # Ingest the document
                        ingestor = DocumentIngestor()
                        doc_id = await ingestor.ingest_document(str(file_path))
                        
                        results[statute_id] = {
                            "status": "success",
                            "doc_id": doc_id,
                            "file_path": str(file_path),
                            "name": statute_info["name"]
                        }
                    else:
                        results[statute_id] = {
                            "status": "failed",
                            "error": "Download failed",
                            "name": statute_info["name"]
                        }
                        
                except Exception as e:
                    logger.error(f"Failed to process {statute_info['name']}: {e}")
                    results[statute_id] = {
                        "status": "error",
                        "error": str(e),
                        "name": statute_info["name"]
                    }
        
        return results
    
    async def _download_statute(
        self,
        client: httpx.AsyncClient,
        statute_id: str,
        statute_info: Dict[str, str]
    ) -> Optional[Path]:
        """Download a single statute PDF"""
        try:
            file_path = self.download_dir / f"{statute_id}.pdf"
            
            # Skip if already downloaded
            if file_path.exists():
                logger.info(f"Statute {statute_id} already downloaded")
                return file_path
            
            logger.info(f"Downloading {statute_info['name']} from {statute_info['url']}")
            
            # Download with streaming
            async with client.stream("GET", statute_info["url"]) as response:
                if response.status_code != 200:
                    logger.error(f"Failed to download {statute_id}: HTTP {response.status_code}")
                    return None
                
                # Save to file
                with open(file_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
            
            logger.info(f"Successfully downloaded {statute_id} to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Download failed for {statute_id}: {e}")
            return None