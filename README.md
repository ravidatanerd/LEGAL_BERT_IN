# InLegalDesk - Indian Legal Research Platform

An AI-powered legal research and judgment drafting platform for Indian law, featuring OCR-free PDF processing, InLegalBERT embeddings, and a ChatGPT-style desktop interface.

## Features

### 🔍 **Advanced Document Processing**
- Vision-Language Model extraction (OCR-free) from PDFs
- Multiple backends: Donut, Pix2Struct, OpenAI Vision, Tesseract fallback
- 300 DPI PDF rendering with parallel page processing
- Confidence scoring and best-of fusion

### 🧠 **Intelligent Retrieval**
- **InLegalBERT** embeddings from Hugging Face (`law-ai/InLegalBERT`)
- Hybrid search: Dense (FAISS) + Sparse (BM25)
- Mixed Hindi/English script support
- Unicode normalization and text cleaning

### ⚖️ **Legal AI Features**
- **Q&A**: Grounded legal question answering with citations
- **Summarization**: Structured case summaries (Facts, Issues, Arguments, Holding, Relief)
- **Judgment Generation**: Complete legal judgments with JSON schema
- **Bilingual Support**: English and Hindi (Devanagari script)

### 🖥️ **Desktop Application**
- **ChatGPT-style Interface**: Modern chat UI with message bubbles
- **Streaming Responses**: Token-by-token streaming simulation
- **Drag & Drop**: PDF ingestion via drag-and-drop
- **Multi-turn Conversations**: Persistent chat history
- **Citation Support**: Clickable source references
- **Export**: Chat transcripts to Markdown/PDF

### 📦 **Windows Distribution**
- **Standalone Executable**: PyInstaller-built desktop app
- **Windows Installer**: Professional Inno Setup installer
- **No Python Required**: Runs on Windows without Python installation

## Quick Start

### Backend Setup

1. **Install Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.sample .env
   # Edit .env with your OpenAI API key
   ```

3. **Run Backend**:
   ```bash
   python app.py
   ```

### Desktop App (Development)

1. **Install Dependencies**:
   ```bash
   cd desktop
   pip install -r requirements.txt
   ```

2. **Copy Backend**:
   ```bash
   cp -r ../backend server/
   ```

3. **Run Desktop App**:
   ```bash
   python main.py
   ```

### Windows Installer Build

1. **Prerequisites**:
   - Python 3.8+
   - Inno Setup 6+
   - PowerShell 5.0+

2. **Build Installer**:
   ```powershell
   cd installer
   .\build_installer.ps1
   ```

3. **Install**:
   ```cmd
   output\InLegalDesk_Installer.exe
   ```

## API Endpoints

### Core Endpoints

- `GET /health` - Health check
- `POST /ask` - Legal question answering
- `POST /summarize` - Document summarization  
- `POST /judgment` - Judgment generation
- `POST /documents/upload` - PDF upload and ingestion

### Sources Management

- `POST /sources/add_statutes` - Download Indian statutes (IPC, CrPC, Evidence Act)
- `GET /sources/status` - Get ingested sources status
- `POST /sources/sync` - Sync from SCI/HC (placeholder)

## Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-xxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Embedding Model
EMBED_MODEL=law-ai/InLegalBERT

# Vision-Language Models
VLM_ORDER=donut,pix2struct,openai,tesseract_fallback
MAX_WORKERS=0
VLM_BATCH_SIZE=4
ENABLE_OCR_FALLBACK=false
TESSERACT_LANG=hin+eng

# Scraping
ENABLE_PLAYWRIGHT=false
HTTP_USER_AGENT=IndiaLawPro/1.0 (+contact@example.com)
HTTP_TIMEOUT=30

# Server
BACKEND_PORT=8877
```

## Project Structure

```
├── backend/                 # FastAPI backend
│   ├── app.py              # Main FastAPI application
│   ├── ingest.py           # Document ingestion
│   ├── retriever.py        # InLegalBERT + FAISS + BM25
│   ├── llm.py              # LLM integration
│   ├── chunking.py         # Text chunking
│   ├── utils/              # Utility modules
│   ├── extractors/         # VLM extractors
│   ├── sources/            # Source downloaders
│   └── requirements.txt
├── desktop/                # PySide6 desktop app
│   ├── main.py             # Main GUI application
│   ├── api_client.py       # Backend API client
│   ├── server_launcher.py  # Server management
│   └── requirements.txt
├── installer/              # Windows installer
│   ├── build_installer.ps1 # Build script
│   ├── InLegalDesk.iss     # Inno Setup script
│   ├── assets/             # Icons and resources
│   └── README.md           # Build instructions
└── data/                   # Data storage
    ├── downloads/          # Downloaded PDFs
    ├── embeddings/         # Vector embeddings
    └── documents/          # Document metadata
```

