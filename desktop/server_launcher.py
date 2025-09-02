"""
Server launcher for the backend
"""

import os
import sys
import subprocess
import logging
import asyncio
import signal
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class ServerLauncher:
    """Launch and manage the backend server"""
    
    def __init__(self, server_dir: str = None):
        self.server_dir = Path(server_dir or "server")
        self.process: Optional[subprocess.Popen] = None
        self.port = int(os.getenv("BACKEND_PORT", "8877"))
        self.logger = logging.getLogger(__name__)
    
    def is_server_running(self) -> bool:
        """Check if server is running"""
        return self.process is not None and self.process.poll() is None
    
    def start_server(self) -> bool:
        """Start the backend server"""
        try:
            if self.is_server_running():
                self.logger.info("Server already running")
                return True
            
            # Check if server files exist
            app_py = self.server_dir / "app.py"
            if not app_py.exists():
                self.logger.error(f"Server files not found in {self.server_dir}")
                return False
            
            # Start server
            env = os.environ.copy()
            env["BACKEND_PORT"] = str(self.port)
            
            self.process = subprocess.Popen(
                [sys.executable, str(app_py)],
                cwd=str(self.server_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.logger.info(f"Started server on port {self.port} (PID: {self.process.pid})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the backend server"""
        try:
            if self.process and self.is_server_running():
                self.logger.info("Stopping server...")
                
                # Try graceful shutdown first
                self.process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    self.logger.warning("Graceful shutdown failed, force killing...")
                    self.process.kill()
                    self.process.wait()
                
                self.logger.info("Server stopped")
            
            self.process = None
            
        except Exception as e:
            self.logger.error(f"Error stopping server: {e}")
    
    def get_server_logs(self) -> str:
        """Get server logs"""
        if self.process and self.is_server_running():
            try:
                # Read available output
                stdout, stderr = self.process.communicate(timeout=0.1)
                return f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
            except subprocess.TimeoutExpired:
                return "Server is running (no new logs)"
        return "Server not running"
    
    def __del__(self):
        """Cleanup on destruction"""
        self.stop_server()