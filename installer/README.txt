InLegal Desktop - Indian Legal Research Assistant
=================================================

Version: 1.0.0
Publisher: InLegal

DESCRIPTION
-----------
InLegal Desktop is a comprehensive legal research and judgment drafting tool 
specifically designed for Indian law. It combines advanced AI technology with 
legal expertise to provide accurate, efficient, and bilingual legal research 
capabilities.

FEATURES
--------
• Document Ingestion: OCR-free PDF processing with vision-language models
• Semantic Search: InLegalBERT embeddings for accurate legal document retrieval
• AI-Powered Q&A: Intelligent legal research with citation support
• Judgment Generation: Structured judgment drafting with legal frameworks
• Bilingual Support: English and Hindi language support
• Statute Integration: Access to Indian Penal Code, CrPC, Evidence Act
• Modern Interface: ChatGPT-style user experience

SYSTEM REQUIREMENTS
-------------------
• Windows 10/11 (64-bit)
• 8GB RAM minimum (16GB recommended)
• 2GB free disk space
• Internet connection for AI features

INSTALLATION
------------
1. Run the installer as Administrator
2. Follow the installation wizard
3. Choose installation directory (default: Program Files)
4. Select optional shortcuts (Desktop, Start Menu)
5. Complete installation

FIRST RUN
---------
1. Launch InLegal Desktop from Start Menu or Desktop
2. The application will start the backend server automatically
3. Click "Ingest Statutes" to download Indian legal statutes
4. Upload your legal documents or start asking questions

CONFIGURATION
-------------
• Environment settings: Edit .env.sample in installation directory
• API Keys: Add your OpenAI API key for AI features
• Model Settings: Configure vision-language model preferences

USAGE
-----
• Upload Documents: Drag and drop PDF files or use Upload button
• Ask Questions: Type legal questions in the chat interface
• Generate Judgments: Use the judgment generation feature for case analysis
• Export Results: Save chat transcripts and generated content

SUPPORT
-------
• Documentation: Check the application help menu
• Issues: Report problems through the application interface
• Updates: Check for updates in the application

LICENSE
-------
This software is provided under the terms specified in LICENSE.txt

TECHNICAL DETAILS
-----------------
• Backend: FastAPI with Python
• Frontend: PySide6 (Qt6)
• AI Models: InLegalBERT, OpenAI GPT-4
• Document Processing: Donut, Pix2Struct, Tesseract
• Search: FAISS + BM25 hybrid retrieval

For technical support or feature requests, please contact the development team.