# InLegalDesk - AI-Powered Legal Research & Judgment Drafting System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![PySide6](https://img.shields.io/badge/PySide6-6.6+-orange.svg)](https://pypi.org/project/PySide6)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

InLegalDesk is a comprehensive AI-powered legal research and judgment drafting system designed specifically for Indian law. It combines advanced vision-language models, legal embeddings, and a ChatGPT-style interface to provide intelligent legal assistance.

## 🌟 Features

### Core Capabilities
- **AI-Powered Legal Research**: Ask questions and get grounded answers with proper citations
- **Document Ingestion**: OCR-free PDF processing using multiple vision-language models
- **Judgment Generation**: Automated structured legal judgment creation
- **Multi-Language Support**: English and Hindi language support
- **ChatGPT-Style Interface**: Intuitive chat-based interaction

### Technical Features
- **Vision-Language Extraction**: Donut, Pix2Struct, OpenAI Vision, Tesseract fallback
- **InLegalBERT Embeddings**: Specialized legal text embeddings from Hugging Face
- **Hybrid Retrieval**: Dense (FAISS) + Sparse (BM25) search
- **Mixed-Script Support**: Hindi/English text processing
- **Windows Desktop App**: Standalone executable with installer

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Desktop GUI   │    │  FastAPI Backend│    │  Vision-Language│
│   (PySide6)     │◄──►│                 │◄──►│  Models         │
│                 │    │                 │    │                 │
│ • Chat Interface│    │ • Legal Q&A     │    │ • Donut         │
│ • File Upload   │    │ • Document      │    │ • Pix2Struct    │
│ • Export        │    │   Ingestion     │    │ • OpenAI Vision │
└─────────────────┘    │ • Judgment      │    │ • Tesseract     │
                       │   Generation    │    └─────────────────┘
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Legal Sources  │
                       │                 │
                       │ • India Code    │
                       │ • Supreme Court │
                       │ • High Courts   │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Windows 10/11** (for desktop app)
