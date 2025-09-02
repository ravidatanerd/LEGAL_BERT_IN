# InLegal Desktop - Indian Legal Research Assistant

A comprehensive legal research and judgment drafting tool specifically designed for Indian law, combining advanced AI technology with legal expertise to provide accurate, efficient, and bilingual legal research capabilities.

## 🚀 Features

### Core Capabilities
- **Document Ingestion**: OCR-free PDF processing using vision-language models (Donut, Pix2Struct, OpenAI Vision)
- **Semantic Search**: InLegalBERT embeddings for accurate legal document retrieval
- **AI-Powered Q&A**: Intelligent legal research with citation support
- **Judgment Generation**: Structured judgment drafting with legal frameworks
- **Bilingual Support**: English and Hindi language support
- **Statute Integration**: Access to Indian Penal Code, CrPC, Evidence Act

### Technical Features
- **Hybrid Retrieval**: FAISS (dense) + BM25 (sparse) search
- **Mixed Script Support**: Devanagari and English text processing
- **Streaming Interface**: ChatGPT-style user experience
- **Windows Standalone**: PyInstaller executable with Inno Setup installer
- **Production Ready**: Comprehensive error handling and logging

## 📋 System Requirements

### Desktop Application
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 2GB free disk space
- **Network**: Internet connection for AI features

### Development Environment
- **Python**: 3.9+
- **OS**: Windows, macOS, or Linux
- **GPU**: Optional (CUDA-compatible for faster processing)

## 🛠️ Installation

### Option 1: Windows Installer (Recommended)
1. Download `InLegalDesk_Installer.exe` from releases
2. Run installer as Administrator
3. Follow installation wizard
4. Launch from Start Menu or Desktop

### Option 2: Development Setup
```bash
# Clone repository
git clone https://github.com/your-org/inlegal.git
cd inlegal

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
pip install -r desktop/requirements.txt

# Set up environment
cp backend/.env.sample backend/.env
cp desktop/.env.sample desktop/.env

# Add your OpenAI API key to .env files
echo "OPENAI_API_KEY=sk-your-key-here" >> backend/.env
echo "OPENAI_API_KEY=sk-your-key-here" >> desktop/.env
```

## 🚀 Quick Start

### 1. Start the Backend
```bash
cd backend
python app.py
```

### 2. Launch Desktop App
```bash
cd desktop
python main.py
```

### 3. First Use
1. Click "Ingest Statutes" to download Indian legal statutes
2. Upload your legal documents (PDF format)
3. Start asking legal questions
4. Generate structured judgments

## 📖 Usage Guide

### Document Management
- **Upload Documents**: Drag and drop PDF files or use Upload button
- **Supported Formats**: PDF documents with text or images
- **Processing**: Automatic OCR-free extraction using vision-language models

### Legal Research
- **Ask Questions**: Type legal questions in natural language
- **Citations**: View source documents with page references
- **Language**: Switch between English, Hindi, or Auto-detect

### Judgment Generation
1. Click "Generate Judgment"
2. Enter case facts
3. List issues for determination
4. Select language preference
5. Review generated structured judgment

### Export Options
- **Chat Export**: Save conversation transcripts as Markdown
- **Judgment Export**: Export generated judgments
- **Document Management**: View and manage uploaded documents

## 🔧 Configuration

### Environment Variables
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Embedding Model
EMBED_MODEL=law-ai/InLegalBERT

# Vision-Language Models
VLM_ORDER=donut,pix2struct,openai,tesseract_fallback
ENABLE_OCR_FALLBACK=false
TESSERACT_LANG=hin+eng

# Server Configuration
BACKEND_PORT=8877
MAX_WORKERS=0
VLM_BATCH_SIZE=4

# Optional Features
ENABLE_PLAYWRIGHT=false  # For web scraping
```

### Model Configuration
- **InLegalBERT**: Default embedding model for legal text
- **Donut**: Primary document understanding model
- **Pix2Struct**: Secondary document understanding model
- **OpenAI Vision**: Fallback for complex documents
- **Tesseract**: OCR fallback (optional)

## 🏗️ Building from Source

### Prerequisites
- Python 3.9+
- Inno Setup 6 (for Windows installer)
- Git

### Build Process
```bash
# 1. Install build dependencies
pip install pyinstaller

