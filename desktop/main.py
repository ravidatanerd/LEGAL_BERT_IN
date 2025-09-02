"""
InLegalDesk - ChatGPT-style Legal Research Desktop Application
"""

import sys
import os
import json
import asyncio
import threading
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import markdown
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QScrollArea, QFrame,
    QSplitter, QMenuBar, QMenu, QStatusBar, QProgressBar, QComboBox,
    QFileDialog, QMessageBox, QDialog, QDialogButtonBox, QFormLayout,
    QCheckBox, QGroupBox, QTabWidget, QListWidget, QListWidgetItem
)
from PySide6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve,
    QRect, QSize, QPoint, QMimeData
)
from PySide6.QtGui import (
    QFont, QPixmap, QIcon, QTextCursor, QTextCharFormat, QColor,
    QDragEnterEvent, QDropEvent, QAction, QKeySequence, QPalette
)

from api_client import LegalAPIClient
from server_launcher import ServerLauncher

class ChatMessage(QFrame):
    """Individual chat message widget"""
    
    def __init__(self, message: Dict[str, Any], is_user: bool = True):
        super().__init__()
        self.message = message
        self.is_user = is_user
        self.setup_ui()
    
    def setup_ui(self):
        """Setup message UI"""
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Message header
        header_layout = QHBoxLayout()
        
        # Avatar/icon
        avatar_label = QLabel()
        if self.is_user:
            avatar_label.setText("👤")
            self.setStyleSheet("""
                ChatMessage {
                    background-color: #007AFF;
                    border-radius: 10px;
                    color: white;
                }
            """)
        else:
            avatar_label.setText("⚖️")
            self.setStyleSheet("""
                ChatMessage {
                    background-color: #F2F2F7;
                    border-radius: 10px;
                    color: black;
                }
            """)
        
        avatar_label.setFixedSize(30, 30)
        avatar_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(avatar_label)
        
        # Timestamp
        timestamp = self.message.get('timestamp', '')
        timestamp_label = QLabel(timestamp)
        timestamp_label.setStyleSheet("font-size: 10px; color: #666;")
        header_layout.addStretch()
        header_layout.addWidget(timestamp_label)
        
        layout.addLayout(header_layout)
        
        # Message content
        content_label = QLabel()
        content_label.setWordWrap(True)
        content_label.setTextFormat(Qt.RichText)
        
        # Render markdown content
        content_html = self._render_markdown(self.message.get('content', ''))
        content_label.setText(content_html)
        
        layout.addWidget(content_label)
        
        # Citations
        citations = self.message.get('citations', [])
        if citations:
            citations_widget = self._create_citations_widget(citations)
            layout.addWidget(citations_widget)
        
        # Copy button for code blocks
        if '```' in self.message.get('content', ''):
            copy_button = QPushButton("📋 Copy Code")
            copy_button.clicked.connect(self._copy_code)
            copy_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.2);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 5px;
                    padding: 5px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.3);
                }
            """)
            layout.addWidget(copy_button)
        
        self.setLayout(layout)
    
    def _render_markdown(self, content: str) -> str:
        """Render markdown content to HTML"""
        try:
            # Convert markdown to HTML
            html = markdown.markdown(
                content,
                extensions=['codehilite', 'fenced_code', 'tables']
            )
            
            # Add custom styling
            styled_html = f"""
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                code {{ background-color: rgba(0, 0, 0, 0.1); padding: 2px 4px; border-radius: 3px; }}
                pre {{ background-color: rgba(0, 0, 0, 0.1); padding: 10px; border-radius: 5px; overflow-x: auto; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                a {{ color: #007AFF; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
            {html}
            """
            
            return styled_html
            
        except Exception as e:
            return f"<p>Error rendering markdown: {e}</p><p>{content}</p>"
    
    def _create_citations_widget(self, citations: List[Dict[str, Any]]) -> QWidget:
        """Create citations widget"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        citations_label = QLabel("📚 Sources:")
        citations_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(citations_label)
        
        for i, citation in enumerate(citations):
            citation_widget = QPushButton(f"[{i+1}] {citation.get('source', 'Unknown')}")
            citation_widget.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 5px;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                    background-color: rgba(255, 255, 255, 0.5);
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.8);
                }
            """)
            citation_widget.clicked.connect(lambda checked, c=citation: self._show_citation_details(c))
            layout.addWidget(citation_widget)
        
        widget.setLayout(layout)
        return widget
    
    def _show_citation_details(self, citation: Dict[str, Any]):
        """Show citation details in popup"""
        dialog = QDialog()
        dialog.setWindowTitle("Citation Details")
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        # Citation details
        details_text = f"""
        <h3>Citation Details</h3>
        <p><strong>Source:</strong> {citation.get('source', 'Unknown')}</p>
        <p><strong>Page:</strong> {citation.get('page', 'N/A')}</p>
        <p><strong>Section:</strong> {citation.get('section', 'N/A')}</p>
        <p><strong>Relevance Score:</strong> {citation.get('score', 'N/A')}</p>
        """
        
        details_label = QLabel(details_text)
        details_label.setWordWrap(True)
        layout.addWidget(details_label)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def _copy_code(self):
        """Copy code blocks to clipboard"""
        content = self.message.get('content', '')
        # Extract code blocks
        import re
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        if code_blocks:
            clipboard = QApplication.clipboard()
            clipboard.setText('\n\n'.join(code_blocks))

class ChatWidget(QWidget):
    """Main chat interface widget"""
    
    message_sent = pyqtSignal(str, str)  # message, language
    
    def __init__(self):
        super().__init__()
        self.chat_history = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup chat UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Chat messages area
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.messages_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout()
        self.messages_layout.setContentsMargins(10, 10, 10, 10)
        self.messages_layout.addStretch()
        self.messages_widget.setLayout(self.messages_layout)
        self.messages_scroll.setWidget(self.messages_widget)
        
        layout.addWidget(self.messages_scroll)
        
        # Input area
        input_frame = QFrame()
        input_frame.setFrameStyle(QFrame.StyledPanel)
        input_layout = QVBoxLayout()
        
        # Language selector
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Language:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Auto", "English", "Hindi"])
        self.language_combo.setCurrentText("Auto")
        lang_layout.addWidget(self.language_combo)
        lang_layout.addStretch()
        input_layout.addLayout(lang_layout)
        
        # Message input
        input_row = QHBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(100)
        self.message_input.setPlaceholderText("Ask a legal question or request a judgment...")
        self.message_input.installEventFilter(self)
        input_row.addWidget(self.message_input)
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.setFixedSize(80, 40)
        self.send_button.clicked.connect(self._send_message)
        input_row.addWidget(self.send_button)
        
        input_layout.addLayout(input_row)
        input_frame.setLayout(input_layout)
        layout.addWidget(input_frame)
        
        self.setLayout(layout)
    
    def eventFilter(self, obj, event):
        """Handle key events for message input"""
        if obj == self.message_input and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                self._send_message()
                return True
        return super().eventFilter(obj, event)
    
    def _send_message(self):
        """Send message"""
        message_text = self.message_input.toPlainText().strip()
        if not message_text:
            return
        
        # Add user message to chat
        self.add_message({
            'content': message_text,
            'timestamp': time.strftime("%H:%M"),
            'type': 'user'
        }, is_user=True)
        
        # Clear input
        self.message_input.clear()
        
        # Emit signal
        language = self.language_combo.currentText().lower()
        if language == "auto":
            language = "auto"
        elif language == "hindi":
            language = "hi"
        else:
            language = "en"
        
        self.message_sent.emit(message_text, language)
    
    def add_message(self, message: Dict[str, Any], is_user: bool = True):
        """Add message to chat"""
        chat_message = ChatMessage(message, is_user)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, chat_message)
        
        # Scroll to bottom
        QTimer.singleShot(100, self._scroll_to_bottom)
        
        # Store in history
        self.chat_history.append({
            'message': message,
            'is_user': is_user,
            'timestamp': time.time()
        })
    
    def _scroll_to_bottom(self):
        """Scroll chat to bottom"""
        scrollbar = self.messages_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_chat(self):
        """Clear chat history"""
        # Clear UI
        for i in reversed(range(self.messages_layout.count() - 1)):
            item = self.messages_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        # Clear history
        self.chat_history.clear()
    
    def export_chat(self, format: str = "markdown") -> str:
        """Export chat to specified format"""
        if format == "markdown":
            return self._export_markdown()
        elif format == "json":
            return json.dumps(self.chat_history, indent=2)
        else:
            return str(self.chat_history)
    
    def _export_markdown(self) -> str:
        """Export chat as markdown"""
        markdown_content = "# Legal Research Chat\n\n"
        
        for item in self.chat_history:
            message = item['message']
            is_user = item['is_user']
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item['timestamp']))
            
            if is_user:
                markdown_content += f"## User ({timestamp})\n\n{message['content']}\n\n"
            else:
                markdown_content += f"## Assistant ({timestamp})\n\n{message['content']}\n\n"
        
        return markdown_content

class AttachmentWidget(QWidget):
    """File attachment widget with drag and drop"""
    
    file_dropped = pyqtSignal(str)  # file path
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setAcceptDrops(True)
    
    def setup_ui(self):
        """Setup attachment UI"""
        layout = QVBoxLayout()
        
        # Drop area
        self.drop_area = QLabel("📎 Drag & Drop PDF files here\nor click to browse")
        self.drop_area.setAlignment(Qt.AlignCenter)
        self.drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 10px;
                padding: 20px;
                background-color: #f9f9f9;
                color: #666;
            }
            QLabel:hover {
                border-color: #007AFF;
                background-color: #f0f8ff;
            }
        """)
        self.drop_area.mousePressEvent = self._browse_files
        layout.addWidget(self.drop_area)
        
        # Attached files list
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(100)
        layout.addWidget(self.files_list)
        
        self.setLayout(layout)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        for file_path in files:
            if file_path.lower().endswith('.pdf'):
                self._add_file(file_path)
                self.file_dropped.emit(file_path)
    
    def _browse_files(self, event):
        """Browse for files"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF File", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self._add_file(file_path)
            self.file_dropped.emit(file_path)
    
    def _add_file(self, file_path: str):
        """Add file to list"""
        filename = os.path.basename(file_path)
        item = QListWidgetItem(f"📄 {filename}")
        item.setData(Qt.UserRole, file_path)
        self.files_list.addItem(item)
    
    def clear_files(self):
        """Clear attached files"""
        self.files_list.clear()

class StatusWidget(QWidget):
    """Status and log widget"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup status UI"""
        layout = QVBoxLayout()
        
        # Status indicators
        status_layout = QHBoxLayout()
        
        self.backend_status = QLabel("🔴 Backend: Disconnected")
        self.backend_status.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(self.backend_status)
        
        self.ingestion_status = QLabel("📄 Ingestion: Ready")
        status_layout.addWidget(self.ingestion_status)
        
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Log area
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(150)
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                font-family: monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.log_area)
        
        self.setLayout(layout)
    
    def update_backend_status(self, connected: bool):
        """Update backend connection status"""
        if connected:
            self.backend_status.setText("🟢 Backend: Connected")
            self.backend_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.backend_status.setText("🔴 Backend: Disconnected")
            self.backend_status.setStyleSheet("color: red; font-weight: bold;")
    
    def update_ingestion_status(self, status: str):
        """Update ingestion status"""
        self.ingestion_status.setText(f"📄 Ingestion: {status}")
    
    def show_progress(self, visible: bool):
        """Show/hide progress bar"""
        self.progress_bar.setVisible(visible)
    
    def update_progress(self, value: int):
        """Update progress bar value"""
        self.progress_bar.setValue(value)
    
    def add_log(self, message: str):
        """Add log message"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")
        
        # Auto-scroll to bottom
        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_area.setTextCursor(cursor)

class InLegalDeskMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.api_client = LegalAPIClient()
        self.server_launcher = ServerLauncher()
        self.setup_ui()
        self.setup_connections()
        self.check_backend_status()
    
    def setup_ui(self):
        """Setup main UI"""
        self.setWindowTitle("InLegalDesk - AI Legal Research Assistant")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set application icon (if available)
        # self.setWindowIcon(QIcon("icon.ico"))
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel (attachments and controls)
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel (chat)
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_left_panel(self) -> QWidget:
        """Create left control panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Controls group
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout()
        
        # Backend controls
        self.start_backend_btn = QPushButton("🚀 Start Backend")
        self.start_backend_btn.clicked.connect(self._start_backend)
        controls_layout.addWidget(self.start_backend_btn)
        
        self.ingest_statutes_btn = QPushButton("📚 Ingest Statutes")
        self.ingest_statutes_btn.clicked.connect(self._ingest_statutes)
        controls_layout.addWidget(self.ingest_statutes_btn)
        
        self.generate_judgment_btn = QPushButton("⚖️ Generate Judgment")
        self.generate_judgment_btn.clicked.connect(self._generate_judgment)
        controls_layout.addWidget(self.generate_judgment_btn)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Attachments
        attachments_group = QGroupBox("Attachments")
        attachments_layout = QVBoxLayout()
        
        self.attachment_widget = AttachmentWidget()
        self.attachment_widget.file_dropped.connect(self._handle_file_drop)
        attachments_layout.addWidget(self.attachment_widget)
        
        attachments_group.setLayout(attachments_layout)
        layout.addWidget(attachments_group)
        
        # Status widget
        self.status_widget = StatusWidget()
        layout.addWidget(self.status_widget)
        
        panel.setLayout(layout)
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """Create right chat panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Chat widget
        self.chat_widget = ChatWidget()
        layout.addWidget(self.chat_widget)
        
        panel.setLayout(layout)
        return panel
    
    def _create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        export_action = QAction("Export Chat", self)
        export_action.triggered.connect(self._export_chat)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        clear_chat_action = QAction("Clear Chat", self)
        clear_chat_action.triggered.connect(self._clear_chat)
        tools_menu.addAction(clear_chat_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def setup_connections(self):
        """Setup signal connections"""
        self.chat_widget.message_sent.connect(self._handle_message)
    
    def _start_backend(self):
        """Start backend server"""
        try:
            self.status_widget.add_log("Starting backend server...")
            self.server_launcher.start_server()
            QTimer.singleShot(2000, self.check_backend_status)
        except Exception as e:
            self.status_widget.add_log(f"Failed to start backend: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start backend: {e}")
    
    def _ingest_statutes(self):
        """Ingest legal statutes"""
        try:
            self.status_widget.add_log("Ingesting legal statutes...")
            self.status_widget.update_ingestion_status("Processing...")
            self.status_widget.show_progress(True)
            
            # This would be an async call in a real implementation
            # For now, simulate the process
            QTimer.singleShot(3000, self._statutes_ingested)
            
        except Exception as e:
            self.status_widget.add_log(f"Failed to ingest statutes: {e}")
            QMessageBox.critical(self, "Error", f"Failed to ingest statutes: {e}")
    
    def _statutes_ingested(self):
        """Handle statutes ingestion completion"""
        self.status_widget.update_ingestion_status("Completed")
        self.status_widget.show_progress(False)
        self.status_widget.add_log("Legal statutes ingested successfully")
    
    def _generate_judgment(self):
        """Generate legal judgment"""
        dialog = JudgmentDialog(self)
        if dialog.exec() == QDialog.Accepted:
            facts, issues = dialog.get_data()
            self._process_judgment_generation(facts, issues)
    
    def _process_judgment_generation(self, facts: str, issues: List[str]):
        """Process judgment generation"""
        try:
            self.status_widget.add_log("Generating legal judgment...")
            self.status_widget.show_progress(True)
            
            # This would be an async call in a real implementation
            # For now, simulate the process
            QTimer.singleShot(5000, lambda: self._judgment_generated(facts, issues))
            
        except Exception as e:
            self.status_widget.add_log(f"Failed to generate judgment: {e}")
            QMessageBox.critical(self, "Error", f"Failed to generate judgment: {e}")
    
    def _judgment_generated(self, facts: str, issues: List[str]):
        """Handle judgment generation completion"""
        self.status_widget.show_progress(False)
        self.status_widget.add_log("Legal judgment generated successfully")
        
        # Add generated judgment to chat
        judgment_text = f"""
