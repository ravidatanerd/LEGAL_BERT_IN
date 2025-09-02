"""
InLegalDesk - Desktop GUI for Indian Legal Research
ChatGPT-style interface with drag-and-drop PDF ingestion
"""
import sys
import os
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QSplitter, QLabel, QComboBox,
    QScrollArea, QFrame, QFileDialog, QMessageBox, QProgressBar,
    QListWidget, QListWidgetItem, QTabWidget, QTextBrowser
)
from PySide6.QtCore import (
    Qt, QThread, QTimer, QMimeData, QUrl, Signal
)
from PySide6.QtGui import (
    QFont, QPixmap, QIcon, QDragEnterEvent, QDropEvent, 
    QTextCharFormat, QColor, QPalette
)
import markdown
from dotenv import load_dotenv

from api_client import LegalAPIClient
from server_launcher import ServerLauncher
from credential_manager import CredentialDialog, SecureCredentialManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatMessage(QFrame):
    """Individual chat message widget"""
    
    def __init__(self, content: str, is_user: bool = True, sources: List[Dict[str, Any]] = None):
        super().__init__()
        self.content = content
        self.is_user = is_user
        self.sources = sources or []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the message UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Message bubble
        bubble = QFrame()
        bubble_layout = QVBoxLayout(bubble)
        
        # Style based on sender
        if self.is_user:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #007acc;
                    border-radius: 18px;
                    padding: 12px;
                }
            """)
            layout.addWidget(bubble, 0, Qt.AlignRight)
        else:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #f1f1f1;
                    border-radius: 18px;
                    padding: 12px;
                    border: 1px solid #e0e0e0;
                }
            """)
            layout.addWidget(bubble, 0, Qt.AlignLeft)
        
        # Message content
        content_widget = QTextBrowser()
        content_widget.setOpenExternalLinks(True)
        content_widget.setFrameStyle(QFrame.NoFrame)
        content_widget.setStyleSheet("background: transparent; border: none;")
        
        # Convert markdown to HTML
        if not self.is_user:
            html_content = markdown.markdown(self.content, extensions=['codehilite', 'tables'])
            content_widget.setHtml(html_content)
        else:
            content_widget.setPlainText(self.content)
        
        # Set text color for user messages
        if self.is_user:
            content_widget.setStyleSheet("color: white; background: transparent; border: none;")
        
        bubble_layout.addWidget(content_widget)
        
        # Add sources if available
        if self.sources and not self.is_user:
            sources_widget = self._create_sources_widget()
            bubble_layout.addWidget(sources_widget)
    
    def _create_sources_widget(self) -> QWidget:
        """Create widget showing source citations"""
        sources_frame = QFrame()
        sources_layout = QVBoxLayout(sources_frame)
        
        sources_label = QLabel("Sources:")
        sources_label.setStyleSheet("font-weight: bold; color: #666;")
        sources_layout.addWidget(sources_label)
        
        for i, source in enumerate(self.sources[:3], 1):  # Show max 3 sources
            filename = source.get("filename", "Unknown")
            confidence = source.get("combined_score", 0)
            
            source_btn = QPushButton(f"[{i}] {filename} (Score: {confidence:.2f})")
            source_btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 5px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    background: white;
                }
                QPushButton:hover {
                    background: #f0f0f0;
                }
            """)
            source_btn.clicked.connect(lambda checked, src=source: self._show_source_detail(src))
            sources_layout.addWidget(source_btn)
        
        return sources_frame
    
    def _show_source_detail(self, source: Dict[str, Any]):
        """Show detailed source information"""
        detail_text = f"""
Filename: {source.get('filename', 'Unknown')}
Document ID: {source.get('doc_id', 'Unknown')}
Chunk: {source.get('chunk_index', 0)}
Dense Score: {source.get('dense_score', 0):.3f}
Sparse Score: {source.get('sparse_score', 0):.3f}
Combined Score: {source.get('combined_score', 0):.3f}

