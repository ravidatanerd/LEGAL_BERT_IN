# InLegalDesk Backend

FastAPI backend for Indian legal research and judgment drafting with vision-language PDF processing.

## Features

### 🔍 **Vision-Language PDF Extraction**
- **OCR-Free Processing**: Uses advanced VLM models instead of traditional OCR
- **Multiple Backends**: Donut, Pix2Struct, OpenAI Vision, Tesseract fallback
- **High-Resolution Rendering**: 300 DPI PDF page rendering
- **Parallel Processing**: Multi-threaded page extraction
- **Confidence Scoring**: Best-of fusion with quality metrics

### 🧠 **InLegalBERT Integration**
- **Legal Domain Embeddings**: Specialized `law-ai/InLegalBERT` model
- **Hybrid Retrieval**: Dense (FAISS) + Sparse (BM25) search
- **Mixed Script Support**: Hindi (Devanagari) and English text
- **Unicode Normalization**: Proper handling of Indian language text

### ⚖️ **Legal AI Endpoints**
- **Q&A**: `/ask` - Grounded question answering with bracket citations
- **Summarization**: `/summarize` - Structured case summaries
- **Judgment Generation**: `/judgment` - Complete legal judgments
- **Document Upload**: `/documents/upload` - PDF ingestion

### 📚 **Indian Legal Sources**
- **Automatic Download**: Indian Penal Code, CrPC, Evidence Act
- **IndiaCode Integration**: Direct PDF download from official sources
- **Court Scraping**: SCI/HC judgment scraping (placeholder)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.sample .env
# Edit .env with your OpenAI API key
```

### 3. Run Server

```bash
python app.py
```

The server will start on `http://localhost:8877`

### 4. Test Installation

```bash
# Run E2E tests
python run_e2e.py

# Or use shell script
./run_e2e.sh
```

## API Documentation

### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "components": {
    "ingestor": true,
    "retriever": true,
    "llm": true
  }
}
```

### Ask Legal Question

```bash
POST /ask
Content-Type: application/json

{
  "question": "What are the provisions for bail under CrPC?",
  "language": "auto",
  "max_results": 5
}
```

Response:
```json
{
  "answer": "Under the Code of Criminal Procedure, 1973, bail provisions are covered in Chapter XXXIII (Sections 436-450) [1]. The general principle is that bail is the rule and jail is the exception [2]...",
  "sources": [
    {
      "chunk_id": "doc123_chunk_5",
      "filename": "CrPC_1973.pdf",
      "text": "436. In what cases bail to be taken...",
      "combined_score": 0.85
    }
  ],
  "language_detected": "en"
}
```

### Generate Judgment

```bash
POST /judgment
Content-Type: application/json

{
  "case_facts": "The accused was found with stolen property...",
  "legal_issues": ["Burden of proof", "Admissibility of confession"],
  "language": "auto"
}
```

Response: Structured JSON with metadata, framing, applicable law, analysis, findings, relief, and prediction.

### Upload Document

```bash
POST /documents/upload
Content-Type: multipart/form-data

file: [PDF file]
```

### Download Statutes

```bash
POST /sources/add_statutes
```

Downloads and ingests:
- Indian Penal Code, 1860
- Code of Criminal Procedure, 1973  
- Indian Evidence Act, 1872

## Configuration

### Vision-Language Models

Configure extraction backends via `VLM_ORDER`:

```bash
# Use all backends in order
VLM_ORDER=donut,pix2struct,openai,tesseract_fallback

# OpenAI only (requires API key)
VLM_ORDER=openai

# Local models only
VLM_ORDER=donut,pix2struct
```

### Performance Tuning

```bash
# Parallel processing
MAX_WORKERS=4           # 0 = auto-detect
VLM_BATCH_SIZE=4        # Pages per batch

# OCR Fallback
ENABLE_OCR_FALLBACK=true
TESSERACT_LANG=hin+eng  # Hindi + English
```

### Embedding Model

```bash
# Use InLegalBERT (recommended)
EMBED_MODEL=law-ai/InLegalBERT

# Alternative models (not recommended for legal text)
# EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## Architecture

