"""
InLegal Desktop Application - ChatGPT-style interface for Indian legal research
"""

import sys
import os
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import tempfile
import markdown
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QScrollArea, QFrame,
    QSplitter, QTabWidget, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QProgressBar, QComboBox, QTextBrowser, QMenuBar,
    QMenu, QStatusBar, QToolBar, QAction, QDialog, QDialogButtonBox,
    QFormLayout, QSpinBox, QCheckBox, QGroupBox, QGridLayout
)
from PySide6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QPropertyAnimation,
    QEasingCurve, QRect, QPoint, QMimeData, QUrl
)
from PySide6.QtGui import (
    QFont, QPixmap, QIcon, QTextCursor, QTextCharFormat, QColor,
    QPalette, QAction, QDragEnterEvent, QDropEvent, QPainter,
    QTextDocument, QTextBlockFormat, QTextListFormat
)

from api_client import APIClient
from server_launcher import ServerLauncher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatMessage(QFrame):
    """Individual chat message widget"""
    
    def __init__(self, content: str, is_user: bool = True, citations: List[Dict] = None):
        super().__init__()
        self.is_user = is_user
        self.citations = citations or []
        self.setup_ui(content)
    
    def setup_ui(self, content: str):
        """Setup the message UI"""
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Message content
        self.content_widget = QTextBrowser()
        self.content_widget.setMaximumHeight(400)
        self.content_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.content_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Style based on user/assistant
        if self.is_user:
            self.setStyleSheet("""
                QFrame {
                    background-color: #007AFF;
                    border-radius: 10px;
                    margin: 5px;
                }
            """)
            self.content_widget.setStyleSheet("""
                QTextBrowser {
                    background-color: transparent;
                    color: white;
                    border: none;
                    font-size: 14px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #F2F2F7;
                    border-radius: 10px;
                    margin: 5px;
                }
            """)
            self.content_widget.setStyleSheet("""
                QTextBrowser {
                    background-color: transparent;
                    color: black;
                    border: none;
                    font-size: 14px;
                }
            """)
        
        # Render markdown content
        html_content = self.render_markdown(content)
        self.content_widget.setHtml(html_content)
        
        layout.addWidget(self.content_widget)
        
        # Citations
        if self.citations and not self.is_user:
            citations_widget = self.create_citations_widget()
            layout.addWidget(citations_widget)
        
        self.setLayout(layout)
    
    def render_markdown(self, content: str) -> str:
        """Render markdown content to HTML"""
        try:
            # Convert markdown to HTML
            html = markdown.markdown(
                content,
                extensions=['codehilite', 'fenced_code', 'tables']
            )
            
            # Add custom CSS for better styling
            styled_html = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        line-height: 1.6;
                        margin: 0;
                        padding: 0;
                    }}
                    code {{
                        background-color: rgba(0,0,0,0.1);
                        padding: 2px 4px;
                        border-radius: 3px;
                        font-family: 'Monaco', 'Menlo', monospace;
                    }}
                    pre {{
                        background-color: rgba(0,0,0,0.05);
                        padding: 10px;
                        border-radius: 5px;
                        overflow-x: auto;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 10px 0;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f2f2f2;
                    }}
                    a {{
                        color: #007AFF;
                        text-decoration: none;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                </style>
            </head>
            <body>
                {html}
            </body>
            </html>
            """
            return styled_html
        except Exception as e:
            logger.error(f"Error rendering markdown: {e}")
            return f"<p>{content}</p>"
    
    def create_citations_widget(self) -> QWidget:
        """Create citations widget"""
        citations_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 5, 0, 0)
        
        citations_label = QLabel("Sources:")
        citations_label.setStyleSheet("font-weight: bold; color: #666;")
        layout.addWidget(citations_label)
        
        for i, citation in enumerate(self.citations[:5]):  # Show max 5 citations
            citation_text = f"[{i+1}] {citation.get('text', '')[:100]}..."
            citation_label = QLabel(citation_text)
            citation_label.setWordWrap(True)
            citation_label.setStyleSheet("color: #666; font-size: 12px;")
            layout.addWidget(citation_label)
        
        citations_widget.setLayout(layout)
        return citations_widget

class ChatWidget(QWidget):
    """Main chat interface widget"""
    
    def __init__(self):
        super().__init__()
        self.messages: List[ChatMessage] = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the chat UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Messages area
        self.messages_area = QScrollArea()
        self.messages_area.setWidgetResizable(True)
        self.messages_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.messages_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout()
        self.messages_layout.setContentsMargins(10, 10, 10, 10)
        self.messages_layout.setSpacing(10)
        self.messages_widget.setLayout(self.messages_layout)
        
        self.messages_area.setWidget(self.messages_widget)
        layout.addWidget(self.messages_area)
        
        # Input area
        input_widget = self.create_input_widget()
        layout.addWidget(input_widget)
        
        self.setLayout(layout)
    
    def create_input_widget(self) -> QWidget:
        """Create input widget"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Language selector
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Language:"))
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Auto", "English", "Hindi"])
        self.language_combo.setCurrentText("Auto")
        lang_layout.addWidget(self.language_combo)
        
        lang_layout.addStretch()
        layout.addLayout(lang_layout)
        
        # Input field
        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(100)
        self.input_field.setPlaceholderText("Ask a legal question...")
        self.input_field.setStyleSheet("""
            QTextEdit {
                border: 2px solid #E5E5EA;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #007AFF;
            }
        """)
        layout.addWidget(self.input_field)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ask_button = QPushButton("Ask Question")
        self.ask_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        button_layout.addWidget(self.ask_button)
        
        self.generate_judgment_button = QPushButton("Generate Judgment")
        self.generate_judgment_button.setStyleSheet("""
            QPushButton {
                background-color: #34C759;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #28A745;
            }
            QPushButton:pressed {
                background-color: #1E7E34;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        button_layout.addWidget(self.generate_judgment_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        widget.setLayout(layout)
        return widget
    
    def add_message(self, content: str, is_user: bool = True, citations: List[Dict] = None):
        """Add a message to the chat"""
        message = ChatMessage(content, is_user, citations)
        self.messages.append(message)
        self.messages_layout.addWidget(message)
        
        # Scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        """Scroll to the bottom of the messages"""
        scrollbar = self.messages_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_messages(self):
        """Clear all messages"""
        for message in self.messages:
            message.deleteLater()
        self.messages.clear()
    
    def get_input_text(self) -> str:
        """Get input text"""
        return self.input_field.toPlainText().strip()
    
    def clear_input(self):
        """Clear input field"""
        self.input_field.clear()
    
    def set_input_text(self, text: str):
        """Set input text"""
        self.input_field.setPlainText(text)

class DocumentWidget(QWidget):
    """Document management widget"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup document UI"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Documents"))
        
        self.upload_button = QPushButton("Upload PDF")
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
        """)
        header_layout.addWidget(self.upload_button)
        
        self.ingest_statutes_button = QPushButton("Ingest Statutes")
        self.ingest_statutes_button.setStyleSheet("""
            QPushButton {
                background-color: #34C759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #28A745;
            }
        """)
        header_layout.addWidget(self.ingest_statutes_button)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Documents list
        self.documents_list = QListWidget()
        self.documents_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E5E5EA;
                border-radius: 6px;
                background-color: white;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #F2F2F7;
            }
            QListWidget::item:selected {
                background-color: #E3F2FD;
            }
        """)
        layout.addWidget(self.documents_list)
        
        self.setLayout(layout)
    
    def add_document(self, doc_id: str, filename: str, status: str = "ingested"):
        """Add document to list"""
        item_text = f"{filename} ({status})"
        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, doc_id)
        self.documents_list.addItem(item)
    
    def clear_documents(self):
        """Clear documents list"""
        self.documents_list.clear()
    
    def get_selected_document_id(self) -> Optional[str]:
        """Get selected document ID"""
        current_item = self.documents_list.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None

class StatusWidget(QWidget):
    """Status and logs widget"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup status UI"""
        layout = QVBoxLayout()
        
        # Status indicators
        status_group = QGroupBox("System Status")
        status_layout = QGridLayout()
        
        self.backend_status = QLabel("Backend: Unknown")
        self.backend_status.setStyleSheet("color: orange; font-weight: bold;")
        status_layout.addWidget(self.backend_status, 0, 0)
        
        self.sources_status = QLabel("Sources: Unknown")
        self.sources_status.setStyleSheet("color: orange; font-weight: bold;")
        status_layout.addWidget(self.sources_status, 0, 1)
        
        self.documents_count = QLabel("Documents: 0")
        status_layout.addWidget(self.documents_count, 1, 0)
        
        self.embedding_model = QLabel("Model: InLegalBERT")
        status_layout.addWidget(self.embedding_model, 1, 1)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Logs
        logs_group = QGroupBox("Logs")
        logs_layout = QVBoxLayout()
        
        self.logs_text = QTextEdit()
        self.logs_text.setMaximumHeight(150)
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet("""
            QTextEdit {
                background-color: #F8F8F8;
                border: 1px solid #E5E5EA;
                border-radius: 6px;
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 12px;
            }
        """)
        logs_layout.addWidget(self.logs_text)
        
        logs_group.setLayout(logs_layout)
        layout.addWidget(logs_group)
        
        self.setLayout(layout)
    
    def update_backend_status(self, status: str, healthy: bool = True):
        """Update backend status"""
        color = "green" if healthy else "red"
        self.backend_status.setText(f"Backend: {status}")
        self.backend_status.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def update_sources_status(self, status: str):
        """Update sources status"""
        self.sources_status.setText(f"Sources: {status}")
    
    def update_documents_count(self, count: int):
        """Update documents count"""
        self.documents_count.setText(f"Documents: {count}")
    
    def add_log(self, message: str):
        """Add log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.logs_text.append(log_message)
        
        # Scroll to bottom
        cursor = self.logs_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.logs_text.setTextCursor(cursor)
    
    def clear_logs(self):
        """Clear logs"""
        self.logs_text.clear()

class InLegalMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.api_client = None
        self.server_launcher = ServerLauncher()
        self.setup_ui()
        self.setup_connections()
        self.start_backend()
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("InLegal - Indian Legal Research Assistant")
        self.setMinimumSize(1200, 800)
        
        # Set application icon (if available)
        # self.setWindowIcon(QIcon("icon.ico"))
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel (documents and status)
        left_panel = QWidget()
        left_panel.setMaximumWidth(300)
        left_layout = QVBoxLayout()
        
        # Documents widget
        self.documents_widget = DocumentWidget()
        left_layout.addWidget(self.documents_widget)
        
        # Status widget
        self.status_widget = StatusWidget()
        left_layout.addWidget(self.status_widget)
        
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)
        
        # Right panel (chat)
        self.chat_widget = ChatWidget()
        splitter.addWidget(self.chat_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create toolbar
        self.create_toolbar()
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        upload_action = QAction("Upload Document", self)
        upload_action.triggered.connect(self.upload_document)
        file_menu.addAction(upload_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Export Chat", self)
        export_action.triggered.connect(self.export_chat)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        ingest_statutes_action = QAction("Ingest Statutes", self)
        ingest_statutes_action.triggered.connect(self.ingest_statutes)
        tools_menu.addAction(ingest_statutes_action)
        
        sync_sources_action = QAction("Sync Sources", self)
        sync_sources_action.triggered.connect(self.sync_sources)
        tools_menu.addAction(sync_sources_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Create toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Backend control
        self.start_backend_action = QAction("Start Backend", self)
        self.start_backend_action.triggered.connect(self.start_backend)
        toolbar.addAction(self.start_backend_action)
        
        self.stop_backend_action = QAction("Stop Backend", self)
        self.stop_backend_action.triggered.connect(self.stop_backend)
        toolbar.addAction(self.stop_backend_action)
        
        toolbar.addSeparator()
        
        # Clear chat
        clear_chat_action = QAction("Clear Chat", self)
        clear_chat_action.triggered.connect(self.clear_chat)
        toolbar.addAction(clear_chat_action)
    
    def setup_connections(self):
        """Setup signal connections"""
        # Chat widget connections
        self.chat_widget.ask_button.clicked.connect(self.ask_question)
        self.chat_widget.generate_judgment_button.clicked.connect(self.generate_judgment)
        
        # Document widget connections
        self.documents_widget.upload_button.clicked.connect(self.upload_document)
        self.documents_widget.ingest_statutes_button.clicked.connect(self.ingest_statutes)
        
        # Enter key for input
        self.chat_widget.input_field.returnPressed.connect(self.ask_question)
    
    def start_backend(self):
        """Start the backend server"""
        try:
            if self.server_launcher.start_server():
                self.status_widget.add_log("Backend server started")
                self.status_widget.update_backend_status("Running", True)
                self.status_bar.showMessage("Backend running")
                
                # Start API client
                asyncio.create_task(self.initialize_api_client())
            else:
                self.status_widget.add_log("Failed to start backend server")
                self.status_widget.update_backend_status("Failed", False)
                self.status_bar.showMessage("Backend failed to start")
        except Exception as e:
            self.status_widget.add_log(f"Error starting backend: {e}")
            self.status_widget.update_backend_status("Error", False)
    
    def stop_backend(self):
        """Stop the backend server"""
        try:
            self.server_launcher.stop_server()
            self.status_widget.add_log("Backend server stopped")
            self.status_widget.update_backend_status("Stopped", False)
            self.status_bar.showMessage("Backend stopped")
        except Exception as e:
            self.status_widget.add_log(f"Error stopping backend: {e}")
    
    async def initialize_api_client(self):
        """Initialize API client"""
        try:
            self.api_client = APIClient()
            await self.api_client.__aenter__()
            
            # Check health
            health = await self.api_client.health_check()
            if health.get("status") == "healthy":
                self.status_widget.add_log("API client connected")
                await self.update_system_status()
            else:
                self.status_widget.add_log("API client connection failed")
        except Exception as e:
            self.status_widget.add_log(f"API client error: {e}")
    
    async def update_system_status(self):
        """Update system status"""
        try:
            if not self.api_client:
                return
            
            # Get sources status
            sources_status = await self.api_client.get_sources_status()
            if "error" not in sources_status:
                total_docs = sources_status.get("total_documents", 0)
                self.status_widget.update_documents_count(total_docs)
                self.status_widget.update_sources_status("Available")
            else:
                self.status_widget.update_sources_status("Error")
            
            # List documents
            documents = await self.api_client.list_documents()
            if "error" not in documents:
                self.documents_widget.clear_documents()
                for doc in documents.get("documents", []):
                    self.documents_widget.add_document(
                        doc["document_id"],
                        doc.get("filename", "Unknown"),
                        "ingested"
                    )
            
        except Exception as e:
            self.status_widget.add_log(f"Error updating status: {e}")
    
    def ask_question(self):
        """Ask a question"""
        question = self.chat_widget.get_input_text()
        if not question:
            return
        
        # Add user message
        self.chat_widget.add_message(question, is_user=True)
        self.chat_widget.clear_input()
        
        # Disable button
        self.chat_widget.ask_button.setEnabled(False)
        self.status_bar.showMessage("Processing question...")
        
        # Process question asynchronously
        asyncio.create_task(self.process_question(question))
    
    async def process_question(self, question: str):
        """Process question asynchronously"""
        try:
            if not self.api_client:
                self.chat_widget.add_message("Backend not available. Please start the backend first.", is_user=False)
                return
            
            # Get language
            language_map = {"Auto": "auto", "English": "en", "Hindi": "hi"}
            language = language_map.get(self.chat_widget.language_combo.currentText(), "auto")
            
            # Ask question
            response = await self.api_client.ask_question(question, language)
            
            if "error" in response:
                self.chat_widget.add_message(f"Error: {response['error']}", is_user=False)
            else:
                answer = response.get("answer", "No answer provided")
                citations = response.get("citations", [])
                self.chat_widget.add_message(answer, is_user=False, citations=citations)
            
            self.status_widget.add_log(f"Question processed: {question[:50]}...")
            
        except Exception as e:
            self.chat_widget.add_message(f"Error processing question: {e}", is_user=False)
            self.status_widget.add_log(f"Question error: {e}")
        finally:
            # Re-enable button
            self.chat_widget.ask_button.setEnabled(True)
            self.status_bar.showMessage("Ready")
    
    def generate_judgment(self):
        """Generate judgment dialog"""
        dialog = JudgmentDialog(self)
        if dialog.exec() == QDialog.Accepted:
            case_facts, issues = dialog.get_data()
            asyncio.create_task(self.process_judgment(case_facts, issues))
    
    async def process_judgment(self, case_facts: str, issues: List[str]):
        """Process judgment generation"""
        try:
            if not self.api_client:
                self.chat_widget.add_message("Backend not available. Please start the backend first.", is_user=False)
                return
            
            # Disable button
            self.chat_widget.generate_judgment_button.setEnabled(False)
            self.status_bar.showMessage("Generating judgment...")
            
            # Get language
            language_map = {"Auto": "auto", "English": "en", "Hindi": "hi"}
            language = language_map.get(self.chat_widget.language_combo.currentText(), "auto")
            
            # Generate judgment
            response = await self.api_client.generate_judgment(case_facts, issues, language)
            
            if "error" in response:
                self.chat_widget.add_message(f"Error: {response['error']}", is_user=False)
            else:
                judgment = response.get("judgment", {})
                judgment_text = self.format_judgment(judgment)
                self.chat_widget.add_message(judgment_text, is_user=False)
            
            self.status_widget.add_log("Judgment generated")
            
        except Exception as e:
            self.chat_widget.add_message(f"Error generating judgment: {e}", is_user=False)
            self.status_widget.add_log(f"Judgment error: {e}")
        finally:
            # Re-enable button
            self.chat_widget.generate_judgment_button.setEnabled(True)
            self.status_bar.showMessage("Ready")
    
    def format_judgment(self, judgment: Dict[str, Any]) -> str:
        """Format judgment for display"""
        try:
            formatted = "# Judgment\n\n"
            
            # Metadata
            metadata = judgment.get("metadata", {})
            if metadata:
                formatted += f"**Case:** {metadata.get('case_title', 'N/A')}\n"
                formatted += f"**Court:** {metadata.get('court', 'N/A')}\n"
                formatted += f"**Date:** {metadata.get('date', 'N/A')}\n"
                formatted += f"**Case Number:** {metadata.get('case_number', 'N/A')}\n\n"
            
            # Framing
            framing = judgment.get("framing", "")
            if framing:
                formatted += f"## Case Framing\n{framing}\n\n"
            
            # Points for determination
            points = judgment.get("points_for_determination", [])
            if points:
                formatted += "## Points for Determination\n"
                for point in points:
                    formatted += f"- {point}\n"
                formatted += "\n"
            
            # Arguments
            arguments = judgment.get("arguments", {})
            if arguments:
                formatted += "## Arguments\n"
                if arguments.get("petitioner"):
                    formatted += f"**Petitioner:** {arguments['petitioner']}\n\n"
                if arguments.get("respondent"):
                    formatted += f"**Respondent:** {arguments['respondent']}\n\n"
            
            # Court analysis
            analysis = judgment.get("court_analysis", [])
            if analysis:
                formatted += "## Court Analysis\n"
                for item in analysis:
                    formatted += f"### {item.get('issue', 'Issue')}\n"
                    formatted += f"{item.get('analysis', '')}\n\n"
            
            # Findings
            findings = judgment.get("findings", [])
            if findings:
                formatted += "## Findings\n"
                for finding in findings:
                    formatted += f"- {finding}\n"
                formatted += "\n"
            
            # Relief
            relief = judgment.get("relief", {})
            if relief:
                formatted += "## Relief\n"
                if relief.get("final_order"):
                    formatted += f"**Final Order:** {relief['final_order']}\n\n"
                if relief.get("directions"):
                    formatted += "**Directions:**\n"
                    for direction in relief["directions"]:
                        formatted += f"- {direction}\n"
                    formatted += "\n"
                if relief.get("costs"):
                    formatted += f"**Costs:** {relief['costs']}\n\n"
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting judgment: {e}")
            return f"Error formatting judgment: {e}"
    
    def upload_document(self):
        """Upload document dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select PDF Document",
            "",
            "PDF Files (*.pdf)"
        )
        
        if file_path:
            asyncio.create_task(self.process_upload(file_path))
    
    async def process_upload(self, file_path: str):
        """Process document upload"""
        try:
            if not self.api_client:
                self.status_widget.add_log("Backend not available for upload")
                return
            
            self.status_bar.showMessage("Uploading document...")
            
            # Upload document
            response = await self.api_client.upload_document(Path(file_path))
            
            if "error" in response:
                self.status_widget.add_log(f"Upload error: {response['error']}")
                QMessageBox.warning(self, "Upload Error", f"Failed to upload document: {response['error']}")
            else:
                doc_id = response.get("document_id")
                filename = response.get("filename")
                self.status_widget.add_log(f"Document uploaded: {filename}")
                
                # Update documents list
                await self.update_system_status()
                
                QMessageBox.information(self, "Upload Success", f"Document {filename} uploaded successfully!")
            
        except Exception as e:
            self.status_widget.add_log(f"Upload error: {e}")
            QMessageBox.critical(self, "Upload Error", f"Error uploading document: {e}")
        finally:
            self.status_bar.showMessage("Ready")
    
    def ingest_statutes(self):
        """Ingest Indian statutes"""
        asyncio.create_task(self.process_ingest_statutes())
    
    async def process_ingest_statutes(self):
        """Process statute ingestion"""
        try:
            if not self.api_client:
                self.status_widget.add_log("Backend not available for statute ingestion")
                return
            
            self.status_bar.showMessage("Ingesting statutes...")
            
            # Ingest statutes
            response = await self.api_client.add_statutes()
            
            if "error" in response:
                self.status_widget.add_log(f"Statute ingestion error: {response['error']}")
                QMessageBox.warning(self, "Ingestion Error", f"Failed to ingest statutes: {response['error']}")
            else:
                self.status_widget.add_log("Statutes ingestion started")
                QMessageBox.information(self, "Ingestion Started", "Statute ingestion has been started in the background.")
                
                # Update status after a delay
                await asyncio.sleep(2)
                await self.update_system_status()
            
        except Exception as e:
            self.status_widget.add_log(f"Statute ingestion error: {e}")
            QMessageBox.critical(self, "Ingestion Error", f"Error ingesting statutes: {e}")
        finally:
            self.status_bar.showMessage("Ready")
    
    def sync_sources(self):
        """Sync all sources"""
        asyncio.create_task(self.process_sync_sources())
    
    async def process_sync_sources(self):
        """Process source synchronization"""
        try:
            if not self.api_client:
                self.status_widget.add_log("Backend not available for source sync")
                return
            
            self.status_bar.showMessage("Syncing sources...")
            
            # Sync sources
            response = await self.api_client.sync_sources()
            
            if "error" in response:
                self.status_widget.add_log(f"Source sync error: {response['error']}")
                QMessageBox.warning(self, "Sync Error", f"Failed to sync sources: {response['error']}")
            else:
                self.status_widget.add_log("Source sync started")
                QMessageBox.information(self, "Sync Started", "Source synchronization has been started in the background.")
            
        except Exception as e:
            self.status_widget.add_log(f"Source sync error: {e}")
            QMessageBox.critical(self, "Sync Error", f"Error syncing sources: {e}")
        finally:
            self.status_bar.showMessage("Ready")
    
    def clear_chat(self):
        """Clear chat messages"""
        self.chat_widget.clear_messages()
        self.status_widget.add_log("Chat cleared")
    
    def export_chat(self):
        """Export chat to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Chat",
            f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            "Markdown Files (*.md);;Text Files (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("# Chat Export\n\n")
                    f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    for message in self.chat_widget.messages:
                        role = "User" if message.is_user else "Assistant"
                        f.write(f"## {role}\n\n")
                        f.write(f"{message.content_widget.toPlainText()}\n\n")
                        f.write("---\n\n")
                
                self.status_widget.add_log(f"Chat exported to {file_path}")
                QMessageBox.information(self, "Export Success", f"Chat exported to {file_path}")
                
            except Exception as e:
                self.status_widget.add_log(f"Export error: {e}")
                QMessageBox.critical(self, "Export Error", f"Error exporting chat: {e}")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About InLegal",
            """
            <h3>InLegal - Indian Legal Research Assistant</h3>
            <p>Version 1.0.0</p>
            <p>A comprehensive legal research and judgment drafting tool for Indian law.</p>
            <p><b>Features:</b></p>
            <ul>
            <li>Document ingestion with OCR-free extraction</li>
            <li>InLegalBERT embeddings for semantic search</li>
            <li>AI-powered legal research and Q&A</li>
            <li>Structured judgment generation</li>
            <li>Bilingual support (English/Hindi)</li>
            </ul>
            <p><b>Powered by:</b> FastAPI, PySide6, InLegalBERT, OpenAI</p>
            """
        )
    
    def closeEvent(self, event):
        """Handle application close"""
        try:
            # Stop backend
            self.stop_backend()
            
            # Close API client
            if self.api_client:
                asyncio.create_task(self.api_client.__aexit__(None, None, None))
            
            event.accept()
        except Exception as e:
            logger.error(f"Error during close: {e}")
            event.accept()

class JudgmentDialog(QDialog):
    """Dialog for judgment generation input"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Judgment")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout()
        
        # Case facts
        facts_label = QLabel("Case Facts:")
        layout.addWidget(facts_label)
        
        self.facts_text = QTextEdit()
        self.facts_text.setPlaceholderText("Enter the facts of the case...")
        self.facts_text.setMaximumHeight(150)
        layout.addWidget(self.facts_text)
        
        # Issues
        issues_label = QLabel("Issues for Determination:")
        layout.addWidget(issues_label)
        
        self.issues_text = QTextEdit()
        self.issues_text.setPlaceholderText("Enter each issue on a new line...")
        self.issues_text.setMaximumHeight(100)
        layout.addWidget(self.issues_text)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_data(self):
        """Get dialog data"""
        facts = self.facts_text.toPlainText().strip()
        issues_text = self.issues_text.toPlainText().strip()
        issues = [issue.strip() for issue in issues_text.split('\n') if issue.strip()]
        return facts, issues

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("InLegal")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("InLegal")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = InLegalMainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()