Text Preview:
{source.get('text', '')[:300]}...
        """
        
        msg = QMessageBox()
        msg.setWindowTitle("Source Details")
        msg.setText(detail_text)
        msg.exec()

class ChatWidget(QScrollArea):
    """Main chat interface widget"""
    
    def __init__(self):
        super().__init__()
        self.messages: List[ChatMessage] = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup chat UI"""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Main container
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setSpacing(10)
        self.layout.addStretch()  # Push messages to bottom initially
        
        self.setWidget(container)
        
        # Style
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
        """)
    
    def add_message(self, content: str, is_user: bool = True, sources: List[Dict[str, Any]] = None):
        """Add a new message to the chat"""
        message = ChatMessage(content, is_user, sources)
        self.messages.append(message)
        
        # Insert before the stretch
        self.layout.insertWidget(self.layout.count() - 1, message)
        
        # Scroll to bottom
        QTimer.singleShot(100, self._scroll_to_bottom)
    
    def _scroll_to_bottom(self):
        """Scroll to the bottom of the chat"""
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_chat(self):
        """Clear all messages"""
        for message in self.messages:
            message.deleteLater()
        self.messages.clear()

class StreamingWorker(QThread):
    """Worker thread for simulating streaming responses"""
    chunk_received = Signal(str)
    finished = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, full_response: str):
        super().__init__()
        self.full_response = full_response
    
    def run(self):
        """Simulate streaming by emitting chunks"""
        try:
            words = self.full_response.split()
            current_text = ""
            
            for word in words:
                current_text += word + " "
                self.chunk_received.emit(current_text.strip())
                self.msleep(50)  # 50ms delay between words
            
            self.finished.emit()
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class APIWorker(QThread):
    """Worker thread for API calls"""
    response_received = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, api_client: LegalAPIClient, endpoint: str, data: Dict[str, Any]):
        super().__init__()
        self.api_client = api_client
        self.endpoint = endpoint
        self.data = data
    
    def run(self):
        """Make API call in background"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if self.endpoint == "ask":
                result = loop.run_until_complete(
                    self.api_client.ask_question(
                        self.data["question"],
                        self.data.get("language", "auto"),
                        self.data.get("max_results", 5)
                    )
                )
            elif self.endpoint == "judgment":
                result = loop.run_until_complete(
                    self.api_client.generate_judgment(
                        self.data["case_facts"],
                        self.data["legal_issues"],
                        self.data.get("language", "auto")
                    )
                )
            elif self.endpoint == "upload":
                result = loop.run_until_complete(
                    self.api_client.upload_document(self.data["file_path"])
                )
            else:
                raise ValueError(f"Unknown endpoint: {self.endpoint}")
            
            self.response_received.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class InLegalDeskApp(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.api_client = LegalAPIClient()
        self.server_launcher = ServerLauncher()
        self.credential_manager = SecureCredentialManager()
        self.chat_history: List[Dict[str, Any]] = []
        
        self.setup_ui()
        self.setup_drag_drop()
        self.load_chat_history()
        
        # Check for credentials and prompt if needed
        self.check_credentials()
        
        # Auto-start server
        self.start_backend_server()
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("InLegalDesk - Indian Legal Research Assistant")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply modern styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #fafafa;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Chat history and controls
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Main chat area
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 1100])
    
    def _create_left_panel(self) -> QWidget:
        """Create left control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("InLegalDesk")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333; padding: 10px;")
        layout.addWidget(title)
        
        # Server controls
        server_group = QFrame()
        server_group.setFrameStyle(QFrame.Box)
        server_layout = QVBoxLayout(server_group)
        
        server_label = QLabel("Backend Server")
        server_label.setStyleSheet("font-weight: bold; color: #555;")
        server_layout.addWidget(server_label)
        
        self.server_status = QLabel("Status: Starting...")
        self.server_status.setStyleSheet("color: #666; font-size: 12px;")
        server_layout.addWidget(self.server_status)
        
        self.start_server_btn = QPushButton("Start Backend")
        self.start_server_btn.clicked.connect(self.start_backend_server)
        server_layout.addWidget(self.start_server_btn)
        
        layout.addWidget(server_group)
        
        # Language selection
        lang_group = QFrame()
        lang_group.setFrameStyle(QFrame.Box)
        lang_layout = QVBoxLayout(lang_group)
        
        lang_label = QLabel("Language")
        lang_label.setStyleSheet("font-weight: bold; color: #555;")
        lang_layout.addWidget(lang_label)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Auto", "English", "हिंदी"])
        self.language_combo.setCurrentText("Auto")
        lang_layout.addWidget(self.language_combo)
        
        layout.addWidget(lang_group)
        
        # Quick actions
        actions_group = QFrame()
        actions_group.setFrameStyle(QFrame.Box)
        actions_layout = QVBoxLayout(actions_group)
        
        actions_label = QLabel("Quick Actions")
        actions_label.setStyleSheet("font-weight: bold; color: #555;")
        actions_layout.addWidget(actions_label)
        
        self.ingest_statutes_btn = QPushButton("📚 Ingest Statutes")
        self.ingest_statutes_btn.clicked.connect(self.ingest_statutes)
        actions_layout.addWidget(self.ingest_statutes_btn)
        
        self.upload_pdf_btn = QPushButton("📄 Upload PDF")
        self.upload_pdf_btn.clicked.connect(self.upload_pdf)
        actions_layout.addWidget(self.upload_pdf_btn)
        
        self.export_chat_btn = QPushButton("💾 Export Chat")
        self.export_chat_btn.clicked.connect(self.export_chat)
        actions_layout.addWidget(self.export_chat_btn)
        
        self.credentials_btn = QPushButton("🔑 API Credentials")
        self.credentials_btn.clicked.connect(self.manage_credentials)
        actions_layout.addWidget(self.credentials_btn)
        
        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        actions_layout.addWidget(self.settings_btn)
        
        layout.addWidget(actions_group)
        
        # Chat history
        history_group = QFrame()
        history_group.setFrameStyle(QFrame.Box)
        history_layout = QVBoxLayout(history_group)
        
        history_label = QLabel("Recent Chats")
        history_label.setStyleSheet("font-weight: bold; color: #555;")
        history_layout.addWidget(history_label)
        
        self.chat_history_list = QListWidget()
        self.chat_history_list.itemClicked.connect(self.load_chat_session)
        history_layout.addWidget(self.chat_history_list)
        
        new_chat_btn = QPushButton("+ New Chat")
        new_chat_btn.clicked.connect(self.new_chat)
        history_layout.addWidget(new_chat_btn)
        
        layout.addWidget(history_group)
        
        # Status panel
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; font-size: 12px; padding: 5px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """Create main chat panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Chat area
        self.chat_widget = ChatWidget()
        layout.addWidget(self.chat_widget)
        
        # Input area
        input_frame = QFrame()
        input_frame.setFrameStyle(QFrame.Box)
        input_layout = QVBoxLayout(input_frame)
        
        # Input controls
        controls_layout = QHBoxLayout()
        
        # Mode selector
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Ask Question", 
            "Generate Judgment", 
            "Hybrid Analysis",
            "Legal Summary"
        ])
        controls_layout.addWidget(QLabel("Mode:"))
        controls_layout.addWidget(self.mode_combo)
        
        # AI Model indicator
        self.ai_mode_label = QLabel("🤖 Hybrid BERT+GPT")
        self.ai_mode_label.setStyleSheet("color: #007acc; font-weight: bold; font-size: 12px;")
        controls_layout.addWidget(self.ai_mode_label)
        
        controls_layout.addStretch()
        input_layout.addLayout(controls_layout)
        
        # Text input
        input_container = QHBoxLayout()
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Ask a legal question or describe case facts...")
        self.input_text.setMaximumHeight(100)
        self.input_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #007acc;
            }
        """)
        input_container.addWidget(self.input_text)
        
        # Send button
        self.send_btn = QPushButton("Send")
        self.send_btn.setMinimumSize(80, 40)
        self.send_btn.clicked.connect(self.send_message)
        input_container.addWidget(self.send_btn)
        
        input_layout.addLayout(input_container)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        input_layout.addWidget(self.progress_bar)
        
        layout.addWidget(input_frame)
        
        return panel
    
    def setup_drag_drop(self):
        """Setup drag and drop for PDF files"""
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.toLocalFile().lower().endswith('.pdf') for url in urls):
                event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event for PDF files"""
        urls = event.mimeData().urls()
        pdf_files = [url.toLocalFile() for url in urls if url.toLocalFile().lower().endswith('.pdf')]
        
        if pdf_files:
            for pdf_file in pdf_files:
                self.upload_pdf_file(pdf_file)
    
    def start_backend_server(self):
        """Start the backend server"""
        try:
            self.server_status.setText("Status: Starting...")
            self.start_server_btn.setEnabled(False)
            
            # Start server in background
            success = self.server_launcher.start_server()
            
            if success:
                self.server_status.setText("Status: Running")
                self.server_status.setStyleSheet("color: green; font-size: 12px;")
                
                # Test connection
                QTimer.singleShot(2000, self.test_backend_connection)
            else:
                self.server_status.setText("Status: Failed to start")
                self.server_status.setStyleSheet("color: red; font-size: 12px;")
                self.start_server_btn.setEnabled(True)
                
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            self.server_status.setText("Status: Error")
            self.start_server_btn.setEnabled(True)
    
    def test_backend_connection(self):
        """Test backend connection"""
        worker = APIWorker(self.api_client, "health", {})
        worker.response_received.connect(self.on_backend_connected)
        worker.error_occurred.connect(self.on_backend_error)
        worker.start()
    
    def on_backend_connected(self, response: Dict[str, Any]):
        """Handle successful backend connection"""
        self.server_status.setText("Status: Connected ✓")
        self.server_status.setStyleSheet("color: green; font-size: 12px;")
        self.status_label.setText("Backend ready")
    
    def on_backend_error(self, error: str):
        """Handle backend connection error"""
        self.server_status.setText("Status: Connection failed")
        self.server_status.setStyleSheet("color: red; font-size: 12px;")
        self.start_server_btn.setEnabled(True)
    
    def send_message(self):
        """Send message to backend"""
        text = self.input_text.toPlainText().strip()
        if not text:
            return
        
        # Add user message
        self.chat_widget.add_message(text, is_user=True)
        self.input_text.clear()
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.send_btn.setEnabled(False)
        
        # Get selected language
        lang_map = {"Auto": "auto", "English": "en", "हिंदी": "hi"}
        language = lang_map[self.language_combo.currentText()]
        
        # Determine mode and make API call
        mode = self.mode_combo.currentText()
        
        if mode == "Ask Question":
            data = {
                "question": text,
                "language": language,
                "max_results": 5
            }
            worker = APIWorker(self.api_client, "ask", data)
        elif mode == "Generate Judgment":
            data = {
                "case_facts": text,
                "legal_issues": [text],  # Simplified for demo
                "language": language
            }
            worker = APIWorker(self.api_client, "judgment", data)
        elif mode == "Hybrid Analysis":
            # Enhanced hybrid analysis mode
            data = {
                "question": f"Perform comprehensive hybrid BERT+GPT analysis: {text}",
                "language": language,
                "max_results": 8  # More sources for hybrid analysis
            }
            worker = APIWorker(self.api_client, "ask", data)
        else:  # Legal Summary
            data = {
                "question": f"Provide a structured legal summary: {text}",
                "language": language,
                "max_results": 5
            }
            worker = APIWorker(self.api_client, "ask", data)
        
        worker.response_received.connect(self.on_response_received)
        worker.error_occurred.connect(self.on_api_error)
        worker.start()
    
    def on_response_received(self, response: Dict[str, Any]):
        """Handle API response"""
        try:
            self.progress_bar.setVisible(False)
            self.send_btn.setEnabled(True)
            
            if "answer" in response:
                # Q&A response (potentially with hybrid analysis)
                content = response["answer"]
                sources = response.get("sources", [])
                
                # Check if this is a hybrid analysis response
                if "hybrid_analysis" in response:
                    hybrid_info = response["hybrid_analysis"]
                    content = self._enhance_response_with_hybrid_info(content, hybrid_info)
                
                # Add assistant message with streaming effect
                self.add_streaming_message(content, sources)
                
            elif "framing" in response:
                # Judgment response
                content = self._format_judgment_response(response)
                self.add_streaming_message(content, [])
            
            # Save to chat history
            self.save_current_chat()
            
        except Exception as e:
            logger.error(f"Failed to handle response: {e}")
            self.on_api_error(str(e))
    
    def on_api_error(self, error: str):
        """Handle API error"""
        self.progress_bar.setVisible(False)
        self.send_btn.setEnabled(True)
        
        error_msg = f"Error: {error}"
        self.chat_widget.add_message(error_msg, is_user=False)
        
        self.status_label.setText(f"Error: {error}")
    
    def add_streaming_message(self, content: str, sources: List[Dict[str, Any]]):
        """Add message with streaming effect"""
        # Add empty assistant message
        message = ChatMessage("", is_user=False, sources=sources)
        self.chat_widget.messages.append(message)
        self.chat_widget.layout.insertWidget(self.chat_widget.layout.count() - 1, message)
        
        # Start streaming worker
        self.streaming_worker = StreamingWorker(content)
        self.streaming_worker.chunk_received.connect(
            lambda text: self._update_streaming_message(message, text)
        )
        self.streaming_worker.finished.connect(
            lambda: self.chat_widget._scroll_to_bottom()
        )
        self.streaming_worker.start()
    
    def _update_streaming_message(self, message: ChatMessage, text: str):
        """Update streaming message content"""
        # Find the content widget and update it
        content_widget = message.findChild(QTextBrowser)
        if content_widget:
            html_content = markdown.markdown(text, extensions=['codehilite', 'tables'])
            content_widget.setHtml(html_content)
        
        self.chat_widget._scroll_to_bottom()
    
    def _format_judgment_response(self, judgment: Dict[str, Any]) -> str:
        """Format judgment response as markdown"""
        md_parts = [
            f"# Legal Judgment\n",
            f"## Case Framing\n{judgment.get('framing', 'N/A')}\n",
            f"## Points for Determination",
        ]
        
        for i, point in enumerate(judgment.get('points_for_determination', []), 1):
            md_parts.append(f"{i}. {point}")
        
        md_parts.extend([
            f"\n## Applicable Law",
            f"**Constitutional Provisions:** {', '.join(judgment.get('applicable_law', {}).get('constitutional', []))}",
            f"**Statutes:** {', '.join(judgment.get('applicable_law', {}).get('statutes', []))}",
            f"**Precedents:** {', '.join(judgment.get('applicable_law', {}).get('precedents', []))}",
            f"\n## Court Analysis"
        ])
        
        for analysis in judgment.get('court_analysis', []):
            md_parts.append(f"**Issue:** {analysis.get('issue', 'N/A')}")
            md_parts.append(f"**Analysis:** {analysis.get('analysis', 'N/A')}")
            md_parts.append("")
        
        md_parts.extend([
            f"## Final Order",
            judgment.get('relief', {}).get('final_order', 'N/A'),
            f"\n## Prediction",
            f"**Likely Outcome:** {judgment.get('prediction', {}).get('likely_outcome', 'N/A')}"
        ])
        
        return "\n".join(md_parts)
    
    def _enhance_response_with_hybrid_info(self, content: str, hybrid_info: Dict[str, Any]) -> str:
        """Enhance response content with hybrid analysis information"""
        
        enhanced_parts = [content]
        
        # Add hybrid analysis section
        if hybrid_info:
            enhanced_parts.append("\n\n---\n## 🤖 Hybrid BERT+GPT Analysis")
            
            # Add confidence metrics
            confidence = hybrid_info.get("confidence_score", 0)
            hybrid_score = hybrid_info.get("hybrid_score", 0)
            
            enhanced_parts.append(f"**Analysis Quality:**")
            enhanced_parts.append(f"- Contextual Understanding (BERT): {confidence:.2f}")
            enhanced_parts.append(f"- Hybrid Model Score: {hybrid_score:.2f}")
            
            # Add contextual understanding
            context = hybrid_info.get("contextual_understanding", {})
            if context:
                enhanced_parts.append(f"\n**Contextual Analysis:**")
                enhanced_parts.append(f"- Context Type: {context.get('context_type', 'Unknown').replace('_', ' ').title()}")
                enhanced_parts.append(f"- Legal Complexity: {context.get('complexity_score', 0):.2f}")
                
                legal_concepts = context.get("legal_concepts", [])
                if legal_concepts:
                    enhanced_parts.append(f"- Legal Concepts: {', '.join(legal_concepts[:5])}")
            
            # Add legal reasoning
            reasoning = hybrid_info.get("legal_reasoning", [])
            if reasoning:
                enhanced_parts.append(f"\n**Legal Reasoning Steps:**")
                for i, step in enumerate(reasoning[:3], 1):
                    enhanced_parts.append(f"{i}. {step}")
            
            # Add model information
            enhanced_parts.append(f"\n**AI Models Used:**")
            enhanced_parts.append(f"- 🧠 **InLegalBERT**: Contextual understanding of Indian legal text")
            enhanced_parts.append(f"- 🤖 **T5/XLNet**: Encoder-decoder and hybrid autoregressive generation")
            enhanced_parts.append(f"- 💬 **GPT**: Advanced natural language generation")
            enhanced_parts.append(f"- 🔗 **Hybrid Fusion**: Combined strengths for superior legal analysis")
        
        return "\n".join(enhanced_parts)
    
    def ingest_statutes(self):
        """Ingest Indian statutes"""
        self.status_label.setText("Ingesting statutes...")
        
        worker = APIWorker(self.api_client, "add_statutes", {})
        worker.response_received.connect(self.on_statutes_ingested)
        worker.error_occurred.connect(lambda e: self.status_label.setText(f"Statute ingestion failed: {e}"))
        worker.start()
    
    def on_statutes_ingested(self, response: Dict[str, Any]):
        """Handle statute ingestion completion"""
        self.status_label.setText("Statutes ingested successfully")
        
        # Show success message
        QMessageBox.information(
            self, 
            "Success", 
            "Indian statutes have been successfully ingested and are ready for search."
        )
    
    def upload_pdf(self):
        """Open file dialog to upload PDF"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select PDF Document", 
            "", 
            "PDF Files (*.pdf)"
        )
        
        if file_path:
            self.upload_pdf_file(file_path)
    
    def upload_pdf_file(self, file_path: str):
        """Upload a specific PDF file with security validation"""
        try:
            from security_validator import DesktopSecurityValidator
            
            # Validate file before upload
            validation = DesktopSecurityValidator.validate_file_for_upload(file_path)
            
            if not validation["is_valid"]:
                error_msg = "File validation failed:\n" + "\n".join(validation["errors"])
                QMessageBox.critical(self, "Upload Failed", error_msg)
                return
            
            # Show warnings if any
            if validation["warnings"]:
                warning_msg = "File validation warnings:\n" + "\n".join(validation["warnings"])
                warning_msg += "\n\nDo you want to continue with the upload?"
                
                reply = QMessageBox.question(
                    self, 
                    "Upload Warning", 
                    warning_msg,
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    return
            
            # Show file info
            file_info = validation["file_info"]
            self.status_label.setText(f"Uploading {file_info['name']} ({file_info['size_mb']} MB)...")
            
            worker = APIWorker(self.api_client, "upload", {"file_path": file_path})
            worker.response_received.connect(
                lambda r: self._on_upload_success(r, validation)
            )
            worker.error_occurred.connect(
                lambda e: self.status_label.setText(f"Upload failed: {e}")
            )
            worker.start()
            
        except Exception as e:
            logger.error(f"Upload validation failed: {e}")
            QMessageBox.critical(self, "Error", f"Upload validation failed: {e}")
    
    def _on_upload_success(self, response: Dict[str, Any], validation: Dict[str, Any]):
        """Handle successful upload"""
        filename = response.get('filename', 'Unknown')
        warnings = response.get('warnings', [])
        
        self.status_label.setText(f"✓ Uploaded: {filename}")
        
        # Show success message with any warnings
        msg = f"Document '{filename}' uploaded successfully!"
        
        if warnings:
            msg += f"\n\nWarnings:\n" + "\n".join(warnings)
        
        if validation.get("warnings"):
            msg += f"\n\nFile Warnings:\n" + "\n".join(validation["warnings"])
        
        QMessageBox.information(self, "Upload Successful", msg)
    
    def export_chat(self):
        """Export current chat to markdown"""
        if not self.chat_widget.messages:
            QMessageBox.information(self, "Info", "No chat to export")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Chat",
            f"legal_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            "Markdown Files (*.md)"
        )
        
        if file_path:
            self._export_chat_to_file(file_path)
    
    def _export_chat_to_file(self, file_path: str):
        """Export chat messages to markdown file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# Legal Research Chat Export\n\n")
                f.write(f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for i, message in enumerate(self.chat_widget.messages):
                    sender = "User" if message.is_user else "Assistant"
                    f.write(f"## {sender} (Message {i+1})\n\n")
                    f.write(f"{message.content}\n\n")
                    
                    if message.sources:
                        f.write("### Sources\n\n")
                        for j, source in enumerate(message.sources, 1):
                            f.write(f"{j}. {source.get('filename', 'Unknown')} (Score: {source.get('combined_score', 0):.3f})\n")
                        f.write("\n")
            
            self.status_label.setText(f"Chat exported to {Path(file_path).name}")
            
        except Exception as e:
            logger.error(f"Failed to export chat: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export chat: {e}")
    
    def new_chat(self):
        """Start a new chat session"""
        self.chat_widget.clear_chat()
        self.status_label.setText("New chat started")
    
    def load_chat_session(self, item: QListWidgetItem):
        """Load a previous chat session"""
        # Placeholder for chat history loading
        self.status_label.setText(f"Loading chat: {item.text()}")
    
    def load_chat_history(self):
        """Load chat history from file"""
        # Placeholder for loading chat history
        pass
    
    def save_current_chat(self):
        """Save current chat session"""
        # Placeholder for saving chat
        pass
    
    def check_credentials(self):
        """Check if credentials are configured and prompt if needed"""
        try:
            # Check if we have credentials in environment
            if not os.getenv('OPENAI_API_KEY'):
                # Check if we have stored credentials
                if not self.credential_manager.credentials_exist():
                    # Prompt for credentials on first run
                    QTimer.singleShot(2000, self.show_credentials_prompt)
                else:
                    # Try to load credentials
                    self.status_label.setText("Credentials found - configure to unlock full features")
            else:
                self.status_label.setText("API credentials configured")
                
        except Exception as e:
            logger.error(f"Failed to check credentials: {e}")
    
    def show_credentials_prompt(self):
        """Show prompt for first-time credential setup"""
        reply = QMessageBox.question(
            self,
            "API Credentials Setup",
            "Welcome to InLegalDesk!\n\n"
            "To unlock full AI features, you'll need to configure your OpenAI API credentials.\n\n"
            "Would you like to set up your credentials now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.manage_credentials()
    
    def manage_credentials(self):
        """Open credential management dialog"""
        try:
            dialog = CredentialDialog(self)
            dialog.credentials_updated.connect(self.on_credentials_updated)
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Failed to open credential dialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open credential manager: {e}")
    
    def on_credentials_updated(self, credentials: Dict[str, Any]):
        """Handle credential updates"""
        try:
            # Update environment variables
            for key, value in credentials.items():
                os.environ[key] = value
            
            # Update API client
            self.api_client.update_credentials(credentials)
            
            # Update status
            self.status_label.setText("✓ API credentials updated")
            
            # Show success message
            QMessageBox.information(
                self,
                "Success",
                "API credentials have been updated successfully!\n\n"
                "The application now has access to full AI features."
            )
            
        except Exception as e:
            logger.error(f"Failed to update credentials: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update credentials: {e}")
    
    def open_settings(self):
        """Open settings dialog"""
        try:
            from secure_settings import SecureSettingsDialog
            
            dialog = SecureSettingsDialog(self)
            dialog.settings_updated.connect(self.on_settings_updated)
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Failed to open settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open settings: {e}")
    
    def on_settings_updated(self, settings: Dict[str, Any]):
        """Handle settings updates"""
        try:
            # Apply settings to current session
            self.status_label.setText("✓ Settings updated")
            
            # Restart backend if needed
            if settings.get("backend_port") != int(os.getenv("BACKEND_PORT", 8877)):
                reply = QMessageBox.question(
                    self,
                    "Restart Required",
                    "Backend port changed. Restart the backend server?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.restart_backend()
            
        except Exception as e:
            logger.error(f"Failed to apply settings: {e}")
    
    def restart_backend(self):
        """Restart the backend server"""
        try:
            self.server_launcher.stop_server()
            self.server_status.setText("Status: Restarting...")
            QTimer.singleShot(2000, self.start_backend_server)
            
        except Exception as e:
            logger.error(f"Failed to restart backend: {e}")
            self.server_status.setText("Status: Restart failed")

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("InLegalDesk")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("InLegalDesk")
    
    # Load environment
    load_dotenv()
    
    # Create and show main window
    window = InLegalDeskApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()