### Document Processing Pipeline

1. **PDF Upload** → `ingest.py`
2. **Page Rendering** → `utils/pdf_images.py` (300 DPI)
3. **VLM Extraction** → `extractors/` (parallel processing)
4. **Text Normalization** → `utils/textnorm.py`
5. **Chunking** → `chunking.py`
6. **Embedding** → `retriever.py` (InLegalBERT)
7. **Indexing** → FAISS + BM25

### Query Processing Pipeline

1. **Query Normalization** → Mixed script handling
2. **Embedding Generation** → InLegalBERT
3. **Hybrid Search** → Dense + Sparse retrieval
4. **Result Fusion** → Weighted scoring
5. **LLM Generation** → OpenAI API with context
6. **Citation Formatting** → Bracket references [1], [2]

## File Structure

```
backend/
├── app.py                  # FastAPI application
├── ingest.py              # Document ingestion
├── retriever.py           # InLegalBERT + FAISS + BM25
├── llm.py                 # LLM integration
├── chunking.py            # Text chunking
├── utils/
│   ├── pdf_images.py      # PDF rendering
│   ├── textnorm.py        # Text normalization
│   └── parallel.py        # Parallel processing
├── extractors/
│   ├── base.py            # Base extractor class
│   ├── donut.py           # Donut VLM
│   ├── pix2struct.py      # Pix2Struct VLM
│   ├── openai_vision.py   # OpenAI Vision API
│   └── tesseract_fallback.py  # OCR fallback
├── sources/
│   ├── indiacode.py       # IndiaCode downloader
│   ├── sci.py             # SCI scraper (placeholder)
│   └── hc.py              # HC scraper (placeholder)
├── data/
│   ├── downloads/         # Downloaded PDFs
│   ├── embeddings/        # Vector embeddings
│   ├── documents/         # Document metadata
│   └── uploads/           # Uploaded files
├── requirements.txt
├── .env.sample
├── run_e2e.py            # E2E tests
└── run_e2e.sh            # E2E test script
```

## Development

### Adding New Extractors

1. Create new extractor in `extractors/`
2. Inherit from `BaseExtractor`
3. Implement `initialize()` and `extract_text()` methods
4. Add to `VLM_ORDER` configuration

### Adding New Sources

1. Create downloader in `sources/`
2. Implement download and ingestion methods
3. Add endpoint in `app.py`

### Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Test individual components
python -c "from retriever import LegalRetriever; r = LegalRetriever()"
python -c "from ingest import DocumentIngestor; i = DocumentIngestor()"
```

## Production Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8877

CMD ["python", "app.py"]
```

### Systemd Service

```ini
[Unit]
Description=InLegalDesk Backend
After=network.target

[Service]
Type=simple
User=inlegaldesk
WorkingDirectory=/opt/inlegaldesk/backend
Environment=PATH=/opt/inlegaldesk/venv/bin
ExecStart=/opt/inlegaldesk/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Common Issues

1. **Model Download Fails**
   - Check internet connection
   - Verify Hugging Face access
   - Check disk space (models are ~500MB each)

2. **High Memory Usage**
   - Reduce `VLM_BATCH_SIZE`
   - Use CPU-only PyTorch
   - Limit `MAX_WORKERS`

3. **Slow Processing**
   - Enable GPU acceleration
   - Increase `MAX_WORKERS`
   - Use faster VLM models only

4. **OCR Quality Issues**
   - Enable `ENABLE_OCR_FALLBACK=true`
   - Adjust `TESSERACT_LANG` for your documents
   - Increase PDF rendering DPI

### Performance Monitoring

```bash
# Check component status
curl http://localhost:8877/sources/status

# Monitor server logs
tail -f server.log

# Check disk usage
du -sh data/
```

## Security Considerations

- **API Keys**: Never commit API keys to version control
- **File Uploads**: Validate PDF files before processing
- **Rate Limiting**: Implement rate limiting for production
- **Authentication**: Add authentication for production deployment

## Legal Disclaimer

This software is for research and educational purposes. Always consult qualified legal professionals for legal advice. AI-generated content should be reviewed by legal experts before use in legal proceedings.