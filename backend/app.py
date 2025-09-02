"""
FastAPI backend for Indian legal research & judgment drafting
"""
import os
import re
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, field_validator
import uvicorn
from dotenv import load_dotenv

from ingest import DocumentIngestor
from retriever import LegalRetriever
from llm import LegalLLM
from sources.indiacode import IndiaCodeDownloader
from vlm_config import vlm_configurator, VLMQuality, get_vlm_configuration_info
from security import (
    SecurityConfig, InputValidator, SecurityHeadersMiddleware, 
    FileSecurityValidator, SecureEnvironment
)
from rate_limiter import RateLimitMiddleware

# Load environment variables
load_dotenv()

# Configure secure logging
from secure_logging import setup_secure_logging, audit_logger
setup_secure_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Indian Legal Research API",
    description="AI-powered legal research and judgment drafting for Indian law",
    version="1.0.0"
)

# Security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

# CORS middleware with secure origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=SecurityConfig.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Restrict to needed methods
    allow_headers=["Content-Type", "Authorization"],
)

# Global components
ingestor: Optional[DocumentIngestor] = None
retriever: Optional[LegalRetriever] = None
llm: Optional[LegalLLM] = None

class QueryRequest(BaseModel):
    question: str = Field(..., description="Legal question to ask", min_length=1, max_length=10000)
    language: str = Field(default="auto", description="Response language: en, hi, or auto")
    max_results: int = Field(default=5, description="Maximum number of sources to retrieve", ge=1, le=20)
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v):
        return InputValidator.sanitize_query(v)
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        if not InputValidator.validate_language_code(v):
            raise ValueError("Invalid language code")
        return v

class SummarizeRequest(BaseModel):
    document_id: str = Field(..., description="Document ID to summarize", min_length=1, max_length=100)
    language: str = Field(default="auto", description="Response language: en, hi, or auto")
    
    @field_validator('document_id')
    @classmethod
    def validate_document_id(cls, v):
        # Only allow alphanumeric, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Invalid document ID format")
        return v
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        if not InputValidator.validate_language_code(v):
            raise ValueError("Invalid language code")
        return v

class JudgmentRequest(BaseModel):
    case_facts: str = Field(..., description="Facts of the case", min_length=1, max_length=50000)
    legal_issues: List[str] = Field(..., description="Legal issues to address", min_items=1, max_items=10)
    language: str = Field(default="auto", description="Response language: en, hi, or auto")
    
    @field_validator('case_facts')
    @classmethod
    def validate_case_facts(cls, v):
        return InputValidator.sanitize_query(v)
    
    @field_validator('legal_issues')
    @classmethod
    def validate_legal_issues(cls, v):
        if not v:
            raise ValueError("At least one legal issue is required")
        
        sanitized_issues = []
        for issue in v:
            if len(issue.strip()) < 5:
                raise ValueError("Legal issues must be at least 5 characters")
            sanitized_issues.append(InputValidator.sanitize_query(issue))
        
        return sanitized_issues
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        if not InputValidator.validate_language_code(v):
            raise ValueError("Invalid language code")
        return v