- **8GB+ RAM** (recommended for AI models)
- **OpenAI API Key** (optional, for enhanced features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/example/inlegaldesk.git
   cd inlegaldesk
   ```

2. **Install dependencies**
   ```bash
   # Backend dependencies
   pip install -r requirements.txt
   
   # Desktop app dependencies
   pip install -r desktop/requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.sample .env
   # Edit .env with your API keys and settings
   ```

4. **Start the backend**
   ```bash
   python -m uvicorn app:app --host 0.0.0.0 --port 8877
   ```

5. **Run the desktop app**
   ```bash
   cd desktop
   python main.py
   ```

### Windows Installer

For Windows users, you can build a standalone installer:

```powershell
# Build executable and installer
.\installer\build_installer.ps1

# Install the application
.\installer\output\InLegalDesk_Installer.exe
```

## 📖 Usage

### Desktop Application

1. **Start the Application**
   - Launch `InLegalDesk.exe` or run `python desktop/main.py`
   - The app will automatically start the backend server

2. **Ingest Legal Documents**
   - Click "Ingest Statutes" to download Indian legal statutes
   - Drag and drop PDF files for document ingestion
   - Monitor progress in the status panel

3. **Ask Legal Questions**
   - Type your legal question in the chat interface
   - Select language (Auto/English/Hindi)
   - Get AI-powered answers with citations

4. **Generate Judgments**
   - Click "Generate Judgment"
   - Enter case facts and legal issues
   - Get structured legal judgments

### API Usage

```python
import asyncio
from api_client import LegalAPIClient

async def main():
    async with LegalAPIClient() as client:
        # Ask a legal question
        response = await client.ask_question(
            "What is the definition of theft under IPC?",
            language="en"
        )
        print(response["answer"])
        
        # Generate a judgment
        judgment = await client.generate_judgment(
            facts="Petitioner was arrested for theft...",
            issues=["Whether arrest was legal?"],
            language="en"
        )
        print(judgment["judgment"])

asyncio.run(main())
```

## 🔧 Configuration

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
ENABLE_OCR_FALLBACK=false

# Backend Configuration
BACKEND_PORT=8877
```

### Model Configuration

The system supports multiple vision-language models in configurable order:

1. **Donut** - Document understanding transformer
2. **Pix2Struct** - Google's document understanding model
3. **OpenAI Vision** - GPT-4 Vision API (requires API key)
4. **Tesseract** - OCR fallback (requires installation)

## 🧪 Testing

### Run E2E Tests

```bash
# Full E2E tests
./run_e2e.sh

# Smoke tests only
./run_e2e.sh --smoke

# Python script
python run_e2e.py --backend-url http://127.0.0.1:8877
```

### Test Coverage

- ✅ Backend health checks
- ✅ Document ingestion
- ✅ Legal Q&A functionality
- ✅ Judgment generation
- ✅ Sources management
- ✅ Export functionality

## 📁 Project Structure

```
inlegaldesk/
├── app.py                 # FastAPI backend
├── ingest.py              # Document ingestion
├── retriever.py           # Legal retrieval system
├── llm.py                 # LLM integration
├── chunking.py            # Document chunking
├── requirements.txt       # Backend dependencies
├── .env.sample           # Environment template
├── run_e2e.py            # E2E testing script
├── run_e2e.sh            # E2E testing shell script
├── utils/                 # Utility modules
│   ├── pdf_images.py     # PDF rendering
│   ├── textnorm.py       # Text normalization
│   └── parallel.py       # Parallel processing
├── extractors/            # Vision-language extractors
│   ├── base.py           # Base extractor class
│   ├── donut.py          # Donut extractor
│   ├── pix2struct.py     # Pix2Struct extractor
│   ├── openai_vision.py  # OpenAI Vision extractor
│   └── tesseract_fallback.py # Tesseract extractor
├── sources/               # Legal sources
│   ├── indiacode.py      # India Code downloader
│   ├── sci.py            # Supreme Court scraper
│   └── hc.py             # High Court scraper
├── desktop/               # Desktop application
│   ├── main.py           # Main GUI application
│   ├── api_client.py     # API client
│   ├── server_launcher.py # Server launcher
│   └── requirements.txt  # Desktop dependencies
└── installer/             # Windows installer
    ├── InLegalDesk.iss   # Inno Setup script
    ├── build_installer.ps1 # Build script
    └── README.md         # Installer documentation
```

## 🔍 API Reference

### Endpoints

#### Health Check
```http
GET /health
```

#### Legal Q&A
```http
POST /ask
Content-Type: application/json

{
  "question": "What is the definition of theft?",
  "language": "en",
  "max_results": 10
}
```

#### Document Ingestion
```http
POST /ingest
Content-Type: multipart/form-data

file: [PDF file]
metadata: [optional JSON metadata]
```

#### Judgment Generation
```http
POST /judgment
Content-Type: application/json

{
  "case_facts": "Petitioner was arrested...",
  "legal_issues": ["Issue 1", "Issue 2"],
  "language": "en",
  "court_type": "high_court"
}
```

#### Sources Management
```http
POST /sources/add_statutes
POST /sources/sync
GET /sources/status
```

## 🛠️ Development

### Setting up Development Environment

1. **Clone and setup**
   ```bash
   git clone https://github.com/example/inlegaldesk.git
   cd inlegaldesk
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

2. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r desktop/requirements.txt
   pip install pytest black flake8 mypy
   ```

3. **Run tests**
   ```bash
   pytest tests/
   python run_e2e.py
   ```

4. **Code formatting**
   ```bash
   black .
   flake8 .
   mypy .
   ```

### Building from Source

#### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8877
```

#### Desktop App
```bash
# Install desktop dependencies
pip install -r desktop/requirements.txt

# Run desktop app
cd desktop
python main.py
```

#### Windows Executable
```powershell
# Build with PyInstaller
pyinstaller --noconfirm --onedir --name InLegalDesk desktop\main.py

# Or use the build script
.\installer\build_installer.ps1
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings
- Write tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **InLegalBERT**: Legal embeddings model from Hugging Face
- **Donut**: Document understanding transformer
- **Pix2Struct**: Google's document understanding model
- **FastAPI**: Modern web framework for APIs
- **PySide6**: Cross-platform GUI toolkit
- **India Code**: Official repository of Indian laws

## 📞 Support

- **Documentation**: [Wiki](https://github.com/example/inlegaldesk/wiki)
- **Issues**: [GitHub Issues](https://github.com/example/inlegaldesk/issues)
- **Discussions**: [GitHub Discussions](https://github.com/example/inlegaldesk/discussions)
- **Email**: support@inlegaldesk.com

## 🗺️ Roadmap

### Version 1.1
- [ ] Advanced legal citation formatting
- [ ] Multi-court judgment templates
- [ ] Legal document comparison
- [ ] Batch document processing

### Version 1.2
- [ ] Mobile app (React Native)
- [ ] Cloud deployment options
- [ ] Advanced analytics dashboard
- [ ] Legal precedent tracking

### Version 2.0
- [ ] Multi-language support (Tamil, Telugu, etc.)
- [ ] Legal document generation
- [ ] Court filing integration
- [ ] Legal research collaboration

---

**InLegalDesk** - Empowering legal professionals with AI-driven research and drafting capabilities.