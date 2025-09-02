"""
Security validation utilities for the desktop application
"""
import os
import re
import hashlib
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class DesktopSecurityValidator:
    """Security validation for desktop application"""
    
    # Allowed file extensions for upload
    ALLOWED_EXTENSIONS = {'.pdf'}
    
    # Maximum file size (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024
    
    # Trusted domains for API endpoints
    TRUSTED_DOMAINS = {
        'api.openai.com',
        'localhost',
        '127.0.0.1',
        '0.0.0.0'
    }
    
    @classmethod
    def validate_file_for_upload(cls, file_path: str) -> Dict[str, Any]:
        """
        Validate file before upload
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            Dict with validation results
        """
        result = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "file_info": {}
        }
        
        try:
            path = Path(file_path)
            
            # Check if file exists
            if not path.exists():
                result["errors"].append("File does not exist")
                return result
            
            # Check file extension
            if path.suffix.lower() not in cls.ALLOWED_EXTENSIONS:
                result["errors"].append(f"Unsupported file type: {path.suffix}")
                return result
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > cls.MAX_FILE_SIZE:
                result["errors"].append(f"File too large: {file_size / (1024*1024):.1f} MB")
                return result
            
            if file_size == 0:
                result["errors"].append("File is empty")
                return result
            
            # Basic PDF validation
            with open(file_path, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'%PDF-'):
                    result["errors"].append("Not a valid PDF file")
                    return result
            
            # Check for potentially suspicious content
            with open(file_path, 'rb') as f:
                content = f.read(2048)  # First 2KB
                
                if b'/JavaScript' in content or b'/JS' in content:
                    result["warnings"].append("PDF contains JavaScript")
                
                if b'/EmbeddedFile' in content:
                    result["warnings"].append("PDF contains embedded files")
                
                if b'/Launch' in content:
                    result["warnings"].append("PDF contains launch actions")
            
            result["is_valid"] = True
            result["file_info"] = {
                "name": path.name,
                "size": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "extension": path.suffix.lower()
            }
            
        except Exception as e:
            result["errors"].append(f"Validation error: {e}")
        
        return result
    
    @classmethod
    def validate_api_url(cls, url: str) -> Dict[str, Any]:
        """
        Validate API URL for security
        
        Args:
            url: URL to validate
            
        Returns:
            Dict with validation results
        """
        result = {
            "is_valid": False,
            "errors": [],
            "warnings": []
        }
        
        try:
            if not url:
                result["errors"].append("URL cannot be empty")
                return result
            
            # Parse URL
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ['http', 'https']:
                result["errors"].append("URL must use HTTP or HTTPS")
                return result
            
            # Warn about HTTP in production
            if parsed.scheme == 'http' and parsed.hostname not in ['localhost', '127.0.0.1']:
                result["warnings"].append("HTTP is not secure for external APIs")
            
            # Check hostname
            if not parsed.hostname:
                result["errors"].append("Invalid hostname")
                return result
            
            # Check for suspicious patterns
            if any(char in url for char in ['<', '>', '"', "'"]):
                result["errors"].append("URL contains invalid characters")
                return result
            
            # Check if domain is trusted (for external APIs)
            if parsed.hostname not in cls.TRUSTED_DOMAINS:
                result["warnings"].append(f"Untrusted domain: {parsed.hostname}")
            
            result["is_valid"] = True
            
        except Exception as e:
            result["errors"].append(f"URL validation error: {e}")
        
        return result
    
    @classmethod
    def validate_api_key(cls, api_key: str) -> Dict[str, Any]:
        """
        Validate API key format and security
        
        Args:
            api_key: API key to validate
            
        Returns:
            Dict with validation results
        """
        result = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "masked_key": ""
        }
        
        try:
            if not api_key:
                result["errors"].append("API key cannot be empty")
                return result
            
            # Check basic format
            if not api_key.startswith('sk-'):
                result["errors"].append("OpenAI API keys must start with 'sk-'")
                return result
            
            # Check length
            if len(api_key) < 20:
                result["errors"].append("API key too short")
                return result
            
            if len(api_key) > 200:
                result["errors"].append("API key too long")
                return result
            
            # Check for invalid characters
            if not re.match(r'^sk-[a-zA-Z0-9]+$', api_key):
                result["errors"].append("API key contains invalid characters")
                return result
            
            # Create masked version
            if len(api_key) > 10:
                result["masked_key"] = api_key[:7] + "..." + api_key[-4:]
            else:
                result["masked_key"] = "sk-****"
            
            result["is_valid"] = True
            
        except Exception as e:
            result["errors"].append(f"Validation error: {e}")
        
        return result
    
    @classmethod
    def sanitize_user_input(cls, text: str, max_length: int = 10000) -> str:
        """
        Sanitize user input text
        
        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Remove potentially dangerous characters
        text = re.sub(r'[<>"\']', '', text)
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @classmethod
    def validate_file_path(cls, file_path: str, base_dir: Optional[str] = None) -> bool:
        """
        Validate file path for security
        
        Args:
            file_path: File path to validate
            base_dir: Base directory to restrict to (optional)
            
        Returns:
            True if path is safe, False otherwise
        """
        try:
            path = Path(file_path)
            
            # Check for path traversal
            if '..' in str(path) or str(path).startswith('/'):
                return False
            
            # If base directory specified, ensure path is within it
            if base_dir:
                base_path = Path(base_dir).resolve()
                full_path = (base_path / path).resolve()
                
                if not str(full_path).startswith(str(base_path)):
                    return False
            
            return True
            
        except Exception:
            return False

class SecureFileHandler:
    """Secure file handling utilities"""
    
    @staticmethod
    def create_secure_temp_file(content: bytes, extension: str = ".tmp") -> str:
        """
        Create a secure temporary file
        
        Args:
            content: File content
            extension: File extension
            
        Returns:
            Path to created file
        """
        import tempfile
        import secrets
        
        # Create secure temp directory
        temp_dir = Path(tempfile.gettempdir()) / "inlegaldesk"
        temp_dir.mkdir(exist_ok=True)
        
        # Generate secure filename
        filename = f"secure_{secrets.token_hex(8)}{extension}"
        file_path = temp_dir / filename
        
        # Write content securely
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Set restrictive permissions (Unix-like systems)
        if os.name != 'nt':
            os.chmod(file_path, 0o600)
        
        return str(file_path)
    
    @staticmethod
    def secure_delete_file(file_path: str) -> bool:
        """
        Securely delete a file
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return True
            
            # Overwrite file content before deletion (basic secure delete)
            file_size = path.stat().st_size
            
            with open(file_path, 'wb') as f:
                f.write(os.urandom(min(file_size, 1024 * 1024)))  # Max 1MB overwrite
            
            # Delete file
            path.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Secure delete failed: {e}")
            return False
    
    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """
        Get SHA-256 hash of file for integrity checking
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex digest of file hash
        """
        try:
            hasher = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            
            return hasher.hexdigest()
            
        except Exception as e:
            logger.error(f"Failed to hash file: {e}")
            return ""