class VLMConfigRequest(BaseModel):
    preset: Optional[str] = Field(None, description="VLM quality preset: premium, high, balanced, fast, offline, basic")
    custom_order: Optional[List[str]] = Field(None, description="Custom VLM model order")
    
    @field_validator('preset')
    @classmethod
    def validate_preset(cls, v):
        if v is not None:
            valid_presets = [quality.value for quality in VLMQuality]
            if v not in valid_presets:
                raise ValueError(f"Invalid preset. Must be one of: {', '.join(valid_presets)}")
        return v
    
    @field_validator('custom_order')
    @classmethod
    def validate_custom_order(cls, v):
        if v is not None:
            valid_models = ["openai", "donut", "pix2struct", "tesseract_fallback"]
            for model in v:
                if model not in valid_models:
                    raise ValueError(f"Invalid model '{model}'. Must be one of: {', '.join(valid_models)}")
        return v

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
async def upload_document(request: Request, file: UploadFile = File(...)):
    """Upload and ingest a PDF document with security validation"""
    try:
        if not ingestor:
            raise HTTPException(status_code=503, detail="Ingestor not initialized")
        
        # Validate filename
        if not InputValidator.validate_filename(file.filename):
            raise HTTPException(status_code=400, detail="Invalid filename or file type")
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        if not InputValidator.validate_file_size(len(content)):
            raise HTTPException(status_code=400, detail="File too large")
        
        # Create secure file path
        safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', file.filename)
        file_path = FileSecurityValidator.sanitize_file_path(
            safe_filename, "data/uploads"
        )
        
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Validate PDF file
        validation_result = FileSecurityValidator.validate_pdf_file(file_path)
        
        if not validation_result["is_valid"]:
            # Clean up invalid file
            Path(file_path).unlink(missing_ok=True)
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid PDF file: {', '.join(validation_result['errors'])}"
            )
        
        # Log warnings if any
        if validation_result["warnings"]:
            logger.warning(f"PDF warnings for {file.filename}: {validation_result['warnings']}")
        
        # Audit log file upload
        client_ip = request.client.host if request.client else "unknown"
        audit_logger.log_file_upload(safe_filename, len(content), client_ip)
        
        # Ingest document
        doc_id = await ingestor.ingest_document(file_path)
        
        return {
            "status": "success",
            "document_id": doc_id,
            "filename": safe_filename,
            "file_info": validation_result["file_info"],
            "warnings": validation_result["warnings"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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

@app.get("/vlm/config")
async def get_vlm_configuration():
    """Get current VLM configuration and available options"""
    try:
        config_info = get_vlm_configuration_info()
        return {
            "current_configuration": config_info,
            "available_presets": {
                quality.value: {
                    "description": preset["description"],
                    "cost": preset["cost"],
                    "speed": preset["speed"],
                    "accuracy": preset["accuracy"],
                    "requirements": preset["requirements"]
                }
                for quality, preset in vlm_configurator.PRESETS.items()
            },
            "available_models": config_info["available_models"]
        }
    except Exception as e:
        logger.error(f"Failed to get VLM configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vlm/config")
async def set_vlm_configuration(request: VLMConfigRequest):
    """Set VLM configuration using preset or custom order"""
    try:
        if request.preset and request.custom_order:
            raise HTTPException(
                status_code=400, 
                detail="Cannot specify both preset and custom_order"
            )
        
        if not request.preset and not request.custom_order:
            raise HTTPException(
                status_code=400, 
                detail="Must specify either preset or custom_order"
            )
        
        if request.preset:
            # Set using preset
            quality = VLMQuality(request.preset)
            new_order = vlm_configurator.set_preset(quality)
            config_type = f"preset ({request.preset})"
        else:
            # Set using custom order
            new_order = vlm_configurator.set_custom_order(request.custom_order)
            config_type = "custom"
        
        # Validate the new configuration
        validation = vlm_configurator.validate_configuration(new_order)
        warnings = []
        for model, is_valid in validation.items():
            if not is_valid:
                warnings.append(f"Model '{model}' may not work properly (missing requirements)")
        
        return {
            "status": "success",
            "message": f"VLM configuration updated to {config_type}",
            "new_order": new_order,
            "validation": validation,
            "warnings": warnings,
            "note": "Restart the application for changes to take full effect"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set VLM configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vlm/recommendations")
async def get_vlm_recommendations():
    """Get VLM configuration recommendations based on current environment"""
    try:
        recommendations = vlm_configurator.get_recommendations()
        available_models = vlm_configurator.get_available_models()
        
        # Check what's actually available
        model_status = {}
        for model_name, model_info in available_models.items():
            if model_name == "openai":
                model_status[model_name] = {
                    "available": bool(os.getenv("OPENAI_API_KEY")),
                    "reason": "OPENAI_API_KEY configured" if os.getenv("OPENAI_API_KEY") else "Missing OPENAI_API_KEY"
                }
            elif model_name == "tesseract_fallback":
                model_status[model_name] = {
                    "available": True,  # Usually available
                    "reason": "OCR fallback (usually works)"
                }
            elif model_name in ["donut", "pix2struct"]:
                try:
                    import torch
                    import transformers
                    has_gpu = torch.cuda.is_available()
                    model_status[model_name] = {
                        "available": True,
                        "reason": f"Transformers available, GPU: {'Yes' if has_gpu else 'No (CPU only)'}"
                    }
                except ImportError:
                    model_status[model_name] = {
                        "available": False,
                        "reason": "Missing transformers or torch"
                    }
        
        return {
            "recommendations": recommendations,
            "model_status": model_status,
            "suggested_configs": {
                "best_quality": "openai,donut,pix2struct,tesseract_fallback",
                "no_api_needed": "donut,pix2struct,tesseract_fallback",
                "fastest": "tesseract_fallback,openai",
                "api_only": "openai,tesseract_fallback"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get VLM recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 8877))
    uvicorn.run(app, host="0.0.0.0", port=port)