## Indian Legal Sources

### Pre-configured Statutes

The platform automatically downloads and ingests:

1. **Indian Penal Code, 1860** - Criminal law provisions
2. **Code of Criminal Procedure, 1973** - Criminal procedure
3. **Indian Evidence Act, 1872** - Evidence and proof

### Future Sources (Planned)

- Supreme Court of India judgments
- High Court judgments (Delhi, Bombay, Madras, Calcutta)
- Additional statutes and regulations

## Development

### Running Tests

```bash
# Start backend
cd backend && python app.py

# Run E2E tests
python run_e2e.py
# or
./run_e2e.sh
```

### Development Mode

```bash
# Backend with auto-reload
cd backend
uvicorn app:app --reload --port 8877

# Desktop app with backend URL
cd desktop
BACKEND_URL=http://127.0.0.1:8877 python main.py
```

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **InLegalBERT** - Legal domain embeddings
- **FAISS** - Vector similarity search
- **BM25** - Sparse retrieval
- **PyMuPDF** - PDF processing
- **Transformers** - Hugging Face models

### Desktop App
- **PySide6** - Qt-based GUI framework
- **Markdown** - Rich text rendering
- **httpx** - Async HTTP client

### Vision-Language Models
- **Donut** - Document understanding transformer
- **Pix2Struct** - Visual question answering
- **OpenAI Vision** - GPT-4 Vision API
- **Tesseract** - OCR fallback

### Build Tools
- **PyInstaller** - Python to executable
- **Inno Setup** - Windows installer creation

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in each module
- Review the troubleshooting sections

## Getting Started

### 🚀 **Quick Demo**

1. **Clone Repository**:
   ```bash
   git clone <repository-url>
   cd inlegaldesk
   ```

2. **Start Backend**:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   cp .env.sample .env
   # Edit .env with your OpenAI API key
   python app.py
   ```

3. **Run Desktop App** (separate terminal):
   ```bash
   cd desktop
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp -r ../backend server/
   python main.py
   ```

### 📦 **Windows Installer**

For end users on Windows:

1. Download `InLegalDesk_Installer.exe`
2. Run as Administrator
3. Follow installation wizard
4. Launch from Start Menu

Build installer yourself:
```powershell
cd installer
.\build_installer.ps1
```

## 🧪 **Testing**

### Backend Tests
```bash
cd backend
source venv/bin/activate
python app.py &
sleep 10
python run_e2e.py
```

### Expected Results
- ✅ Health check passes
- ✅ Statute download works
- ✅ Document upload succeeds
- ✅ Question answering responds (with/without OpenAI key)
- ✅ Judgment generation works (fallback mode without key)

## 🔧 **Configuration Guide**

### Essential Setup

1. **OpenAI API Key** (for full functionality):
   ```bash
   OPENAI_API_KEY=sk-your_actual_key_here
   ```

2. **Model Selection**:
   ```bash
   # Fastest (requires OpenAI key)
   VLM_ORDER=openai
   
   # Best quality (local + API)
   VLM_ORDER=donut,pix2struct,openai,tesseract_fallback
   
   # Local only (no API key needed)
   VLM_ORDER=donut,pix2struct
   ```

3. **Performance Tuning**:
   ```bash
   MAX_WORKERS=4      # Parallel processing
   VLM_BATCH_SIZE=2   # Reduce for lower memory
   ```

## 📊 **System Requirements**

### Minimum Requirements
- **OS**: Windows 10 (64-bit) / Linux / macOS
- **RAM**: 4GB (8GB recommended)
- **Storage**: 5GB free space
- **Internet**: Required for model downloads and API calls

### Recommended Specifications
- **RAM**: 16GB+ for large documents
- **GPU**: NVIDIA GPU for faster processing
- **Storage**: SSD for better performance
- **CPU**: Multi-core for parallel processing

## 🔄 **Workflow Examples**

### Legal Research Workflow

1. **Setup**: Install app and configure API key
2. **Ingest**: Add statutes and case documents
3. **Research**: Ask specific legal questions
4. **Analyze**: Review sources and citations
5. **Export**: Save findings to Markdown

### Judgment Drafting Workflow

1. **Prepare**: Upload relevant case documents
2. **Input**: Enter case facts and legal issues
3. **Generate**: Create structured judgment
4. **Review**: Examine legal analysis and citations
5. **Refine**: Iterate with follow-up questions

## 🛠 **Development Guide**

### Architecture Overview

```
┌─────────────────┐    HTTP/REST    ┌─────────────────┐
│   Desktop App   │ ◄─────────────► │  FastAPI Backend│
│   (PySide6)     │                 │                 │
└─────────────────┘                 └─────────────────┘
         │                                   │
         │                                   │
    ┌─────────┐                         ┌─────────┐
    │ Chat UI │                         │   AI    │
    │ Markdown│                         │ Models  │
    │ Export  │                         │ FAISS   │
    └─────────┘                         │ BM25    │
                                        └─────────┘