# Generated Legal Judgment

## Case Facts
{facts}

## Legal Issues
{chr(10).join(f"- {issue}" for issue in issues)}

## Analysis
[Generated legal analysis would appear here]

## Holding
[Court's decision would appear here]

## Relief
[Relief granted would appear here]
        """
        
        self.chat_widget.add_message({
            'content': judgment_text,
            'timestamp': time.strftime("%H:%M"),
            'type': 'assistant'
        }, is_user=False)
    
    def _handle_file_drop(self, file_path: str):
        """Handle file drop"""
        try:
            self.status_widget.add_log(f"Processing file: {os.path.basename(file_path)}")
            self.status_widget.update_ingestion_status("Processing...")
            self.status_widget.show_progress(True)
            
            # This would be an async call in a real implementation
            # For now, simulate the process
            QTimer.singleShot(2000, lambda: self._file_processed(file_path))
            
        except Exception as e:
            self.status_widget.add_log(f"Failed to process file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to process file: {e}")
    
    def _file_processed(self, file_path: str):
        """Handle file processing completion"""
        self.status_widget.update_ingestion_status("Completed")
        self.status_widget.show_progress(False)
        self.status_widget.add_log(f"File processed: {os.path.basename(file_path)}")
    
    def _handle_message(self, message: str, language: str):
        """Handle chat message"""
        try:
            self.status_widget.add_log(f"Processing question: {message[:50]}...")
            
            # This would be an async call in a real implementation
            # For now, simulate the response
            QTimer.singleShot(2000, lambda: self._message_processed(message, language))
            
        except Exception as e:
            self.status_widget.add_log(f"Failed to process message: {e}")
            QMessageBox.critical(self, "Error", f"Failed to process message: {e}")
    
    def _message_processed(self, message: str, language: str):
        """Handle message processing completion"""
        # Simulate AI response
        response_text = f"""
Based on your question: "{message}"

Here's a comprehensive legal analysis:

## Legal Principles
[Relevant legal principles would be provided here]

## Precedents
[Relevant case law and precedents would be cited here]

## Analysis
[Detailed legal analysis would be provided here]

## Conclusion
[Conclusion and recommendations would be provided here]

*Note: This is a simulated response. In the full implementation, this would be generated by the AI system using the legal knowledge base.*
        """
        
        self.chat_widget.add_message({
            'content': response_text,
            'timestamp': time.strftime("%H:%M"),
            'type': 'assistant',
            'citations': [
                {'source': 'Sample Legal Document.pdf', 'page': '15', 'section': 'Section 420'},
                {'source': 'Case Law Database', 'page': '23', 'section': 'Precedent XYZ'}
            ]
        }, is_user=False)
        
        self.status_widget.add_log("Response generated successfully")
    
    def check_backend_status(self):
        """Check backend connection status"""
        try:
            # This would be an actual API call in a real implementation
            # For now, simulate the check
            connected = self.api_client.is_connected()
            self.status_widget.update_backend_status(connected)
        except Exception as e:
            self.status_widget.update_backend_status(False)
            self.status_widget.add_log(f"Backend check failed: {e}")
    
    def _export_chat(self):
        """Export chat to file"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Chat", "legal_research_chat.md", "Markdown Files (*.md);;All Files (*)"
            )
            if file_path:
                content = self.chat_widget.export_chat("markdown")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.status_widget.add_log(f"Chat exported to: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export chat: {e}")
    
    def _clear_chat(self):
        """Clear chat history"""
        reply = QMessageBox.question(
            self, "Clear Chat", "Are you sure you want to clear the chat history?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.chat_widget.clear_chat()
            self.status_widget.add_log("Chat history cleared")
    
    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About InLegalDesk",
            """
            <h3>InLegalDesk v1.0</h3>
            <p>AI-powered Legal Research and Judgment Drafting System</p>
            <p>Built with PySide6 and FastAPI</p>
            <p>Features:</p>
            <ul>
                <li>ChatGPT-style legal research interface</li>
                <li>Document ingestion with vision-language models</li>
                <li>InLegalBERT embeddings for legal text</li>
                <li>Automated judgment generation</li>
                <li>Multi-language support (English/Hindi)</li>
            </ul>
            """
        )

