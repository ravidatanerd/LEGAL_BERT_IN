# InLegalDesk Desktop Application

Modern ChatGPT-style desktop interface for Indian legal research, built with PySide6.

## Features

### 💬 **ChatGPT-Style Interface**
- **Message Bubbles**: Distinct user/assistant message styling
- **Markdown Rendering**: Rich text with tables, code blocks, formatting
- **Streaming Simulation**: Token-by-token response animation
- **Multi-turn Conversations**: Persistent chat history
- **Copy Functionality**: Copy code blocks and responses

### 📁 **Document Management**
- **Drag & Drop**: Drop PDF files directly into the app
- **Upload Dialog**: Traditional file selection
- **Progress Tracking**: Visual upload progress
- **Document Status**: View ingested documents

### 🔍 **Legal Research**
- **Ask Questions**: Natural language legal queries
- **Generate Judgments**: Structured legal judgment drafting
- **Cite Sources**: Clickable citation references [1], [2]
- **Source Details**: View document metadata and scores

### 🌐 **Language Support**
- **Bilingual**: English and Hindi (Devanagari)
- **Auto-Detection**: Automatic language detection
- **Mixed Script**: Handle mixed Hindi/English queries

### 🔧 **Backend Integration**
- **Auto-Start**: Automatically launches backend server
- **Health Monitoring**: Real-time server status
- **Error Handling**: Graceful error display
- **Offline Mode**: Fallback when backend unavailable

## Installation

### Prerequisites

- **Windows 10/11** (64-bit)
- **No Python Required** (for installer version)

### Option 1: Windows Installer (Recommended)

1. Download `InLegalDesk_Installer.exe`
2. Run installer as Administrator
3. Follow installation wizard
4. Launch from Start Menu or Desktop

### Option 2: Development Setup

1. **Install Python 3.8+**
2. **Clone Repository**:
   ```bash
   git clone <repository-url>
   cd inlegaldesk/desktop
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Copy Backend**:
   ```bash
   cp -r ../backend server/
   ```
5. **Run Application**:
   ```bash
   python main.py
   ```

## Usage

### First Launch

1. **Start Application** - The app will auto-start the backend server
2. **Wait for Initialization** - InLegalBERT model downloads (~500MB)
3. **Ingest Statutes** - Click "📚 Ingest Statutes" to download Indian laws
4. **Start Chatting** - Ask legal questions in the chat interface

### Basic Operations

#### Asking Questions

1. Type your legal question in the input box
2. Select language (Auto/English/हिंदी)
3. Click "Send" or press Enter
4. View response with citations
5. Click citation numbers [1], [2] to see source details

#### Uploading Documents

**Method 1: Drag & Drop**
- Drag PDF files from Windows Explorer
- Drop them anywhere in the app window
- Wait for processing completion

**Method 2: Upload Button**
- Click "📄 Upload PDF"
- Select PDF file(s)
- Wait for processing completion

#### Generating Judgments

1. Change mode to "Generate Judgment"
2. Enter case facts and legal issues
3. Click "Send"
4. Review structured judgment output

### Advanced Features

#### Exporting Chats

1. Click "💾 Export Chat"
2. Choose location and filename
3. Saves as Markdown (.md) file
4. Includes all messages and source references

#### Managing Chats

- **New Chat**: Click "+ New Chat" to start fresh
- **Chat History**: View recent conversations (planned feature)
- **Auto-Save**: Chats saved automatically

## Configuration

### Environment File

Create `.env` file in the desktop directory:

```bash
# OpenAI Configuration (required for full functionality)
OPENAI_API_KEY=your_actual_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Backend Configuration
BACKEND_PORT=8877
# BACKEND_URL=http://127.0.0.1:8877  # Use external backend

# VLM Configuration
VLM_ORDER=donut,pix2struct,openai,tesseract_fallback
ENABLE_OCR_FALLBACK=true

