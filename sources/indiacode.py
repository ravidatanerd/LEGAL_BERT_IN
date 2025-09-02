"""
India Code PDF downloader for legal statutes
"""

import os
import asyncio
import aiohttp
import aiofiles
from typing import Dict, Any, List
from pathlib import Path
from loguru import logger

class IndiaCodeDownloader:
    """Downloader for Indian legal statutes from India Code"""
    
    def __init__(self):
        self.base_url = "https://www.indiacode.nic.in"
        self.download_dir = Path(os.getenv("DOWNLOAD_DIR", "data/downloads"))
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
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
    
    async def download_all_statutes(self) -> Dict[str, Any]:
        """Download all Indian legal statutes"""
        try:
            logger.info("Starting download of Indian legal statutes...")
            
            results = {}
            
            async with aiohttp.ClientSession() as session:
                for statute_id, statute_info in self.statutes.items():
                    try:
                        result = await self._download_statute(session, statute_id, statute_info)
                        results[statute_id] = result
                    except Exception as e:
                        logger.error(f"Failed to download {statute_id}: {e}")
                        results[statute_id] = {"error": str(e)}
            
            logger.info(f"Completed downloading {len(results)} statutes")
            return results
            
        except Exception as e:
            logger.error(f"Statute download failed: {e}")
            raise
    
    async def _download_statute(self, session: aiohttp.ClientSession, 
                              statute_id: str, statute_info: Dict[str, Any]) -> Dict[str, Any]:
        """Download a single statute"""
        try:
            url = statute_info["url"]
            filename = statute_info["filename"]
            file_path = self.download_dir / filename
            
            # Check if file already exists
            if file_path.exists():
                logger.info(f"Statute {statute_id} already exists, skipping download")
                return {
                    "status": "already_exists",
                    "file_path": str(file_path),
                    "size": file_path.stat().st_size
                }
            
            logger.info(f"Downloading {statute_id} from {url}")
            
            # Download file
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    # Save file
                    async with aiofiles.open(file_path, 'wb') as f:
                        await f.write(content)
                    
                    logger.info(f"Successfully downloaded {statute_id} ({len(content)} bytes)")
                    
                    return {
                        "status": "downloaded",
                        "file_path": str(file_path),
                        "size": len(content),
                        "url": url
                    }
                else:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                    
        except Exception as e:
            logger.error(f"Failed to download {statute_id}: {e}")
            raise
    
    async def download_statute(self, statute_id: str) -> Dict[str, Any]:
        """Download a specific statute"""
        if statute_id not in self.statutes:
            raise ValueError(f"Unknown statute: {statute_id}")
        
        statute_info = self.statutes[statute_id]
        
        async with aiohttp.ClientSession() as session:
            return await self._download_statute(session, statute_id, statute_info)
    
    def get_available_statutes(self) -> List[Dict[str, Any]]:
        """Get list of available statutes"""
        return [
            {
                "id": statute_id,
                "name": info["name"],
                "filename": info["filename"],
                "url": info["url"]
            }
            for statute_id, info in self.statutes.items()
        ]
    
    def get_downloaded_statutes(self) -> List[Dict[str, Any]]:
        """Get list of downloaded statutes"""
        downloaded = []
        
        for statute_id, statute_info in self.statutes.items():
            file_path = self.download_dir / statute_info["filename"]
            if file_path.exists():
                downloaded.append({
                    "id": statute_id,
                    "name": statute_info["name"],
                    "filename": statute_info["filename"],
                    "file_path": str(file_path),
                    "size": file_path.stat().st_size,
                    "downloaded": True
                })
            else:
                downloaded.append({
                    "id": statute_id,
                    "name": statute_info["name"],
                    "filename": statute_info["filename"],
                    "downloaded": False
                })
        
        return downloaded