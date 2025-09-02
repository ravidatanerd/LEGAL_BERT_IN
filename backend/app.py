"""
FastAPI backend for Indian legal research & judgment drafting
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
import logging
from dotenv import load_dotenv

from ingest import DocumentIngester
from retriever import DocumentRetriever
from llm import LLMService
from sources.indiacode import IndiaCodeSource
from sources.sci import SCISource
from sources.hc import HCSource

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="InLegal Research API",
    description="Indian Legal Research & Judgment Drafting API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
ingester = None
retriever = None
llm_service = None
indiacode_source = None
sci_source = None
hc_source = None

# Pydantic models
class AskRequest(BaseModel):
    question: str
    language: str = "auto"
    max_sources: int = 5

class SummarizeRequest(BaseModel):
    document_ids: List[str]
    language: str = "auto"

class JudgmentRequest(BaseModel):
    case_facts: str
    issues: List[str]
    language: str = "auto"

class SourceStatus(BaseModel):
    indiacode: bool
    sci: bool
    hc: bool
    total_documents: int

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global ingester, retriever, llm_service, indiacode_source, sci_source, hc_source
    
    try:
        # Initialize services
        ingester = DocumentIngester()
        retriever = DocumentRetriever()
        llm_service = LLMService()
        
        # Initialize sources
        indiacode_source = IndiaCodeSource()
        if os.getenv("ENABLE_PLAYWRIGHT", "false").lower() == "true":
            sci_source = SCISource()
            hc_source = HCSource()
        
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/sources/status")
async def get_sources_status():
    """Get status of all sources"""
    try:
        total_docs = await retriever.get_document_count() if retriever else 0
        
        return SourceStatus(
            indiacode=indiacode_source is not None,
            sci=sci_source is not None,
            hc=hc_source is not None,
            total_documents=total_docs
        )
    except Exception as e:
        logger.error(f"Error getting sources status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sources/add_statutes")
async def add_statutes(background_tasks: BackgroundTasks):
    """Add Indian statutes from IndiaCode"""
    try:
        if not indiacode_source:
            raise HTTPException(status_code=503, detail="IndiaCode source not available")
        
        # Add background task to download and ingest statutes
        background_tasks.add_task(indiacode_source.download_and_ingest_statutes)
        
        return {"message": "Statute ingestion started in background"}
    except Exception as e:
        logger.error(f"Error adding statutes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sources/sync")
async def sync_sources(background_tasks: BackgroundTasks):
    """Sync all sources (SCI/HC scraping)"""
    try:
        if not sci_source or not hc_source:
            raise HTTPException(status_code=503, detail="SCI/HC sources not available")
        
        # Add background tasks for syncing
        background_tasks.add_task(sci_source.sync_recent_cases)
        background_tasks.add_task(hc_source.sync_recent_cases)
        
        return {"message": "Source sync started in background"}
    except Exception as e:
        logger.error(f"Error syncing sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a document"""
    try:
        if not ingester:
            raise HTTPException(status_code=503, detail="Document ingester not available")
        
        # Save uploaded file
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(exist_ok=True)
        
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Ingest document
        doc_id = await ingester.ingest_document(file_path)
        
        return {"document_id": doc_id, "filename": file.filename}
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask_question(request: AskRequest):
    """Ask a question with grounded QA"""
    try:
        if not retriever or not llm_service:
            raise HTTPException(status_code=503, detail="Services not available")
        
        # Retrieve relevant documents
        results = await retriever.search(request.question, top_k=request.max_sources)
        
        # Generate answer with citations
        answer = await llm_service.generate_answer(
            question=request.question,
            context=results,
            language=request.language
        )
        
        return {
            "answer": answer["text"],
            "citations": answer["citations"],
            "sources": results
        }
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize")
async def summarize_documents(request: SummarizeRequest):
    """Generate structured summary of documents"""
    try:
        if not retriever or not llm_service:
            raise HTTPException(status_code=503, detail="Services not available")
        
        # Get documents
        documents = await retriever.get_documents_by_ids(request.document_ids)
        
        # Generate summary
        summary = await llm_service.generate_summary(
            documents=documents,
            language=request.language
        )
        
        return summary
    except Exception as e:
        logger.error(f"Error summarizing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/judgment")
async def generate_judgment(request: JudgmentRequest):
    """Generate structured judgment"""
    try:
        if not llm_service:
            raise HTTPException(status_code=503, detail="LLM service not available")
        
        # Generate judgment
        judgment = await llm_service.generate_judgment(
            case_facts=request.case_facts,
            issues=request.issues,
            language=request.language
        )
        
        return judgment
    except Exception as e:
        logger.error(f"Error generating judgment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents():
    """List all ingested documents"""
    try:
        if not retriever:
            raise HTTPException(status_code=503, detail="Retriever not available")
        
        documents = await retriever.list_documents()
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    try:
        if not retriever:
            raise HTTPException(status_code=503, detail="Retriever not available")
        
        await retriever.delete_document(document_id)
        return {"message": "Document deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 8877))
    uvicorn.run(app, host="0.0.0.0", port=port)