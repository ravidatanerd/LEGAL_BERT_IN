#!/usr/bin/env python3
"""
E2E Smoke Tests for InLegal Desktop Application
This script tests the complete functionality of the application
"""

import os
import sys
import json
import time
import tempfile
import requests
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InLegalE2ETester:
    """End-to-end tester for InLegal Desktop application"""
    
    def __init__(self, backend_url: str = "http://127.0.0.1:8877"):
        self.backend_url = backend_url
        self.temp_dir = Path(tempfile.mkdtemp(prefix="inlegal_test_"))
        self.test_pdf_path = self.temp_dir / "sample_case.pdf"
        self.judgment_output = self.temp_dir / "judgment.md"
        self.tests_passed = 0
        self.tests_failed = 0
        
        logger.info(f"E2E Tester initialized")
        logger.info(f"Backend URL: {self.backend_url}")
        logger.info(f"Temp directory: {self.temp_dir}")
    
    def print_status(self, status: str, message: str):
        """Print colored status message"""
        if status == "PASS":
            logger.info(f"✓ PASS: {message}")
        elif status == "FAIL":
            logger.error(f"✗ FAIL: {message}")
        else:
            logger.info(f"ℹ INFO: {message}")
    
    def check_backend(self) -> bool:
        """Check if backend is running and healthy"""
        self.print_status("INFO", "Checking backend health...")
        
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.print_status("PASS", "Backend is running and healthy")
                    return True
                else:
                    self.print_status("FAIL", f"Backend unhealthy: {data}")
                    return False
            else:
                self.print_status("FAIL", f"Backend returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_status("FAIL", f"Backend connection failed: {e}")
            return False
    
    def test_sources_status(self) -> bool:
        """Test sources status endpoint"""
        self.print_status("INFO", "Testing sources status endpoint...")
        
        try:
            response = requests.get(f"{self.backend_url}/sources/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.print_status("PASS", "Sources status endpoint working")
                logger.info(f"Sources status: {data}")
                return True
            else:
                self.print_status("FAIL", f"Sources status failed with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_status("FAIL", f"Sources status request failed: {e}")
            return False
    
    def test_statute_ingestion(self) -> bool:
        """Test statute ingestion"""
        self.print_status("INFO", "Testing statute ingestion...")
        
        try:
            response = requests.post(f"{self.backend_url}/sources/add_statutes", timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.print_status("PASS", "Statute ingestion started successfully")
                logger.info(f"Ingestion response: {data}")
                
                # Wait for ingestion to complete
                self.print_status("INFO", "Waiting for statute ingestion to complete...")
                time.sleep(30)
                
                # Check if documents were ingested
                documents_response = requests.get(f"{self.backend_url}/documents", timeout=10)
                if documents_response.status_code == 200:
                    documents_data = documents_response.json()
                    if documents_data.get("documents"):
                        self.print_status("PASS", "Documents were ingested successfully")
                        return True
                    else:
                        self.print_status("FAIL", "No documents found after ingestion")
                        return False
                else:
                    self.print_status("FAIL", "Failed to check documents after ingestion")
                    return False
            else:
                self.print_status("FAIL", f"Statute ingestion failed with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_status("FAIL", f"Statute ingestion request failed: {e}")
            return False
    
    def create_test_pdf(self) -> bool:
        """Create a test PDF document"""
        self.print_status("INFO", "Creating test PDF document...")
        
        try:
            # Try to create PDF using reportlab
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            c = canvas.Canvas(str(self.test_pdf_path), pagesize=letter)
            c.drawString(100, 750, 'Test Legal Document')
            c.drawString(100, 700, 'This is a test document for InLegal E2E testing.')
            c.drawString(100, 650, 'Section 1: Test Case Facts')
            c.drawString(100, 600, 'The plaintiff filed a suit against the defendant.')
            c.drawString(100, 550, 'The defendant failed to perform contractual obligations.')
            c.drawString(100, 500, 'Section 2: Legal Issues')
            c.drawString(100, 450, '1. Whether the contract is valid?')
            c.drawString(100, 400, '2. Whether the defendant is liable for breach?')
            c.drawString(100, 350, '3. What damages are recoverable?')
            c.drawString(100, 300, 'Section 3: Legal Provisions')
            c.drawString(100, 250, 'Indian Contract Act, 1872 - Section 73')
            c.drawString(100, 200, 'Indian Penal Code, 1860 - Section 420')
            c.save()
            
            self.print_status("PASS", f"Test PDF created: {self.test_pdf_path}")
            return True
            
        except ImportError:
            # Fallback: create a simple text file
            self.print_status("INFO", "reportlab not available, creating text file instead")
            with open(self.test_pdf_path.with_suffix('.txt'), 'w') as f:
                f.write("Test Legal Document\n")
                f.write("This is a test document for InLegal E2E testing.\n")
                f.write("Section 1: Test Case Facts\n")
                f.write("The plaintiff filed a suit against the defendant.\n")
                f.write("Section 2: Legal Issues\n")
                f.write("1. Whether the contract is valid?\n")
                f.write("2. Whether the defendant is liable for breach?\n")
            
            self.test_pdf_path = self.test_pdf_path.with_suffix('.txt')
            self.print_status("PASS", f"Test text file created: {self.test_pdf_path}")
            return True
        except Exception as e:
            self.print_status("FAIL", f"Failed to create test document: {e}")
            return False
    
    def test_document_upload(self) -> bool:
        """Test document upload"""
        self.print_status("INFO", "Testing document upload...")
        
        if not self.create_test_pdf():
            return False
        
        try:
            with open(self.test_pdf_path, 'rb') as f:
                files = {'file': (self.test_pdf_path.name, f, 'application/pdf' if self.test_pdf_path.suffix == '.pdf' else 'text/plain')}
                response = requests.post(f"{self.backend_url}/upload", files=files, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if 'document_id' in data:
                    self.print_status("PASS", "Document upload successful")
                    logger.info(f"Upload response: {data}")
                    self.uploaded_document_id = data['document_id']
                    return True
                else:
                    self.print_status("FAIL", "No document_id in upload response")
                    return False
            else:
                self.print_status("FAIL", f"Document upload failed with status {response.status_code}")
                logger.error(f"Upload error: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_status("FAIL", f"Document upload request failed: {e}")
            return False
    
    def test_question_answering(self) -> bool:
        """Test question answering"""
        self.print_status("INFO", "Testing question answering...")
        
        question_data = {
            "question": "What are the provisions regarding confessions in the Evidence Act?",
            "language": "auto",
            "max_sources": 5
        }
        
        try:
            response = requests.post(
                f"{self.backend_url}/ask",
                json=question_data,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'answer' in data:
                    self.print_status("PASS", "Question answering working")
                    logger.info(f"Answer preview: {data['answer'][:200]}...")
                    return True
                else:
                    self.print_status("FAIL", "No answer in response")
                    return False
            else:
                self.print_status("FAIL", f"Question answering failed with status {response.status_code}")
                logger.error(f"QA error: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_status("FAIL", f"Question answering request failed: {e}")
            return False
    
    def test_judgment_generation(self) -> bool:
        """Test judgment generation"""
        self.print_status("INFO", "Testing judgment generation...")
        
        judgment_data = {
            "case_facts": "The plaintiff entered into a contract with the defendant for the sale of goods. The defendant failed to deliver the goods as per the contract terms, causing financial loss to the plaintiff.",
            "issues": [
                "Whether the contract is valid and enforceable?",
                "Whether the defendant is liable for breach of contract?",
                "What are the damages recoverable by the plaintiff?"
            ],
            "language": "auto"
        }
        
        try:
            response = requests.post(
                f"{self.backend_url}/judgment",
                json=judgment_data,
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'judgment' in data:
                    self.print_status("PASS", "Judgment generation working")
                    
                    # Save judgment to file
                    self.save_judgment_to_file(data['judgment'])
                    return True
                else:
                    self.print_status("FAIL", "No judgment in response")
                    return False
            else:
                self.print_status("FAIL", f"Judgment generation failed with status {response.status_code}")
                logger.error(f"Judgment error: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_status("FAIL", f"Judgment generation request failed: {e}")
            return False
    
    def save_judgment_to_file(self, judgment: Dict[str, Any]):
        """Save judgment to markdown file"""
        try:
            with open(self.judgment_output, 'w', encoding='utf-8') as f:
                f.write('# Generated Judgment\n\n')
                
                # Metadata
                metadata = judgment.get('metadata', {})
                if metadata:
                    f.write('## Case Information\n\n')
                    f.write(f"**Case:** {metadata.get('case_title', 'N/A')}\n")
                    f.write(f"**Court:** {metadata.get('court', 'N/A')}\n")
                    f.write(f"**Date:** {metadata.get('date', 'N/A')}\n")
                    f.write(f"**Case Number:** {metadata.get('case_number', 'N/A')}\n\n")
                
                # Framing
                framing = judgment.get('framing', '')
                if framing:
                    f.write('## Case Facts\n\n')
                    f.write(f"{framing}\n\n")
                
                # Issues
                issues = judgment.get('points_for_determination', [])
                if issues:
                    f.write('## Points for Determination\n\n')
                    for issue in issues:
                        f.write(f"- {issue}\n")
                    f.write('\n')
                
                # Arguments
                arguments = judgment.get('arguments', {})
                if arguments:
                    f.write('## Arguments\n\n')
                    if arguments.get('petitioner'):
                        f.write(f"**Petitioner:** {arguments['petitioner']}\n\n")
                    if arguments.get('respondent'):
                        f.write(f"**Respondent:** {arguments['respondent']}\n\n")
                
                # Analysis
                analysis = judgment.get('court_analysis', [])
                if analysis:
                    f.write('## Court Analysis\n\n')
                    for item in analysis:
                        f.write(f"### {item.get('issue', 'Issue')}\n\n")
                        f.write(f"{item.get('analysis', '')}\n\n")
                
                # Findings
                findings = judgment.get('findings', [])
                if findings:
                    f.write('## Findings\n\n')
                    for finding in findings:
                        f.write(f"- {finding}\n")
                    f.write('\n')
                
                # Relief
                relief = judgment.get('relief', {})
                if relief:
                    f.write('## Relief\n\n')
                    if relief.get('final_order'):
                        f.write(f"**Final Order:** {relief['final_order']}\n\n")
                    if relief.get('directions'):
                        f.write('**Directions:**\n\n')
                        for direction in relief['directions']:
                            f.write(f"- {direction}\n")
                        f.write('\n')
                    if relief.get('costs'):
                        f.write(f"**Costs:** {relief['costs']}\n\n")
            
            self.print_status("PASS", f"Judgment saved to {self.judgment_output}")
            
        except Exception as e:
            self.print_status("FAIL", f"Failed to save judgment: {e}")
    
    def test_document_listing(self) -> bool:
        """Test document listing"""
        self.print_status("INFO", "Testing document listing...")
        
        try:
            response = requests.get(f"{self.backend_url}/documents", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'documents' in data:
                    self.print_status("PASS", "Document listing working")
                    logger.info(f"Found {len(data['documents'])} documents")
                    return True
                else:
                    self.print_status("FAIL", "No documents key in response")
                    return False
            else:
                self.print_status("FAIL", f"Document listing failed with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_status("FAIL", f"Document listing request failed: {e}")
            return False
    
    def test_summarization(self) -> bool:
        """Test document summarization"""
        self.print_status("INFO", "Testing document summarization...")
        
        try:
            # Get document IDs first
            documents_response = requests.get(f"{self.backend_url}/documents", timeout=10)
            if documents_response.status_code == 200:
                documents_data = documents_response.json()
                documents = documents_data.get('documents', [])
                
                if documents:
                    # Take first 2 documents
                    document_ids = [doc['document_id'] for doc in documents[:2]]
                    
                    summary_data = {
                        "document_ids": document_ids,
                        "language": "auto"
                    }
                    
                    response = requests.post(
                        f"{self.backend_url}/summarize",
                        json=summary_data,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'summary' in data:
                            self.print_status("PASS", "Document summarization working")
                            logger.info(f"Summary preview: {data['summary'][:200]}...")
                            return True
                        else:
                            self.print_status("FAIL", "No summary in response")
                            return False
                    else:
                        self.print_status("FAIL", f"Summarization failed with status {response.status_code}")
                        return False
                else:
                    self.print_status("INFO", "No documents available for summarization test")
                    return True
            else:
                self.print_status("FAIL", "Failed to get documents for summarization")
                return False
        except requests.exceptions.RequestException as e:
            self.print_status("FAIL", f"Summarization request failed: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all E2E tests"""
        logger.info("Starting E2E smoke tests...")
        logger.info("=" * 50)
        
        # Test counter
        self.tests_passed = 0
        self.tests_failed = 0
        
        # Run tests
        tests = [
            ("Backend Health Check", self.check_backend),
            ("Sources Status", self.test_sources_status),
            ("Statute Ingestion", self.test_statute_ingestion),
            ("Document Upload", self.test_document_upload),
            ("Question Answering", self.test_question_answering),
            ("Judgment Generation", self.test_judgment_generation),
            ("Document Listing", self.test_document_listing),
            ("Document Summarization", self.test_summarization),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"Running test: {test_name}")
            try:
                if test_func():
                    self.tests_passed += 1
                else:
                    self.tests_failed += 1
            except Exception as e:
                logger.error(f"Test {test_name} failed with exception: {e}")
                self.tests_failed += 1
            logger.info("-" * 30)
        
        # Summary
        logger.info("=" * 50)
        logger.info("E2E Test Summary")
        logger.info("=" * 50)
        logger.info(f"Tests Passed: {self.tests_passed}")
        logger.info(f"Tests Failed: {self.tests_failed}")
        logger.info(f"Total Tests: {self.tests_passed + self.tests_failed}")
        
        if self.tests_failed == 0:
            self.print_status("PASS", "All E2E tests passed!")
            logger.info("")
            logger.info("Generated files:")
            logger.info(f"- Judgment: {self.judgment_output}")
            logger.info(f"- Test Document: {self.test_pdf_path}")
            return True
        else:
            self.print_status("FAIL", f"{self.tests_failed} test(s) failed")
            return False
    
    def cleanup(self):
        """Cleanup temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary directory: {e}")

def check_dependencies():
    """Check if required dependencies are available"""
    logger.info("Checking dependencies...")
    
    # Check requests
    try:
        import requests
        logger.info("✓ requests available")
    except ImportError:
        logger.error("✗ requests not available. Install with: pip install requests")
        return False
    
    # Check reportlab (optional)
    try:
        import reportlab
        logger.info("✓ reportlab available")
    except ImportError:
        logger.warning("⚠ reportlab not available. Will create text files instead of PDFs.")
    
    logger.info("Dependencies check completed")
    return True

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="InLegal Desktop E2E Smoke Tests")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8877", 
                       help="Backend URL (default: http://127.0.0.1:8877)")
    parser.add_argument("--keep-files", action="store_true",
                       help="Keep generated test files")
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create tester
    tester = InLegalE2ETester(args.backend_url)
    
    try:
        # Run tests
        success = tester.run_all_tests()
        
        if not args.keep_files:
            tester.cleanup()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        if not args.keep_files:
            tester.cleanup()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if not args.keep_files:
            tester.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()