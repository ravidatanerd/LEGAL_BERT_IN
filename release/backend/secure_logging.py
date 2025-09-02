"""
Secure logging configuration that prevents credential leakage
"""
import logging
import re
import os
from typing import Any

class SecureFormatter(logging.Formatter):
    """Custom formatter that masks sensitive information"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Patterns to mask in logs
        self.sensitive_patterns = [
            (r'sk-[a-zA-Z0-9]{20,}', 'sk-****'),  # OpenAI API keys
            (r'Bearer [a-zA-Z0-9._-]+', 'Bearer ****'),  # Bearer tokens
            (r'password["\']?\s*[:=]\s*["\']?[^"\s\n]+', 'password: ****'),  # Passwords
            (r'api_key["\']?\s*[:=]\s*["\']?[^"\s\n]+', 'api_key: ****'),  # API keys
            (r'token["\']?\s*[:=]\s*["\']?[^"\s\n]+', 'token: ****'),  # Tokens
        ]
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with sensitive data masked"""
        # Get the original formatted message
        formatted = super().format(record)
        
        # Apply masking patterns
        for pattern, replacement in self.sensitive_patterns:
            formatted = re.sub(pattern, replacement, formatted, flags=re.IGNORECASE)
        
        return formatted

class SecureFilter(logging.Filter):
    """Filter that blocks log records containing sensitive information"""
    
    def __init__(self):
        super().__init__()
        
        # Patterns that should never appear in logs
        self.blocked_patterns = [
            r'sk-[a-zA-Z0-9]{40,}',  # Full API keys
            r'"password"\s*:\s*"[^"]{8,}"',  # JSON passwords
            r'Authorization:\s*Bearer\s+[a-zA-Z0-9._-]{20,}',  # Auth headers
        ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out records containing sensitive patterns"""
        message = str(record.getMessage())
        
        for pattern in self.blocked_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                # Replace the message with a safe version
                record.msg = "[SENSITIVE DATA FILTERED]"
                record.args = ()
                break
        
        return True

def setup_secure_logging(log_level: str = "INFO"):
    """Setup secure logging configuration"""
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with secure formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Add secure formatter and filter
    formatter = SecureFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SecureFilter())
    
    root_logger.addHandler(console_handler)
    
    # Create file handler for persistent logs (if enabled)
    if os.getenv("ENABLE_FILE_LOGGING", "false").lower() == "true":
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(
            os.path.join(log_dir, "inlegaldesk.log"),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.WARNING)  # Only warnings and errors to file
        file_handler.setFormatter(formatter)
        file_handler.addFilter(SecureFilter())
        
        root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Secure logging configured")

class AuditLogger:
    """Audit logger for security events"""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        
        # Create audit-specific handler
        audit_handler = logging.StreamHandler()
        audit_formatter = SecureFormatter(
            'AUDIT - %(asctime)s - %(message)s'
        )
        audit_handler.setFormatter(audit_formatter)
        self.logger.addHandler(audit_handler)
        self.logger.setLevel(logging.INFO)
    
    def log_file_upload(self, filename: str, file_size: int, client_ip: str = "unknown"):
        """Log file upload event"""
        self.logger.info(f"File upload: {filename} ({file_size} bytes) from {client_ip}")
    
    def log_api_key_usage(self, key_hash: str, endpoint: str):
        """Log API key usage (hashed)"""
        self.logger.info(f"API key used: {key_hash} for {endpoint}")
    
    def log_security_event(self, event: str, details: str = ""):
        """Log security-related events"""
        self.logger.warning(f"Security event: {event} - {details}")
    
    def log_rate_limit(self, client_ip: str, endpoint: str):
        """Log rate limiting events"""
        self.logger.warning(f"Rate limit exceeded: {client_ip} on {endpoint}")

# Global audit logger instance
audit_logger = AuditLogger()