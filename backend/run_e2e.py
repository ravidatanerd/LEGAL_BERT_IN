#!/usr/bin/env python3
"""
End-to-end smoke tests for InLegalDesk backend
"""
import asyncio
import logging
import tempfile
import json
import os
from pathlib import Path
from typing import Dict, Any
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class E2ETestRunner:
    """End-to-end test runner"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8877"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(120.0))
    
    async def run_all_tests(self):
        """Run all end-to-end tests"""
        try:
            logger.info("Starting E2E tests...")
            
            # Test 1: Health check
            await self.test_health_check()
            
            # Test 2: Add statutes
            await self.test_add_statutes()
            
            # Test 3: Upload local PDF (if available)
            await self.test_upload_document()
            
            # Test 4: Ask question about Evidence Act
            await self.test_ask_question()
            
            # Test 5: Generate judgment
            await self.test_generate_judgment()
            
            logger.info("All E2E tests completed successfully!")
            
        except Exception as e:
            logger.error(f"E2E tests failed: {e}")
            raise
        finally:
            await self.client.aclose()
    
    async def test_health_check(self):
        """Test health check endpoint"""
        logger.info("Testing health check...")
        
        response = await self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        
        data = response.json()
        assert data["status"] == "healthy"
        
        logger.info("✓ Health check passed")
    
    async def test_add_statutes(self):
        """Test statute ingestion"""
        logger.info("Testing statute ingestion...")
        
        response = await self.client.post(f"{self.base_url}/sources/add_statutes")
        response.raise_for_status()
        
        data = response.json()
        assert data["status"] == "success"
        
        logger.info("✓ Statute ingestion passed")
    
    async def test_upload_document(self):
        """Test document upload (creates a dummy PDF if none available)"""
        logger.info("Testing document upload...")
        
        # Create a simple test PDF
        test_pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj 4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Times-Roman>>endobj 5 0 obj<</Length 44>>stream\nBT /F1 12 Tf 100 700 Td (Test Legal Document) Tj ET\nendstream endobj xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000265 00000 n \n0000000336 00000 n \ntrailer<</Size 6/Root 1 0 R>>\nstartxref\n428\n%%EOF"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(test_pdf_content)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as f:
                files = {"file": ("test_document.pdf", f, "application/pdf")}
                response = await self.client.post(f"{self.base_url}/documents/upload", files=files)
            
            response.raise_for_status()
            data = response.json()
            
            assert data["status"] == "success"
            assert "document_id" in data
            
            logger.info("✓ Document upload passed")
            
        finally:
            # Clean up
            os.unlink(tmp_file_path)
    
    async def test_ask_question(self):
        """Test question answering about Evidence Act"""
        logger.info("Testing question answering...")
        
        payload = {
            "question": "What are the provisions regarding confessions under the Indian Evidence Act?",
            "language": "auto",
            "max_results": 3
        }
        
        response = await self.client.post(f"{self.base_url}/ask", json=payload)
        response.raise_for_status()
        
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        
        logger.info("✓ Question answering passed")
        logger.info(f"Answer preview: {data['answer'][:100]}...")
    
    async def test_generate_judgment(self):
        """Test judgment generation"""
        logger.info("Testing judgment generation...")
        
        payload = {
            "case_facts": "The accused was found with stolen property. He confessed to the crime during police interrogation.",
            "legal_issues": [
                "Admissibility of confession made to police",
                "Burden of proof regarding stolen property"
            ],
            "language": "auto"
        }
        
        response = await self.client.post(f"{self.base_url}/judgment", json=payload)
        response.raise_for_status()
        
        data = response.json()
        assert "framing" in data
        assert "applicable_law" in data
        
        logger.info("✓ Judgment generation passed")
        
        # Save judgment to temp file (Windows style)
        temp_dir = os.environ.get('TEMP', '/tmp')
        judgment_path = Path(temp_dir) / "judgment.md"
        
        # Convert judgment to markdown
        markdown_content = self._format_judgment_markdown(data)
        
        with open(judgment_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"✓ Judgment saved to {judgment_path}")
    
    def _format_judgment_markdown(self, judgment: Dict[str, Any]) -> str:
        """Format judgment as markdown"""
        md_parts = [
            "# Legal Judgment - E2E Test\n",
            f"Generated on: {Path().cwd()}\n",
            f"## Case Framing\n{judgment.get('framing', 'N/A')}\n",
            "## Points for Determination\n"
        ]
        
        for i, point in enumerate(judgment.get('points_for_determination', []), 1):
            md_parts.append(f"{i}. {point}")
        
        md_parts.extend([
            "\n## Applicable Law",
            f"- **Constitutional**: {', '.join(judgment.get('applicable_law', {}).get('constitutional', []))}",
            f"- **Statutes**: {', '.join(judgment.get('applicable_law', {}).get('statutes', []))}",
            f"- **Precedents**: {', '.join(judgment.get('applicable_law', {}).get('precedents', []))}",
            "\n## Court Analysis\n"
        ])
        
        for analysis in judgment.get('court_analysis', []):
            md_parts.append(f"### {analysis.get('issue', 'Issue')}")
            md_parts.append(f"{analysis.get('analysis', 'N/A')}\n")
        
        md_parts.extend([
            "## Final Order",
            judgment.get('relief', {}).get('final_order', 'N/A'),
            "\n## Prediction",
            f"**Likely Outcome**: {judgment.get('prediction', {}).get('likely_outcome', 'N/A')}"
        ])
        
        return "\n".join(md_parts)

async def main():
    """Main test runner"""
    runner = E2ETestRunner()
    await runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())