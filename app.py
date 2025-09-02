import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="InLegalDesk Backend", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    """Health check endpoint returning basic status and config values."""
    return {
        "status": "ok",
        "port": os.getenv("BACKEND_PORT", 8877),
        "embed_model": os.getenv("EMBED_MODEL"),
    }


# --- Placeholder endpoints ---------------------------------------------------

@app.post("/sources/add_statutes")
async def add_statutes() -> JSONResponse:
    # TODO: download and ingest IndiaCode PDFs
    return JSONResponse({"msg": "add_statutes not yet implemented"}, status_code=501)


@app.post("/ask")
async def ask(question: str):
    # TODO: retrieve & answer via LLM
    return JSONResponse({"msg": "ask not yet implemented"}, status_code=501)


@app.post("/summarize")
async def summarize(doc_id: str):
    # TODO: summarize doc
    return JSONResponse({"msg": "summarize not yet implemented"}, status_code=501)


@app.post("/judgment")
async def judgment(doc_id: str, language: str = "auto"):
    # TODO: generate judgment JSON
    return JSONResponse({"msg": "judgment not yet implemented"}, status_code=501)