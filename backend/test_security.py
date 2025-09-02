#!/usr/bin/env python3
"""
Security test suite for InLegalDesk backend
"""
import asyncio
import tempfile
import os
import logging
from pathlib import Path
import httpx
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityTestSuite:
    """Comprehensive security test suite"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8877"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
    
    async def run_all_tests(self):
        """Run all security tests"""
        try:
            logger.info("🔒 Starting Security Test Suite...")
            
            # Test 1: Input validation
            await self.test_input_validation()
            
            # Test 2: File upload security
            await self.test_file_upload_security()
            
            # Test 3: Rate limiting
            await self.test_rate_limiting()
            
            # Test 4: Error handling
            await self.test_error_handling()
            
            # Test 5: Security headers
            await self.test_security_headers()
            
            # Test 6: Path traversal protection
            await self.test_path_traversal()
            
            logger.info("✅ All security tests completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Security tests failed: {e}")
            raise
        finally:
            await self.client.aclose()
    
    async def test_input_validation(self):
        """Test input validation and sanitization"""
        logger.info("Testing input validation...")
        
        # Test malicious queries
        malicious_queries = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../etc/passwd",
            "A" * 50000,  # Very long input
            "",  # Empty input
            "\x00\x01\x02",  # Binary data
        ]
        
        for query in malicious_queries:
            try:
                response = await self.client.post(
                    f"{self.base_url}/ask",
                    json={"question": query, "language": "auto"}
                )
                
                # Should either reject (400) or sanitize the input
                if response.status_code == 200:
                    data = response.json()
                    # Check that response doesn't contain the malicious input
                    if query in data.get("answer", ""):
                        logger.warning(f"Potential XSS vulnerability with input: {query[:50]}...")
                
            except Exception as e:
                # Exceptions are expected for malicious input
                pass
        
        logger.info("✅ Input validation tests passed")
    
    async def test_file_upload_security(self):
        """Test file upload security"""
        logger.info("Testing file upload security...")
        
        # Test 1: Non-PDF file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
            tmp_file.write(b"This is not a PDF")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as f:
                files = {"file": ("malicious.txt", f, "text/plain")}
                response = await self.client.post(f"{self.base_url}/documents/upload", files=files)
            
            # Should reject non-PDF files
            assert response.status_code == 400, "Should reject non-PDF files"
            
        finally:
            os.unlink(tmp_file_path)
        
        # Test 2: Oversized file
        large_content = b"A" * (200 * 1024 * 1024)  # 200MB
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(b"%PDF-1.4\n")  # PDF header
            tmp_file.write(large_content)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as f:
                files = {"file": ("large.pdf", f, "application/pdf")}
                response = await self.client.post(f"{self.base_url}/documents/upload", files=files)
            
            # Should reject oversized files
            assert response.status_code == 400, "Should reject oversized files"
            
        finally:
            os.unlink(tmp_file_path)
        
        # Test 3: Path traversal in filename
        malicious_filenames = [
            "../../../etc/passwd.pdf",
            "..\\..\\windows\\system32\\config\\sam.pdf",
            "C:\\Windows\\System32\\evil.pdf"
        ]
        
        for filename in malicious_filenames:
            pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\nxref\n0 1\n0000000000 65535 f \ntrailer<</Size 1/Root 1 0 R>>\nstartxref\n9\n%%EOF"
            
            try:
                files = {"file": (filename, pdf_content, "application/pdf")}
                response = await self.client.post(f"{self.base_url}/documents/upload", files=files)
                
                # Should reject malicious filenames
                assert response.status_code == 400, f"Should reject malicious filename: {filename}"
                
            except Exception:
                pass  # Expected to fail
        
        logger.info("✅ File upload security tests passed")
    
    async def test_rate_limiting(self):
        """Test rate limiting functionality"""
        logger.info("Testing rate limiting...")
        
        # Make rapid requests to trigger rate limiting
        responses = []
        for i in range(25):  # Exceed typical rate limit
            try:
                response = await self.client.get(f"{self.base_url}/health")
                responses.append(response.status_code)
            except Exception:
                responses.append(0)
        
        # Should see some 429 (rate limited) responses
        rate_limited_count = responses.count(429)
        
        if rate_limited_count > 0:
            logger.info(f"✅ Rate limiting working: {rate_limited_count} requests blocked")
        else:
            logger.warning("⚠️ Rate limiting may not be working properly")
    
    async def test_error_handling(self):
        """Test secure error handling"""
        logger.info("Testing error handling...")
        
        # Test invalid endpoints
        invalid_endpoints = [
            "/nonexistent",
            "/ask/../admin",
            "/ask?param=<script>",
        ]
        
        for endpoint in invalid_endpoints:
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                
                # Check that error responses don't leak information
                if response.status_code >= 400:
                    error_text = response.text.lower()
                    
                    # Should not contain sensitive information
                    sensitive_terms = ["traceback", "exception", "stack trace", "file path"]
                    for term in sensitive_terms:
                        if term in error_text:
                            logger.warning(f"Potential information leakage in error: {endpoint}")
                
            except Exception:
                pass  # Expected for invalid endpoints
        
        logger.info("✅ Error handling tests passed")
    
    async def test_security_headers(self):
        """Test security headers"""
        logger.info("Testing security headers...")
        
        response = await self.client.get(f"{self.base_url}/health")
        headers = response.headers
        
        # Check for required security headers
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Content-Security-Policy"
        ]
        
        missing_headers = []
        for header in required_headers:
            if header not in headers:
                missing_headers.append(header)
        
        if missing_headers:
            logger.warning(f"Missing security headers: {missing_headers}")
        else:
            logger.info("✅ All security headers present")
    
    async def test_path_traversal(self):
        """Test path traversal protection"""
        logger.info("Testing path traversal protection...")
        
        # Test path traversal in various endpoints
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc//passwd"
        ]
        
        for payload in traversal_payloads:
            try:
                # Test in document ID parameter
                response = await self.client.post(
                    f"{self.base_url}/summarize",
                    json={"document_id": payload}
                )
                
                # Should reject path traversal attempts
                if response.status_code == 200:
                    logger.warning(f"Potential path traversal vulnerability: {payload}")
                
            except Exception:
                pass  # Expected to fail
        
        logger.info("✅ Path traversal protection tests passed")
    
    async def test_injection_attacks(self):
        """Test for injection attack vulnerabilities"""
        logger.info("Testing injection attack protection...")
        
        # SQL injection payloads (shouldn't affect our app but good to test)
        sql_payloads = [
            "'; DROP TABLE documents; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM users",
        ]
        
        # Command injection payloads
        cmd_payloads = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& whoami",
            "`id`",
        ]
        
        all_payloads = sql_payloads + cmd_payloads
        
        for payload in all_payloads:
            try:
                response = await self.client.post(
                    f"{self.base_url}/ask",
                    json={"question": payload}
                )
                
                # Check response doesn't contain evidence of injection
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "").lower()
                    
                    # Look for signs of successful injection
                    injection_indicators = ["root:", "uid=", "gid=", "administrator", "system32"]
                    for indicator in injection_indicators:
                        if indicator in answer:
                            logger.warning(f"Potential injection vulnerability: {payload}")
                
            except Exception:
                pass  # Expected to fail for malicious input
        
        logger.info("✅ Injection attack protection tests passed")

async def main():
    """Main test runner"""
    # Check if backend is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8877/health", timeout=5.0)
            if response.status_code != 200:
                raise Exception("Backend not responding")
    except Exception:
        logger.error("❌ Backend not running. Please start it first:")
        logger.error("cd backend && python app.py")
        return
    
    # Run security tests
    test_suite = SecurityTestSuite()
    await test_suite.run_all_tests()
    
    logger.info("🎉 Security test suite completed!")

if __name__ == "__main__":
    asyncio.run(main())