# Language Configuration
TESSERACT_LANG=hin+eng
```

### External Backend

To use an external backend server:

```bash
# In .env file
BACKEND_URL=http://your-server:8877
```

The app will connect to the external server instead of starting a local one.

## Troubleshooting

### Common Issues

#### "Backend Failed to Start"

**Cause**: Missing dependencies or port conflicts

**Solutions**:
1. Check if port 8877 is available
2. Install missing Python packages
3. Check firewall settings
4. Try different port in `.env`

#### "Model Download Failed"

**Cause**: Internet connectivity or disk space

**Solutions**:
1. Check internet connection
2. Ensure 2GB+ free disk space
3. Restart application
4. Check antivirus software

#### "No Response to Questions"

**Cause**: Missing OpenAI API key or backend issues

**Solutions**:
1. Add valid OpenAI API key to `.env`
2. Check backend server status
3. Try simpler questions first
4. Check server logs

#### "PDF Upload Failed"

**Cause**: Unsupported file format or processing errors

**Solutions**:
1. Ensure file is a valid PDF
2. Try smaller PDF files first
3. Check file permissions
4. Restart application

### Debug Mode

Enable detailed logging:

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or in .env file
LOG_LEVEL=DEBUG
```

### Log Files

Check these locations for logs:
- **Application Logs**: Console output
- **Backend Logs**: `server/server.log` (if created)
- **Crash Logs**: Windows Event Viewer

## Development

### Building from Source

1. **Setup Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Copy Backend**:
   ```bash
   cp -r ../backend server/
   ```

4. **Run Development Server**:
   ```bash
   python main.py
   ```

### Creating Installer

See `../installer/README.md` for detailed build instructions.

## User Interface Guide

### Main Window Layout

```
┌─────────────────────────────────────────────────────────────┐
│ InLegalDesk                                                 │
├─────────────┬───────────────────────────────────────────────┤
│ Left Panel  │ Chat Area                                     │
│             │                                               │
│ • Server    │ ┌─────────────────────────────────────────┐   │
│   Status    │ │ User: What is Section 302 IPC?         │   │
│ • Language  │ └─────────────────────────────────────────┘   │
│   Selector  │                                               │
│ • Quick     │ ┌─────────────────────────────────────────┐   │
│   Actions   │ │ Assistant: Section 302 of the Indian   │   │
│ • Chat      │ │ Penal Code deals with murder... [1]     │   │
│   History   │ │                                         │   │
│             │ │ Sources: [1] IPC_1860.pdf              │   │
│             │ └─────────────────────────────────────────┘   │
│             │                                               │
│             │ ┌─────────────────────────────────────────┐   │
│             │ │ [Ask Question ▼] [Auto ▼]              │   │
│             │ │ ┌─────────────────────────────────────┐ │   │
│             │ │ │ Type your legal question...         │ │   │
│             │ │ └─────────────────────────────────────┘ │   │
│             │ │                               [Send]   │   │
│             │ └─────────────────────────────────────────┘   │
└─────────────┴───────────────────────────────────────────────┘
```

### Keyboard Shortcuts

- **Enter**: Send message (in input box)
- **Ctrl+N**: New chat
- **Ctrl+S**: Export chat
- **Ctrl+O**: Upload PDF
- **Ctrl+Q**: Quit application

### Message Types

- **User Messages**: Blue bubbles on the right
- **Assistant Messages**: Gray bubbles on the left with sources
- **System Messages**: Centered status updates
- **Error Messages**: Red-tinted error notifications

## Technical Details

### Dependencies

- **PySide6**: Qt-based GUI framework
- **httpx**: Async HTTP client for API calls
- **markdown**: Markdown to HTML conversion
- **python-dotenv**: Environment variable management

### Threading

- **Main Thread**: GUI updates and user interaction
- **API Worker**: Background API calls to prevent UI freezing
- **Streaming Worker**: Simulates token streaming for better UX
- **Server Launcher**: Manages backend server process

### Data Storage

- **Chat History**: JSON files in user data directory
- **Settings**: Registry (Windows) or config files
- **Temporary Files**: System temp directory
- **Backend Data**: `server/data/` directory

## Support

### Getting Help

1. **Check Status Panel**: Shows backend connection status
2. **Review Error Messages**: Detailed error information
3. **Check Logs**: Console output for debugging
4. **Restart Application**: Often resolves temporary issues

### Reporting Issues

When reporting issues, include:
- Windows version
- Error messages from the app
- Steps to reproduce
- PDF file characteristics (if relevant)
- Backend server logs

### Performance Tips

- **Close Unused Chats**: Reduces memory usage
- **Restart Periodically**: Clears accumulated data
- **Monitor Disk Space**: Models and documents need storage
- **Update Regularly**: Get latest improvements

## License

MIT License - See LICENSE file for details.