"""
Server launcher for the legal research backend
"""

import os
import sys
import subprocess
import threading
import time
from typing import Optional
from pathlib import Path
from loguru import logger

class ServerLauncher:
    """Launcher for the FastAPI backend server"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.server_thread: Optional[threading.Thread] = None
        self.is_running = False
        
        # Server configuration
        self.host = "127.0.0.1"
        self.port = 8877
        self.backend_dir = self._find_backend_directory()
    
    def _find_backend_directory(self) -> Path:
        """Find the backend directory"""
        # Look for backend files relative to desktop directory
        desktop_dir = Path(__file__).parent
        backend_dir = desktop_dir.parent  # Go up one level from desktop/
        
        # Check if backend files exist
        if (backend_dir / "app.py").exists():
            return backend_dir
        
        # Alternative: look for server directory
        server_dir = desktop_dir / "server"
        if server_dir.exists():
            return server_dir
        
        # Fallback to current directory
        return Path.cwd()
    
    def start_server(self) -> bool:
        """Start the backend server"""
        try:
            if self.is_running:
                logger.info("Server is already running")
                return True
            
            logger.info(f"Starting server from: {self.backend_dir}")
            
            # Check if Python is available
            python_cmd = self._find_python_executable()
            if not python_cmd:
                raise Exception("Python executable not found")
            
            # Check if required files exist
            app_file = self.backend_dir / "app.py"
            if not app_file.exists():
                raise Exception(f"Backend app.py not found at: {app_file}")
            
            # Prepare environment
            env = os.environ.copy()
            env["BACKEND_PORT"] = str(self.port)
            
            # Start server in a separate thread
            self.server_thread = threading.Thread(
                target=self._run_server,
                args=(python_cmd, app_file, env),
                daemon=True
            )
            self.server_thread.start()
            
            # Wait a moment for server to start
            time.sleep(2)
            
            # Check if server started successfully
            if self._check_server_health():
                self.is_running = True
                logger.info(f"Server started successfully on {self.host}:{self.port}")
                return True
            else:
                logger.error("Server failed to start or is not responding")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    def _run_server(self, python_cmd: str, app_file: Path, env: dict):
        """Run the server process"""
        try:
            # Change to backend directory
            os.chdir(self.backend_dir)
            
            # Start uvicorn server
            cmd = [
                python_cmd, "-m", "uvicorn",
                "app:app",
                "--host", self.host,
                "--port", str(self.port),
                "--reload"
            ]
            
            logger.info(f"Running command: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor server output
            while self.process.poll() is None:
                output = self.process.stdout.readline()
                if output:
                    logger.info(f"Server: {output.strip()}")
                
                error = self.process.stderr.readline()
                if error:
                    logger.error(f"Server error: {error.strip()}")
            
            # Server process ended
            return_code = self.process.returncode
            logger.info(f"Server process ended with return code: {return_code}")
            
        except Exception as e:
            logger.error(f"Server execution failed: {e}")
        finally:
            self.is_running = False
    
    def stop_server(self) -> bool:
        """Stop the backend server"""
        try:
            if not self.is_running or not self.process:
                logger.info("Server is not running")
                return True
            
            logger.info("Stopping server...")
            
            # Terminate the process
            self.process.terminate()
            
            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                logger.warning("Graceful shutdown failed, force killing server")
                self.process.kill()
                self.process.wait()
            
            self.is_running = False
            self.process = None
            
            logger.info("Server stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop server: {e}")
            return False
    
    def _find_python_executable(self) -> Optional[str]:
        """Find Python executable"""
        # Try different Python commands
        python_commands = ["python", "python3", "py"]
        
        for cmd in python_commands:
            try:
                result = subprocess.run(
                    [cmd, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"Found Python: {cmd}")
                    return cmd
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        return None
    
    def _check_server_health(self) -> bool:
        """Check if server is healthy"""
        try:
            import requests
            response = requests.get(
                f"http://{self.host}:{self.port}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False
    
    def get_server_status(self) -> dict:
        """Get server status information"""
        return {
            "is_running": self.is_running,
            "host": self.host,
            "port": self.port,
            "backend_dir": str(self.backend_dir),
            "process_id": self.process.pid if self.process else None
        }
    
    def is_server_healthy(self) -> bool:
        """Check if server is healthy (synchronous)"""
        return self._check_server_health()
    
    def __del__(self):
        """Cleanup on destruction"""
        if self.is_running:
            self.stop_server()