class JudgmentDialog(QDialog):
    """Dialog for judgment generation input"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Legal Judgment")
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout()
        
        # Form layout
        form_layout = QFormLayout()
        
        # Case facts
        self.facts_input = QTextEdit()
        self.facts_input.setPlaceholderText("Enter the case facts...")
        self.facts_input.setMaximumHeight(100)
        form_layout.addRow("Case Facts:", self.facts_input)
        
        # Legal issues
        self.issues_input = QTextEdit()
        self.issues_input.setPlaceholderText("Enter legal issues (one per line)...")
        self.issues_input.setMaximumHeight(100)
        form_layout.addRow("Legal Issues:", self.issues_input)
        
        # Court type
        self.court_combo = QComboBox()
        self.court_combo.addItems(["High Court", "Supreme Court", "District Court"])
        form_layout.addRow("Court Type:", self.court_combo)
        
        # Language
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Auto", "English", "Hindi"])
        form_layout.addRow("Language:", self.language_combo)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_data(self):
        """Get dialog data"""
        facts = self.facts_input.toPlainText().strip()
        issues_text = self.issues_input.toPlainText().strip()
        issues = [issue.strip() for issue in issues_text.split('\n') if issue.strip()]
        
        return facts, issues

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("InLegalDesk")
    app.setApplicationVersion("1.0.0")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = InLegalDeskMainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()