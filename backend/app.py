"""
FastAPI backend for Indian legal research & judgment drafting
"""
import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

from ingest import DocumentIngestor
from retriever import LegalRetriever
from llm import LegalLLM
from sources.indiacode import IndiaCodeDownloader

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Indian Legal Research API",
    description="AI-powered legal research and judgment drafting for Indian law",
    version="1.0.0"
)

# CORS middleware for desktop app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components
ingestor: Optional[DocumentIngestor] = None
retriever: Optional[LegalRetriever] = None
llm: Optional[LegalLLM] = None

class QueryRequest(BaseModel):
    question: str = Field(..., description="Legal question to ask")
    language: str = Field(default="auto", description="Response language: en, hi, or auto")
    max_results: int = Field(default=5, description="Maximum number of sources to retrieve")

class SummarizeRequest(BaseModel):
    document_id: str = Field(..., description="Document ID to summarize")
    language: str = Field(default="auto", description="Response language: en, hi, or auto")

class JudgmentRequest(BaseModel):
    case_facts: str = Field(..., description="Facts of the case")
    legal_issues: List[str] = Field(..., description="Legal issues to address")
    language: str = Field(default="auto", description="Response language: en, hi, or auto")

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    language_detected: str

class SummaryResponse(BaseModel):
    facts: str
    issues: List[str]
    arguments: str
    holding: str
    relief: str
    language_detected: str

class JudgmentResponse(BaseModel):
    metadata: Dict[str, Any]
    framing: str
    points_for_determination: List[str]
    applicable_law: Dict[str, List[str]]
    arguments: Dict[str, str]
    court_analysis: List[Dict[str, Any]]
    findings: List[str]
    relief: Dict[str, Any]
    prediction: Dict[str, Any]
    limitations: List[str]

async def startup_event():
    """Initialize components on startup"""
    global ingestor, retriever, llm
    
    try:
        logger.info("Initializing backend components...")
        
        # Initialize document ingestor
        ingestor = DocumentIngestor()
        
        # Initialize retriever with InLegalBERT
        retriever = LegalRetriever()
        await retriever.initialize()
        
        # Initialize LLM
        llm = LegalLLM()
        await llm.initialize()
        
        # Connect ingestor to retriever
        ingestor.set_retriever(retriever)
        
        logger.info("Backend initialization complete")
        
    except Exception as e:
        logger.error(f"Failed to initialize backend: {e}")
        raise

# Register startup event
app.add_event_handler("startup", startup_event)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "components": {
            "ingestor": ingestor is not None,
            "retriever": retriever is not None,
            "llm": llm is not None
        }
    }

@app.post("/sources/add_statutes")
async def add_statutes():
    """Download and ingest Indian statutes from IndiaCode"""
    try:
        downloader = IndiaCodeDownloader()
        results = await downloader.download_and_ingest()
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Failed to add statutes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sources/status")
async def sources_status():
    """Get status of ingested sources"""
    try:
        if not retriever:
            raise HTTPException(status_code=503, detail="Retriever not initialized")
        
        status = await retriever.get_sources_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get sources status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sources/sync")
async def sync_sources():
    """Sync sources from SCI/HC (placeholder for future implementation)"""
    return {
        "status": "not_implemented",
        "message": "SCI/HC scraping will be implemented in future version"
    }

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a PDF document"""
    try:
        if not ingestor:
            raise HTTPException(status_code=503, detail="Ingestor not initialized")
        
        # Save uploaded file
        file_path = Path("data/uploads") / file.filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Ingest document
        doc_id = await ingestor.ingest_document(str(file_path))
        
        return {
            "status": "success",
            "document_id": doc_id,
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """Answer legal questions with grounded citations"""
    try:
        if not retriever or not llm:
            raise HTTPException(status_code=503, detail="Components not initialized")
        
        # Retrieve relevant documents
        results = await retriever.search(
            query=request.question,
            max_results=request.max_results
        )
        
        # Generate answer with citations
        answer = await llm.generate_answer(
            question=request.question,
            sources=results,
            language=request.language
        )
        
        return QueryResponse(
            answer=answer["text"],
            sources=results,
            language_detected=answer.get("language_detected", "auto")
        )
        
    except Exception as e:
        logger.error(f"Failed to answer question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize", response_model=SummaryResponse)
async def summarize_document(request: SummarizeRequest):
    """Generate structured summary of a legal document"""
    try:
        if not retriever or not llm:
            raise HTTPException(status_code=503, detail="Components not initialized")
        
        # Get document content
        doc_content = await retriever.get_document_content(request.document_id)
        
        # Generate structured summary
        summary = await llm.generate_summary(
            content=doc_content,
            language=request.language
        )
        
        return SummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"Failed to summarize document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/judgment", response_model=JudgmentResponse)
async def generate_judgment(request: JudgmentRequest):
    """Generate structured legal judgment"""
    try:
        if not retriever or not llm:
            raise HTTPException(status_code=503, detail="Components not initialized")
        
        # Retrieve relevant legal precedents and statutes
        relevant_docs = []
        for issue in request.legal_issues:
            results = await retriever.search(query=issue, max_results=3)
            relevant_docs.extend(results)
        
        # Generate judgment
        judgment = await llm.generate_judgment(
            case_facts=request.case_facts,
            legal_issues=request.legal_issues,
            relevant_sources=relevant_docs,
            language=request.language
        )
        
        return JudgmentResponse(**judgment)
        
    except Exception as e:
        logger.error(f"Failed to generate judgment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 8877))
    uvicorn.run(app, host="0.0.0.0", port=port)