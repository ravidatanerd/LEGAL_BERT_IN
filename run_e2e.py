"""
End-to-End Testing Script for InLegalDesk
Tests the complete system functionality
"""

import os
import sys
import asyncio
import json
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import requests
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api_client import LegalAPIClient

class E2ETester:
    """End-to-end testing for InLegalDesk system"""
    
    def __init__(self, backend_url: str = "http://127.0.0.1:8877"):
        self.backend_url = backend_url
        self.api_client = LegalAPIClient(backend_url)
        self.test_results = []
        self.temp_dir = None
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all E2E tests"""
        logger.info("Starting E2E tests for InLegalDesk...")
        
        # Create temp directory for test files
        self.temp_dir = tempfile.mkdtemp(prefix="inlegaldesk_e2e_")
        logger.info(f"Using temp directory: {self.temp_dir}")
        
        try:
            # Test 1: Backend Health Check
            await self._test_backend_health()
            
            # Test 2: Add Legal Statutes
            await self._test_add_statutes()
            
            # Test 3: Document Ingestion
            await self._test_document_ingestion()
            
            # Test 4: Legal Q&A
            await self._test_legal_qa()
            
            # Test 5: Document Summarization
            await self._test_document_summarization()
            
            # Test 6: Judgment Generation
            await self._test_judgment_generation()
            
            # Test 7: Sources Status
            await self._test_sources_status()
            
            # Test 8: Export Functionality
            await self._test_export_functionality()
            
            # Generate test report
            report = self._generate_test_report()
            
            logger.info("E2E tests completed successfully!")
            return report
            
        except Exception as e:
            logger.error(f"E2E tests failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "results": self.test_results
            }
        finally:
            # Cleanup temp directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
    
    async def _test_backend_health(self):
        """Test backend health endpoint"""
        logger.info("Testing backend health...")
        
        try:
            async with self.api_client:
                health = await self.api_client.health_check()
                
                if health.get("status") == "healthy":
                    self._record_test_result("backend_health", True, "Backend is healthy", health)
                else:
                    self._record_test_result("backend_health", False, "Backend is not healthy", health)
                    
        except Exception as e:
            self._record_test_result("backend_health", False, f"Health check failed: {e}")
    
    async def _test_add_statutes(self):
        """Test adding legal statutes"""
        logger.info("Testing legal statutes ingestion...")
        
        try:
            async with self.api_client:
                result = await self.api_client.add_statutes()
                
                if "error" not in result:
                    self._record_test_result("add_statutes", True, "Statutes ingestion initiated", result)
                else:
                    self._record_test_result("add_statutes", False, f"Statutes ingestion failed: {result['error']}")
                    
        except Exception as e:
            self._record_test_result("add_statutes", False, f"Statutes test failed: {e}")
    
    async def _test_document_ingestion(self):
        """Test document ingestion with sample PDF"""
        logger.info("Testing document ingestion...")
        
        try:
            # Create a sample PDF for testing
            sample_pdf_path = await self._create_sample_pdf()
            
            async with self.api_client:
                result = await self.api_client.ingest_document(sample_pdf_path)
                
                if "error" not in result:
                    self._record_test_result("document_ingestion", True, "Document ingestion successful", result)
                else:
                    self._record_test_result("document_ingestion", False, f"Document ingestion failed: {result['error']}")
                    
        except Exception as e:
            self._record_test_result("document_ingestion", False, f"Document ingestion test failed: {e}")
    
    async def _test_legal_qa(self):
        """Test legal Q&A functionality"""
        logger.info("Testing legal Q&A...")
        
        test_questions = [
            "What is the definition of theft under Indian Penal Code?",
            "What are the requirements for a valid confession under Evidence Act?",
            "What is the procedure for filing a criminal complaint?"
        ]
        
        for i, question in enumerate(test_questions):
            try:
                async with self.api_client:
                    result = await self.api_client.ask_question(question, language="en")
                    
                    if "error" not in result and result.get("answer"):
                        self._record_test_result(f"legal_qa_{i+1}", True, f"Q&A successful for question {i+1}", {
                            "question": question,
                            "answer_length": len(result.get("answer", "")),
                            "citations_count": len(result.get("citations", []))
                        })
                    else:
                        self._record_test_result(f"legal_qa_{i+1}", False, f"Q&A failed for question {i+1}: {result.get('error', 'No answer')}")
                        
            except Exception as e:
                self._record_test_result(f"legal_qa_{i+1}", False, f"Q&A test {i+1} failed: {e}")
    
    async def _test_document_summarization(self):
        """Test document summarization"""
        logger.info("Testing document summarization...")
        
        try:
            # This would require a document ID from previous ingestion
            # For now, we'll test with a mock document ID
            mock_document_id = "test_document_123"
            
            async with self.api_client:
                result = await self.api_client.generate_summary(mock_document_id, language="en")
                
                if "error" not in result:
                    self._record_test_result("document_summarization", True, "Document summarization successful", result)
                else:
                    self._record_test_result("document_summarization", False, f"Document summarization failed: {result['error']}")
                    
        except Exception as e:
            self._record_test_result("document_summarization", False, f"Document summarization test failed: {e}")
    
    async def _test_judgment_generation(self):
        """Test judgment generation"""
        logger.info("Testing judgment generation...")
        
        test_cases = [
            {
                "facts": "The petitioner was arrested for theft of a mobile phone worth Rs. 15,000. The police found the phone in his possession during a routine check.",
                "issues": [
                    "Whether the arrest was legal under Section 41 of CrPC?",
                    "Whether the evidence is sufficient to prove theft under Section 378 of IPC?"
                ]
            },
            {
                "facts": "A contract was entered into between A and B for the sale of goods. A failed to deliver the goods on the agreed date, causing B to suffer losses.",
                "issues": [
                    "Whether A is liable for breach of contract?",
                    "What damages can B claim under the Indian Contract Act?"
                ]
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            try:
                async with self.api_client:
                    result = await self.api_client.generate_judgment(
                        facts=test_case["facts"],
                        issues=test_case["issues"],
                        language="en",
                        court_type="high_court"
                    )
                    
                    if "error" not in result and result.get("judgment"):
                        self._record_test_result(f"judgment_generation_{i+1}", True, f"Judgment generation successful for case {i+1}", {
                            "judgment_length": len(str(result.get("judgment", ""))),
                            "sources_used": result.get("sources_used", 0)
                        })
                    else:
                        self._record_test_result(f"judgment_generation_{i+1}", False, f"Judgment generation failed for case {i+1}: {result.get('error', 'No judgment')}")
                        
            except Exception as e:
                self._record_test_result(f"judgment_generation_{i+1}", False, f"Judgment generation test {i+1} failed: {e}")
    
    async def _test_sources_status(self):
        """Test sources status endpoint"""
        logger.info("Testing sources status...")
        
        try:
            async with self.api_client:
                result = await self.api_client.get_sources_status()
                
                if "error" not in result:
                    self._record_test_result("sources_status", True, "Sources status retrieved successfully", result)
                else:
                    self._record_test_result("sources_status", False, f"Sources status failed: {result['error']}")
                    
        except Exception as e:
            self._record_test_result("sources_status", False, f"Sources status test failed: {e}")
    
    async def _test_export_functionality(self):
        """Test export functionality"""
        logger.info("Testing export functionality...")
        
        try:
            # Test chat export
            mock_chat_id = "test_chat_123"
            
            async with self.api_client:
                result = await self.api_client.export_chat(mock_chat_id, format="markdown")
                
                if "error" not in result:
                    self._record_test_result("export_functionality", True, "Export functionality working", result)
                else:
                    self._record_test_result("export_functionality", False, f"Export functionality failed: {result['error']}")
                    
        except Exception as e:
            self._record_test_result("export_functionality", False, f"Export functionality test failed: {e}")
    
    async def _create_sample_pdf(self) -> str:
        """Create a sample PDF for testing"""
        try:
            # Create a simple text file that could be converted to PDF
            # In a real implementation, you would create an actual PDF
            sample_text = """
            IN THE HIGH COURT OF DELHI AT NEW DELHI
            
            CRIMINAL APPEAL NO. 1234 OF 2024
            
            Appellant: State of Delhi
            Respondent: John Doe
            
            JUDGMENT
            
            This is a sample legal document for testing purposes.
            It contains various legal terms and concepts.
            
            The facts of the case are as follows:
            1. The respondent was charged with theft under Section 378 of IPC
            2. The prosecution presented evidence of the stolen goods
            3. The trial court convicted the respondent
            
            Issues for determination:
            1. Whether the conviction is sustainable in law?
            2. Whether the sentence is appropriate?
            
            After considering the arguments and evidence, this court finds...
            """
            
            sample_file_path = os.path.join(self.temp_dir, "sample_legal_document.txt")
            with open(sample_file_path, 'w', encoding='utf-8') as f:
                f.write(sample_text)
            
            # For testing purposes, we'll use the text file
            # In a real implementation, you would convert this to PDF
            return sample_file_path
            
        except Exception as e:
            logger.error(f"Failed to create sample PDF: {e}")
            raise
    
    def _record_test_result(self, test_name: str, success: bool, message: str, data: Any = None):
        """Record test result"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": time.time(),
            "data": data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {message}")
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "status": "PASS" if failed_tests == 0 else "FAIL"
            },
            "test_results": self.test_results,
            "timestamp": time.time(),
            "environment": {
                "backend_url": self.backend_url,
                "temp_dir": self.temp_dir
            }
        }
        
        # Save report to file
        report_file = os.path.join(self.temp_dir, "e2e_test_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Test report saved to: {report_file}")
        
        return report

async def main():
    """Main E2E test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run E2E tests for InLegalDesk")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8877", help="Backend URL")
    parser.add_argument("--output", help="Output file for test report")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")
    
    # Run tests
    tester = E2ETester(args.backend_url)
    report = await tester.run_all_tests()
    
    # Print summary
    summary = report["summary"]
    print(f"\n{'='*50}")
    print(f"E2E Test Summary")
    print(f"{'='*50}")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Status: {summary['status']}")
    print(f"{'='*50}")
    
    # Save report if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Test report saved to: {args.output}")
    
    # Exit with appropriate code
    sys.exit(0 if summary['status'] == 'PASS' else 1)

if __name__ == "__main__":
    asyncio.run(main())