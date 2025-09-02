"""
FastAPI backend for Indian legal research & judgment drafting
"""

import os
import asyncio
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import logging
from loguru import logger

from ingest import DocumentIngester
from retriever import LegalRetriever
from llm import LegalLLM
from sources.indiacode import IndiaCodeDownloader
from sources.sci import SCIScraper
from sources.hc import HCScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger.add("logs/legal_research.log", rotation="10 MB", retention="7 days")

# Global instances
ingester: Optional[DocumentIngester] = None
retriever: Optional[LegalRetriever] = None
llm: Optional[LegalLLM] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    global ingester, retriever, llm
    
    logger.info("Starting Legal Research Backend...")
    
    # Initialize components
    try:
        ingester = DocumentIngester()
        retriever = LegalRetriever()
        llm = LegalLLM()
        
        logger.info("Backend initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize backend: {e}")
        raise
    
    yield
    
    logger.info("Shutting down Legal Research Backend...")

app = FastAPI(
    title="Indian Legal Research API",
    description="AI-powered legal research and judgment drafting system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QueryRequest(BaseModel):
    question: str
    language: str = "auto"
    max_results: int = 10

class JudgmentRequest(BaseModel):
    case_facts: str
    legal_issues: List[str]
    language: str = "auto"
    court_type: str = "high_court"

class SummaryRequest(BaseModel):
    document_id: str
    language: str = "auto"

class SourceRequest(BaseModel):
    source_type: str  # "statutes", "sci", "hc"
    parameters: Dict[str, Any] = {}

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "ingester": ingester is not None,
            "retriever": retriever is not None,
            "llm": llm is not None
        }
    }

# Document ingestion
@app.post("/ingest")
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None)
):
    """Ingest a legal document (PDF)"""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save uploaded file temporarily
        temp_path = f"temp/{file.filename}"
        os.makedirs("temp", exist_ok=True)
        
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process document in background
        background_tasks.add_task(ingester.ingest_document, temp_path, metadata)
        
        return {
            "message": "Document queued for processing",
            "filename": file.filename,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Legal Q&A
@app.post("/ask")
async def ask_question(request: QueryRequest):
    """Ask a legal question with grounded citations"""
    try:
        # Retrieve relevant documents
        results = await retriever.search(
            query=request.question,
            max_results=request.max_results,
            language=request.language
        )
        
        # Generate answer with citations
        answer = await llm.generate_answer(
            question=request.question,
            context=results,
            language=request.language
        )
        
        return {
            "question": request.question,
            "answer": answer["text"],
            "citations": answer["citations"],
            "sources": results,
            "language": request.language
        }
        
    except Exception as e:
        logger.error(f"Question answering failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Document summarization
@app.post("/summarize")
async def summarize_document(request: SummaryRequest):
    """Generate structured summary of a legal document"""
    try:
        # Get document content
        document = await retriever.get_document(request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Generate summary
        summary = await llm.generate_summary(
            document=document,
            language=request.language
        )
        
        return {
            "document_id": request.document_id,
            "summary": summary,
            "language": request.language
        }
        
    except Exception as e:
        logger.error(f"Document summarization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Judgment generation
@app.post("/judgment")
async def generate_judgment(request: JudgmentRequest):
    """Generate a structured legal judgment"""
    try:
        # Retrieve relevant legal precedents and statutes
        context = await retriever.search_judgment_context(
            facts=request.case_facts,
            issues=request.legal_issues,
            court_type=request.court_type
        )
        
        # Generate judgment
        judgment = await llm.generate_judgment(
            facts=request.case_facts,
            issues=request.legal_issues,
            context=context,
            language=request.language,
            court_type=request.court_type
        )
        
        return {
            "judgment": judgment,
            "language": request.language,
            "court_type": request.court_type,
            "sources_used": len(context)
        }
        
    except Exception as e:
        logger.error(f"Judgment generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Source management
@app.post("/sources/add_statutes")
async def add_statutes(background_tasks: BackgroundTasks):
    """Download and ingest Indian legal statutes"""
    try:
        downloader = IndiaCodeDownloader()
        
        # Download statutes in background
        background_tasks.add_task(downloader.download_all_statutes)
        
        return {
            "message": "Statutes download initiated",
            "status": "processing",
            "statutes": ["IPC_1860", "CrPC_1973", "Evidence_1872"]
        }
        
    except Exception as e:
        logger.error(f"Statutes download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sources/sync")
async def sync_sources(request: SourceRequest):
    """Sync legal sources (SCI/HC scraping)"""
    try:
        if request.source_type == "sci":
            scraper = SCIScraper()
            result = await scraper.sync_recent_judgments()
        elif request.source_type == "hc":
            scraper = HCScraper()
            result = await scraper.sync_recent_judgments()
        else:
            raise HTTPException(status_code=400, detail="Invalid source type")
        
        return {
            "source_type": request.source_type,
            "result": result,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Source sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sources/status")
async def get_sources_status():
    """Get status of legal sources"""
    try:
        status = await retriever.get_sources_status()
        return status
        
    except Exception as e:
        logger.error(f"Failed to get sources status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Export functionality
@app.get("/export/chat/{chat_id}")
async def export_chat(chat_id: str, format: str = "markdown"):
    """Export chat transcript"""
    try:
        # This would be implemented with chat storage
        # For now, return a placeholder
        return {
            "chat_id": chat_id,
            "format": format,
            "download_url": f"/downloads/chat_{chat_id}.{format}"
        }
        
    except Exception as e:
        logger.error(f"Chat export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("BACKEND_PORT", 8877)),
        reload=True
    )