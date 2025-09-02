"""
Server launcher for the desktop application
"""
import os
import sys
import subprocess
import logging
import time
from pathlib import Path
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

class ServerLauncher:
    """Handles launching and managing the backend server"""
    
    def __init__(self):
        self.server_process: Optional[subprocess.Popen] = None
        self.backend_url = os.getenv("BACKEND_URL")
        self.backend_port = int(os.getenv("BACKEND_PORT", 8877))
        
    def start_server(self) -> bool:
        """
        Start the backend server
        
        Returns:
            True if server started successfully, False otherwise
        """
        try:
            # If BACKEND_URL is set, assume external server
            if self.backend_url:
                logger.info(f"Using external backend at {self.backend_url}")
                return self._test_connection()
            
            # Find server directory
            server_dir = self._find_server_directory()
            if not server_dir:
                logger.error("Backend server files not found")
                return False
            
            # Check if server is already running
            if self._test_connection():
                logger.info("Backend server already running")
                return True
            
            # Start the server
            return self._launch_local_server(server_dir)
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    def _find_server_directory(self) -> Optional[Path]:
        """Find the backend server directory"""
        possible_paths = [
            Path(__file__).parent / "server",  # Bundled with desktop app
            Path(__file__).parent.parent / "backend",  # Development mode
        ]
        
        for path in possible_paths:
            if path.exists() and (path / "app.py").exists():
                logger.info(f"Found server directory: {path}")
                return path
        
        return None
    
    def _launch_local_server(self, server_dir: Path) -> bool:
        """Launch the local server process"""
        try:
            # Prepare environment
            env = os.environ.copy()
            
            # Add server directory to Python path
            if "PYTHONPATH" in env:
                env["PYTHONPATH"] = f"{server_dir}{os.pathsep}{env['PYTHONPATH']}"
            else:
                env["PYTHONPATH"] = str(server_dir)
            
            # Launch server
            cmd = [
                sys.executable, "-m", "uvicorn", "app:app",
                "--host", "127.0.0.1",
                "--port", str(self.backend_port),
                "--log-level", "info"
            ]
            
            logger.info(f"Starting server with command: {' '.join(cmd)}")
            
            self.server_process = subprocess.Popen(
                cmd,
                cwd=server_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Wait for server to start
            for attempt in range(30):  # 30 second timeout
                time.sleep(1)
                if self._test_connection():
                    logger.info("Backend server started successfully")
                    return True
                
                # Check if process died
                if self.server_process.poll() is not None:
                    stdout, stderr = self.server_process.communicate()
                    logger.error(f"Server process died: {stderr.decode()}")
                    return False
            
            logger.error("Server failed to start within timeout")
            self.stop_server()
            return False
            
        except Exception as e:
            logger.error(f"Failed to launch server: {e}")
            return False
    
    def _test_connection(self) -> bool:
        """Test connection to backend server"""
        try:
            url = self.backend_url or f"http://127.0.0.1:{self.backend_port}"
            
            # Use synchronous request for simplicity
            import requests
            response = requests.get(f"{url}/health", timeout=5)
            return response.status_code == 200
            
        except Exception:
            return False
    
    def stop_server(self):
        """Stop the backend server"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
                logger.info("Backend server stopped")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                logger.warning("Backend server force killed")
            except Exception as e:
                logger.error(f"Failed to stop server: {e}")
            
            self.server_process = None
    
    def __del__(self):
        """Cleanup on destruction"""
        self.stop_server()