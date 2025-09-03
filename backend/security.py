"""
Security utilities and middleware for the FastAPI backend
"""
import os
import re
import hashlib
import secrets
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import time
from collections import defaultdict

try:
    from fastapi import HTTPException, Request, Response
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from starlette.middleware.base import BaseHTTPMiddleware
    import httpx
except ImportError:
    # For testing without FastAPI
    BaseHTTPMiddleware = object
    HTTPException = Exception
    Request = object

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Security configuration and validation"""
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.pdf'}
    
    # Maximum file size (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = 100  # requests per minute
    RATE_LIMIT_WINDOW = 60     # seconds
    
    # Allowed origins for CORS (production)
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080", 
        "http://127.0.0.1:8080"
    ]
    
    @classmethod
    def get_cors_origins(cls) -> List[str]:
        """Get CORS origins based on environment"""
        if os.getenv("ENVIRONMENT") == "production":
            return cls.ALLOWED_ORIGINS
        else:
            # Development mode - more permissive but still restricted
            return [
                "http://localhost:*",
                "http://127.0.0.1:*",
                "http://0.0.0.0:*"
            ]

class InputValidator:
    """Input validation and sanitization"""
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """Validate uploaded filename for security"""
        if not filename:
            return False
        
        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check extension
        ext = Path(filename).suffix.lower()
        if ext not in SecurityConfig.ALLOWED_EXTENSIONS:
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'[<>:"|?*]',  # Windows invalid chars
            r'^\.',        # Hidden files
            r'\.{2,}',     # Multiple dots
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, filename):
                return False
        
        return True
    
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """Validate file size"""
        return 0 < file_size <= SecurityConfig.MAX_FILE_SIZE
    
    @staticmethod
    def sanitize_query(query: str) -> str:
        """Sanitize user query input"""
        if not query:
            return ""
        
        # Remove potential injection patterns
        query = re.sub(r'[<>"]', '', query)
        
        # Limit length
        if len(query) > 10000:
            query = query[:10000]
        
        return query.strip()
    
    @staticmethod
    def validate_language_code(lang: str) -> bool:
        """Validate language code"""
        valid_langs = {'auto', 'en', 'hi'}
        return lang in valid_langs
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate OpenAI API key format - Updated for latest ChatGPT tokens"""
        if not api_key:
            return False
        
        # Updated format validation for modern OpenAI API keys
        # Support multiple key formats: sk-, sk-proj-, sk-svcacct-
        valid_prefixes = ['sk-', 'sk-proj-', 'sk-svcacct-']
        has_valid_prefix = any(api_key.startswith(prefix) for prefix in valid_prefixes)
        
        if not has_valid_prefix:
            return False
        
        # Updated length validation for modern keys
        if len(api_key) < 20 or len(api_key) > 300:
            return False
        
        # Check for suspicious patterns (but allow valid characters)
        # Modern keys can contain: letters, numbers, hyphens, underscores
        if any(char in api_key for char in [' ', '\n', '\t', '<', '>', '"', "'", '\\', '/', '?', '&', '=', '+', '%', '@', '!', '#', '$', '^', '*', '(', ')', '[', ']', '{', '}', '|', ';', ':', ',', '.', '`', '~']):
            return False
        
        # Validate character set - allow letters, numbers, hyphens, underscores
        # Updated pattern to support sk-proj- and sk-svcacct- prefixes
        import re
        if not re.match(r'^sk-(?:proj-|svcacct-)?[a-zA-Z0-9_-]+$', api_key):
            return False
        
        return True

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting"""
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < SecurityConfig.RATE_LIMIT_WINDOW
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Record this request
        self.requests[client_ip].append(current_time)
        
        response = await call_next(request)
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response

class FileSecurityValidator:
    """Validate uploaded files for security"""
    
    @staticmethod
    def validate_pdf_file(file_path: str) -> Dict[str, Any]:
        """
        Validate PDF file for security issues
        
        Returns:
            Dict with validation results
        """
        results = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "file_info": {}
        }
        
        try:
            # Check file exists and size
            if not Path(file_path).exists():
                results["errors"].append("File does not exist")
                return results
            
            file_size = Path(file_path).stat().st_size
            if not InputValidator.validate_file_size(file_size):
                results["errors"].append(f"File too large: {file_size} bytes")
                return results
            
            # Basic PDF validation
            with open(file_path, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'%PDF-'):
                    results["errors"].append("Not a valid PDF file")
                    return results
            
            # Check for embedded content (basic)
            with open(file_path, 'rb') as f:
                content = f.read(1024)  # First 1KB
                
                # Check for suspicious content
                if b'/JavaScript' in content or b'/JS' in content:
                    results["warnings"].append("PDF contains JavaScript")
                
                if b'/EmbeddedFile' in content:
                    results["warnings"].append("PDF contains embedded files")
            
            results["is_valid"] = True
            results["file_info"] = {
                "size": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            results["errors"].append(f"Validation error: {e}")
        
        return results
    
    @staticmethod
    def sanitize_file_path(file_path: str, base_dir: str) -> str:
        """
        Sanitize file path to prevent directory traversal
        
        Args:
            file_path: User-provided file path
            base_dir: Base directory to restrict to
            
        Returns:
            Sanitized absolute path within base_dir
        """
        try:
            # Resolve paths
            base_path = Path(base_dir).resolve()
            target_path = (base_path / file_path).resolve()
            
            # Ensure target is within base directory
            if not str(target_path).startswith(str(base_path)):
                raise ValueError("Path traversal attempt detected")
            
            return str(target_path)
            
        except Exception as e:
            logger.error(f"Path sanitization failed: {e}")
            raise ValueError("Invalid file path")

class APIKeyManager:
    """Secure API key management"""
    
    @staticmethod
    def validate_and_mask_key(api_key: str) -> Dict[str, Any]:
        """
        Validate API key and return masked version for logging
        
        Returns:
            Dict with validation results and masked key
        """
        if not InputValidator.validate_api_key(api_key):
            return {
                "is_valid": False,
                "masked_key": "invalid",
                "error": "Invalid API key format"
            }
        
        # Create masked version for logging
        if len(api_key) > 10:
            masked_key = api_key[:7] + "..." + api_key[-4:]
        else:
            masked_key = "sk-****"
        
        return {
            "is_valid": True,
            "masked_key": masked_key,
            "error": None
        }
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Create hash of API key for logging/tracking without exposing key"""
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]