class SecurityAudit:
    """Security audit utilities for desktop app"""
    
    @staticmethod
    def audit_application_security() -> Dict[str, Any]:
        """
        Perform security audit of the application
        
        Returns:
            Dict with audit results
        """
        audit_results = {
            "overall_status": "unknown",
            "checks": {},
            "recommendations": []
        }
        
        try:
            # Check credential storage
            cred_manager = SecureCredentialManager()
            if cred_manager.credentials_exist():
                audit_results["checks"]["credentials_encrypted"] = True
            else:
                audit_results["checks"]["credentials_encrypted"] = None
                audit_results["recommendations"].append("Configure API credentials for full functionality")
            
            # Check file permissions
            config_dir = cred_manager.config_dir
            if config_dir.exists():
                # Check if config directory has appropriate permissions
                if os.name != 'nt':
                    stat_info = config_dir.stat()
                    permissions = oct(stat_info.st_mode)[-3:]
                    audit_results["checks"]["config_permissions"] = permissions in ['700', '750']
                else:
                    audit_results["checks"]["config_permissions"] = True  # Windows handles this differently
            
            # Check for debug mode
            debug_enabled = os.getenv("DEBUG", "false").lower() == "true"
            audit_results["checks"]["debug_disabled"] = not debug_enabled
            if debug_enabled:
                audit_results["recommendations"].append("Disable debug mode in production")
            
            # Check for secure connections
            openai_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            audit_results["checks"]["secure_api_connection"] = openai_url.startswith("https://")
            if not openai_url.startswith("https://"):
                audit_results["recommendations"].append("Use HTTPS for API connections")
            
            # Overall status
            passed_checks = sum(1 for v in audit_results["checks"].values() if v is True)
            total_checks = len([v for v in audit_results["checks"].values() if v is not None])
            
            if total_checks == 0:
                audit_results["overall_status"] = "unknown"
            elif passed_checks == total_checks:
                audit_results["overall_status"] = "secure"
            elif passed_checks >= total_checks * 0.8:
                audit_results["overall_status"] = "mostly_secure"
            else:
                audit_results["overall_status"] = "needs_attention"
            
        except Exception as e:
            logger.error(f"Security audit failed: {e}")
            audit_results["checks"]["audit_error"] = str(e)
            audit_results["overall_status"] = "error"
        
        return audit_results