# 2. Build executable
cd desktop
pyinstaller --noconfirm --onedir --name InLegalDesk main.py \
  --add-data "server;server" \
  --add-data ".env.sample;.env.sample"

# 3. Create installer (Windows)
cd ../installer
powershell -ExecutionPolicy Bypass -File build_installer.ps1
```

### Build Scripts
- **PowerShell**: `installer/build_installer.ps1` (Windows)
- **Manual**: Follow steps in `installer/README.md`

## 🧪 Testing

### E2E Smoke Tests
```bash
# Run comprehensive tests
./run_e2e.sh

# Or using Python
python run_e2e.py

# With custom backend URL
python run_e2e.py --backend-url http://localhost:8877
```

### Test Coverage
- Backend health check
- Sources status and ingestion
- Document upload and processing
- Question answering
- Judgment generation
- Document listing and summarization

## 📁 Project Structure

```
inlegal/
├── backend/                 # FastAPI backend
│   ├── app.py              # Main application
│   ├── ingest.py           # Document ingestion
│   ├── retriever.py        # Search and retrieval
│   ├── llm.py              # LLM services
│   ├── chunking.py         # Text chunking
│   ├── utils/              # Utilities
│   ├── extractors/         # Vision-language models
│   └── sources/            # Legal sources
├── desktop/                # PySide6 desktop app
│   ├── main.py             # Main application
│   ├── api_client.py       # Backend client
│   ├── server_launcher.py  # Server management
│   └── requirements.txt    # Dependencies
├── installer/              # Windows installer
│   ├── InLegalDesk.iss     # Inno Setup script
│   ├── build_installer.ps1 # Build script
│   └── README.md           # Build instructions
├── data/                   # Application data
│   ├── uploads/            # Uploaded documents
│   ├── downloads/          # Downloaded statutes
│   ├── chunks/             # Document chunks
│   └── embeddings/         # FAISS indexes
├── run_e2e.sh             # E2E test script
├── run_e2e.py             # E2E test script (Python)
└── README.md              # This file
```

## 🔌 API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `GET /sources/status` - Sources status
- `POST /sources/add_statutes` - Ingest Indian statutes
- `POST /upload` - Upload documents
- `POST /ask` - Ask legal questions
- `POST /summarize` - Summarize documents
- `POST /judgment` - Generate judgments
- `GET /documents` - List documents

### Request/Response Examples
```python
# Ask a question
POST /ask
{
  "question": "What are the provisions regarding confessions?",
  "language": "auto",
  "max_sources": 5
}

# Generate judgment
POST /judgment
{
  "case_facts": "Contract dispute case facts...",
  "issues": ["Issue 1", "Issue 2"],
  "language": "auto"
}
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use type hints
- Add docstrings for functions
- Include error handling

### Testing
- Run E2E tests before submitting
- Add unit tests for new features
- Ensure backward compatibility

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Third-Party Licenses
- **InLegalBERT**: Apache 2.0
- **PyTorch**: BSD-3-Clause
- **Transformers**: Apache 2.0
- **FAISS**: MIT
- **PySide6**: LGPL v3
- **FastAPI**: MIT

## ⚠️ Disclaimer

This software is for educational and research purposes. It is not intended to replace professional legal advice. Users should consult qualified legal professionals for important legal matters.

The AI-generated content should be reviewed and validated by legal experts before use in professional contexts.

## 🆘 Support

### Documentation
- Check the application help menu
- Review API documentation
- Read the installer README

### Issues
- Report bugs through GitHub Issues
- Include system information and logs
- Provide steps to reproduce

### Contact
- Email: support@inlegal.ai
- GitHub: [Issues](https://github.com/your-org/inlegal/issues)
- Documentation: [Wiki](https://github.com/your-org/inlegal/wiki)

## 🗺️ Roadmap

### Version 1.1
- [ ] Enhanced document processing
- [ ] More legal sources integration
- [ ] Improved UI/UX
- [ ] Performance optimizations

### Version 1.2
- [ ] Multi-language support
- [ ] Advanced search filters
- [ ] Document comparison
- [ ] Collaborative features

### Version 2.0
- [ ] Cloud deployment
- [ ] API access
- [ ] Mobile application
- [ ] Enterprise features

---

**InLegal Desktop** - Empowering legal research with AI technology.