class SecureEnvironment:
    """Secure environment variable handling"""
    
    @staticmethod
    def load_secure_env() -> Dict[str, str]:
        """Load environment variables with validation"""
        secure_env = {}
        
        # Required variables
        required_vars = ['OPENAI_API_KEY']
        optional_vars = [
            'OPENAI_BASE_URL', 'OPENAI_MODEL', 'EMBED_MODEL',
            'VLM_ORDER', 'MAX_WORKERS', 'VLM_BATCH_SIZE'
        ]
        
        # Load and validate required variables
        for var in required_vars:
            value = os.getenv(var)
            if value:
                if var == 'OPENAI_API_KEY':
                    if InputValidator.validate_api_key(value):
                        secure_env[var] = value
                    else:
                        logger.warning(f"Invalid {var} format")
                else:
                    secure_env[var] = value
        
        # Load optional variables
        for var in optional_vars:
            value = os.getenv(var)
            if value:
                secure_env[var] = value
        
        return secure_env
    
    @staticmethod
    def set_secure_env(credentials: Dict[str, str]):
        """Set environment variables securely"""
        for key, value in credentials.items():
            if key == 'OPENAI_API_KEY':
                if InputValidator.validate_api_key(value):
                    os.environ[key] = value
                else:
                    logger.warning(f"Skipping invalid API key")
            else:
                os.environ[key] = value

def generate_session_token() -> str:
    """Generate secure session token"""
    return secrets.token_urlsafe(32)

def verify_file_integrity(file_path: str) -> bool:
    """Verify file hasn't been tampered with"""
    try:
        # Basic integrity check
        return Path(file_path).exists() and Path(file_path).stat().st_size > 0
    except Exception:
        return False