```

### Adding Features

#### New Chat Features
1. Modify `main.py` chat interface
2. Add new API endpoints in backend
3. Update API client methods
4. Test integration

#### New Document Types
1. Add extractor in `backend/extractors/`
2. Update ingestion pipeline
3. Test with sample documents

### Code Quality

```bash
# Format code
black backend/ desktop/

# Type checking
mypy backend/ desktop/

# Linting
flake8 backend/ desktop/
```

## 📈 **Performance Optimization**

### Backend Optimization

- **GPU Acceleration**: Enable CUDA for VLM models
- **Batch Processing**: Increase `VLM_BATCH_SIZE` for large documents
- **Caching**: FAISS indexes are cached automatically
- **Parallel Processing**: Tune `MAX_WORKERS` based on CPU cores

### Desktop App Optimization

- **UI Responsiveness**: API calls run in background threads
- **Memory Management**: Clear chat history periodically
- **Startup Time**: Backend server starts asynchronously

## 🔒 **Security & Privacy**

### Data Handling
- **Local Processing**: Documents processed locally by default
- **API Security**: OpenAI API calls use HTTPS
- **No Data Retention**: No chat data sent to external services (except OpenAI)
- **File Cleanup**: Temporary files cleaned automatically

### Recommendations
- **API Keys**: Store securely, never share
- **Sensitive Documents**: Use local-only VLM models
- **Network Security**: Use VPN for sensitive research
- **Regular Updates**: Keep application updated

## 🌟 **Advanced Usage**

### Custom Legal Databases

Add your own legal documents:
1. Upload PDFs via drag-and-drop
2. Documents are automatically indexed
3. Search across all ingested content
4. Citations include your documents

### Batch Processing

Process multiple documents:
1. Drop multiple PDFs simultaneously
2. Monitor progress in status panel
3. All documents become searchable
4. Cross-document citations supported

### API Integration

Use the backend programmatically:
```python
import httpx

async def ask_legal_question(question: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8877/ask",
            json={"question": question, "language": "auto"}
        )
        return response.json()
```

## 🎯 **Use Cases**

### Legal Practitioners
- **Case Research**: Find relevant precedents and statutes
- **Judgment Drafting**: Generate structured legal judgments
- **Document Analysis**: Extract key information from case files
- **Citation Verification**: Cross-reference legal sources

### Law Students
- **Study Aid**: Ask questions about legal concepts
- **Case Analysis**: Understand legal reasoning
- **Research Training**: Learn legal research methodology
- **Exam Preparation**: Practice with legal scenarios

### Legal Researchers
- **Academic Research**: Analyze legal trends and patterns
- **Comparative Analysis**: Compare different legal interpretations
- **Statistical Analysis**: Extract data from large document sets
- **Publication Support**: Generate citations and references

## 🤝 **Contributing**

### Ways to Contribute

1. **Bug Reports**: Report issues with detailed information
2. **Feature Requests**: Suggest new functionality
3. **Code Contributions**: Submit pull requests
4. **Documentation**: Improve guides and examples
5. **Testing**: Test on different systems and use cases

### Development Setup

1. **Fork Repository**
2. **Create Feature Branch**: `git checkout -b feature/new-feature`
3. **Make Changes**: Follow coding standards
4. **Add Tests**: Ensure functionality works
5. **Submit PR**: Include description and testing notes

## 📞 **Support**

### Community Support
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share tips
- **Wiki**: Community-maintained documentation

### Professional Support
- **Custom Development**: Tailored legal AI solutions
- **Enterprise Deployment**: Large-scale installations
- **Training**: User training and onboarding
- **Integration**: Custom API integrations

## 🏆 **Acknowledgments**

### Models and Libraries
- **InLegalBERT**: Legal domain embeddings by law-ai
- **Donut**: Document understanding by NAVER CLOVA
- **Pix2Struct**: Visual reasoning by Google Research
- **FastAPI**: Modern Python web framework
- **PySide6**: Qt for Python GUI framework

### Data Sources
- **IndiaCode**: Official Indian legal statutes
- **Supreme Court of India**: Judgment database
- **High Courts**: Regional legal decisions

## 📄 **License**

MIT License - See [LICENSE](LICENSE) file for details.

## ⚠️ **Disclaimer**

This software is for research and educational purposes. Legal advice should always be obtained from qualified legal professionals. The AI-generated content should be reviewed and verified by legal experts before use in any legal proceedings.

**Important**: This tool assists with legal research but does not replace professional legal judgment. Always verify AI-generated content with authoritative legal sources and qualified practitioners.