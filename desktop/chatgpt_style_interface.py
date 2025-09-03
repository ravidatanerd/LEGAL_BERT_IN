#!/usr/bin/env python3
"""
ChatGPT-Style Interface for InLegalDesk
Includes file upload, drag & drop, and premium fallback system
"""
import sys
import os
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTextEdit, QLineEdit, QPushButton, QSplitter, QLabel, QComboBox,
        QScrollArea, QFrame, QFileDialog, QMessageBox, QProgressBar,
        QListWidget, QListWidgetItem, QTabWidget, QTextBrowser,
        QToolBar, QMenuBar, QMenu, QAction, QStatusBar, QGroupBox,
        QGridLayout, QCheckBox, QSpinBox, QSlider
    )
    from PySide6.QtCore import Qt, QThread, QTimer, Signal, QMimeData, QUrl
    from PySide6.QtGui import (
        QFont, QPixmap, QIcon, QDragEnterEvent, QDropEvent, 
        QTextCharFormat, QColor, QPalette, QAction as QGuiAction
    )
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    print("❌ PySide6 not available - desktop GUI cannot run")
    print("💡 Use web interface instead: http://localhost:8877")

import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PremiumFallbackSystem:
    """Handles premium to free ChatGPT model fallback"""
    
    def __init__(self):
        self.current_model = "gpt-4"  # Start with premium
        self.fallback_models = [
            "gpt-4",
            "gpt-4-turbo-preview", 
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]
        self.rate_limit_count = 0
        self.last_rate_limit = None
        
    def get_next_model(self):
        """Get next model in fallback chain"""
        try:
            current_index = self.fallback_models.index(self.current_model)
            if current_index < len(self.fallback_models) - 1:
                self.current_model = self.fallback_models[current_index + 1]
                logger.info(f"Falling back to model: {self.current_model}")
                return self.current_model
            else:
                logger.warning("No more fallback models available")
                return self.current_model
        except ValueError:
            return self.fallback_models[0]
    
    def handle_rate_limit(self):
        """Handle rate limit by falling back to next model"""
        self.rate_limit_count += 1
        self.last_rate_limit = datetime.now()
        
        if self.rate_limit_count <= len(self.fallback_models):
            next_model = self.get_next_model()
            return {
                "status": "fallback",
                "message": f"Rate limit hit. Switching to {next_model}",
                "new_model": next_model
            }
        else:
            return {
                "status": "exhausted",
                "message": "All models rate limited. Please wait or add credits.",
                "suggestion": "Use offline mode or wait 1 hour"
            }

class ChatGPTStyleMessage(QFrame):
    """ChatGPT-style message bubble with file attachments"""
    
    def __init__(self, content: str, is_user: bool = True, attachments: List[Dict] = None):
        super().__init__()
        self.content = content
        self.is_user = is_user
        self.attachments = attachments or []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup ChatGPT-style message UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Message container
        message_container = QHBoxLayout()
        
        if self.is_user:
            message_container.addStretch()  # Push to right
        
        # Message bubble
        bubble = QFrame()
        bubble.setMaximumWidth(600)
        bubble_layout = QVBoxLayout(bubble)
        
        # Style bubble
        if self.is_user:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #007acc;
                    border-radius: 15px;
                    padding: 5px;
                }
            """)
        else:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #f1f1f1;
                    border-radius: 15px;
                    padding: 5px;
                    border: 1px solid #e0e0e0;
                }
            """)
        
        # Show attachments first (if any)
        if self.attachments:
            attachments_widget = self._create_attachments_widget()
            bubble_layout.addWidget(attachments_widget)
        
        # Message content
        content_widget = QTextBrowser()
        content_widget.setHtml(self.content)
        content_widget.setStyleSheet("background: transparent; border: none;")
        content_widget.setMaximumHeight(400)
        
        if self.is_user:
            content_widget.setStyleSheet("color: white; background: transparent; border: none;")
        
        bubble_layout.addWidget(content_widget)
        
        message_container.addWidget(bubble)
        
        if not self.is_user:
            message_container.addStretch()  # Push to left
        
        layout.addLayout(message_container)
    
    def _create_attachments_widget(self):
        """Create widget showing file attachments"""
        attachments_frame = QFrame()
        attachments_layout = QVBoxLayout(attachments_frame)
        
        for attachment in self.attachments:
            att_widget = QFrame()
            att_layout = QHBoxLayout(att_widget)
            
            # File type icon
            file_type = attachment.get("type", "file")
            icon_text = {
                "pdf": "📄",
                "image": "🖼️",
                "text": "📝",
                "folder": "📁"
            }.get(file_type, "📎")
            
            icon_label = QLabel(icon_text)
            att_layout.addWidget(icon_label)
            
            # File info
            filename = attachment.get("name", "Unknown file")
            size = attachment.get("size", "")
            
            info_label = QLabel(f"{filename} {size}")
            info_label.setStyleSheet("font-size: 12px; color: #666;")
            att_layout.addWidget(info_label)
            
            att_layout.addStretch()
            attachments_layout.addWidget(att_widget)
        
        return attachments_frame

class ChatGPTStyleInterface(QMainWindow):
    """Main ChatGPT-style interface with file upload capabilities"""
    
    def __init__(self):
        super().__init__()
        self.messages = []
        self.attachments = []
        self.fallback_system = PremiumFallbackSystem()
        
        self.setup_ui()
        self.setup_drag_drop()
        
        # Add welcome message
        self.add_message(
            "👋 Welcome to InLegalDesk! I'm your AI legal research assistant.\n\n" +
            "You can:\n" +
            "• Ask legal questions\n" +
            "• Upload PDF documents\n" +
            "• Drag & drop files\n" +
            "• Get AI-powered legal analysis\n\n" +
            "Try asking: 'What is Section 302 IPC?' or upload a legal document!",
            is_user=False
        )
    
    def setup_ui(self):
        """Setup ChatGPT-style UI"""
        self.setWindowTitle("InLegalDesk - AI Legal Research")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Header with model indicator
        header_layout = QHBoxLayout()
        
        title_label = QLabel("InLegalDesk")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.model_label = QLabel("Model: GPT-4 (Premium)")
        self.model_label.setStyleSheet("color: #007acc; font-weight: bold;")
        header_layout.addWidget(self.model_label)
        
        main_layout.addLayout(header_layout)
        
        # Chat area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.addStretch()
        
        self.chat_scroll.setWidget(self.chat_widget)
        main_layout.addWidget(self.chat_scroll)
        
        # Input area with ChatGPT-style features
        input_frame = QFrame()
        input_frame.setFrameStyle(QFrame.Box)
        input_layout = QVBoxLayout(input_frame)
        
        # Attachment area
        self.attachment_area = QFrame()
        self.attachment_layout = QHBoxLayout(self.attachment_area)
        self.attachment_area.setVisible(False)
        input_layout.addWidget(self.attachment_area)
        
        # Input controls
        controls_layout = QHBoxLayout()
        
        # File upload button
        self.upload_btn = QPushButton("📎 Attach")
        self.upload_btn.clicked.connect(self.show_upload_menu)
        controls_layout.addWidget(self.upload_btn)
        
        # Mode selector
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Legal Question", 
            "Document Analysis", 
            "Generate Judgment",
            "Legal Summary"
        ])
        controls_layout.addWidget(self.mode_combo)
        
        controls_layout.addStretch()
        
        # Clear attachments button
        self.clear_attachments_btn = QPushButton("Clear Attachments")
        self.clear_attachments_btn.clicked.connect(self.clear_attachments)
        self.clear_attachments_btn.setVisible(False)
        controls_layout.addWidget(self.clear_attachments_btn)
        
        input_layout.addLayout(controls_layout)
        
        # Text input with send button
        input_container = QHBoxLayout()
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Message InLegalDesk... (or drag files here)")
        self.input_text.setMaximumHeight(100)
        self.input_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                background-color: white;
            }
            QTextEdit:focus {
                border-color: #007acc;
            }
        """)
        input_container.addWidget(self.input_text)
        
        # Send button
        self.send_btn = QPushButton("Send")
        self.send_btn.setMinimumSize(80, 50)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005fa3;
            }
            QPushButton:pressed {
                background-color: #004a82;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        input_container.addWidget(self.send_btn)
        
        input_layout.addLayout(input_container)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        input_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(input_frame)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready - Backend: Checking connection...")
        self.setStatusBar(self.status_bar)
        
        # Test backend connection
        QTimer.singleShot(1000, self.test_backend_connection)
    
    def setup_drag_drop(self):
        """Setup drag and drop for files"""
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event for files"""
        urls = event.mimeData().urls()
        files = [url.toLocalFile() for url in urls]
        
        for file_path in files:
            self.add_attachment(file_path)
    
    def show_upload_menu(self):
        """Show ChatGPT-style upload menu"""
        menu = QMenu(self)
        
        # File upload options
        upload_file_action = menu.addAction("📄 Upload File")
        upload_file_action.triggered.connect(self.upload_file)
        
        upload_folder_action = menu.addAction("📁 Upload Folder")
        upload_folder_action.triggered.connect(self.upload_folder)
        
        upload_image_action = menu.addAction("🖼️ Upload Image")
        upload_image_action.triggered.connect(self.upload_image)
        
        menu.addSeparator()
        
        upload_pdf_action = menu.addAction("📋 Upload PDF Document")
        upload_pdf_action.triggered.connect(self.upload_pdf)
        
        # Show menu
        menu.exec(self.upload_btn.mapToGlobal(self.upload_btn.rect().bottomLeft()))
    
    def upload_file(self):
        """Upload any file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Upload File", "", "All Files (*.*)"
        )
        if file_path:
            self.add_attachment(file_path)
    
    def upload_folder(self):
        """Upload folder"""
        folder_path = QFileDialog.getExistingDirectory(self, "Upload Folder")
        if folder_path:
            self.add_attachment(folder_path, is_folder=True)
    
    def upload_image(self):
        """Upload image file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Upload Image", "", "Images (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if file_path:
            self.add_attachment(file_path, file_type="image")
    
    def upload_pdf(self):
        """Upload PDF document"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Upload PDF Document", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.add_attachment(file_path, file_type="pdf")
    
    def add_attachment(self, file_path: str, is_folder: bool = False, file_type: str = "file"):
        """Add file attachment to current message"""
        try:
            path_obj = Path(file_path)
            
            if is_folder:
                attachment = {
                    "name": path_obj.name,
                    "path": file_path,
                    "type": "folder",
                    "size": f"({len(list(path_obj.iterdir()))} items)"
                }
            else:
                size = path_obj.stat().st_size
                size_str = self.format_file_size(size)
                
                attachment = {
                    "name": path_obj.name,
                    "path": file_path,
                    "type": file_type,
                    "size": size_str
                }
            
            self.attachments.append(attachment)
            self.update_attachment_display()
            
            logger.info(f"Added attachment: {path_obj.name}")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to add attachment: {e}")
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"({size_bytes:.1f} {unit})"
            size_bytes /= 1024
        return f"({size_bytes:.1f} TB)"
    
    def update_attachment_display(self):
        """Update attachment display area"""
        # Clear existing attachments display
        for i in reversed(range(self.attachment_layout.count())):
            self.attachment_layout.itemAt(i).widget().setParent(None)
        
        if not self.attachments:
            self.attachment_area.setVisible(False)
            self.clear_attachments_btn.setVisible(False)
            return
        
        self.attachment_area.setVisible(True)
        self.clear_attachments_btn.setVisible(True)
        
        for attachment in self.attachments:
            att_widget = QFrame()
            att_widget.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
            
            att_layout = QHBoxLayout(att_widget)
            
            # File type icon
            icon_text = {
                "pdf": "📄",
                "image": "🖼️",
                "text": "📝",
                "folder": "📁"
            }.get(attachment["type"], "📎")
            
            icon_label = QLabel(icon_text)
            att_layout.addWidget(icon_label)
            
            # File info
            info_label = QLabel(f"{attachment['name']} {attachment['size']}")
            info_label.setStyleSheet("font-size: 12px;")
            att_layout.addWidget(info_label)
            
            # Remove button
            remove_btn = QPushButton("×")
            remove_btn.setMaximumSize(20, 20)
            remove_btn.setStyleSheet("color: red; font-weight: bold;")
            remove_btn.clicked.connect(lambda checked, att=attachment: self.remove_attachment(att))
            att_layout.addWidget(remove_btn)
            
            self.attachment_layout.addWidget(att_widget)
    
    def remove_attachment(self, attachment: Dict):
        """Remove an attachment"""
        if attachment in self.attachments:
            self.attachments.remove(attachment)
            self.update_attachment_display()
    
    def clear_attachments(self):
        """Clear all attachments"""
        self.attachments.clear()
        self.update_attachment_display()
    
    def add_message(self, content: str, is_user: bool = True, attachments: List[Dict] = None):
        """Add message to chat"""
        message = ChatGPTStyleMessage(content, is_user, attachments)
        
        # Insert before stretch
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, message)
        
        # Scroll to bottom
        QTimer.singleShot(100, self._scroll_to_bottom)
    
    def _scroll_to_bottom(self):
        """Scroll chat to bottom"""
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def test_backend_connection(self):
        """Test backend connection"""
        try:
            response = requests.get("http://localhost:8877/health", timeout=5)
            if response.status_code == 200:
                self.status_bar.showMessage("✅ Backend: Connected")
                self.status_bar.setStyleSheet("color: green;")
            else:
                self.status_bar.showMessage("❌ Backend: Connection failed")
                self.status_bar.setStyleSheet("color: red;")
        except Exception as e:
            self.status_bar.showMessage("❌ Backend: Not running - Click to start")
            self.status_bar.setStyleSheet("color: red;")
            self.status_bar.mousePressEvent = self.start_backend
    
    def start_backend(self, event=None):
        """Start backend server"""
        try:
            import subprocess
            backend_dir = Path.cwd().parent / "backend"
            
            if (backend_dir / "app_fixed.py").exists():
                subprocess.Popen([sys.executable, "app_fixed.py"], cwd=backend_dir)
                self.status_bar.showMessage("🚀 Backend: Starting...")
                QTimer.singleShot(3000, self.test_backend_connection)
            else:
                QMessageBox.warning(self, "Error", "Backend files not found!")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start backend: {e}")
    
    def send_message(self):
        """Send message with error handling"""
        try:
            text = self.input_text.toPlainText().strip()
            if not text and not self.attachments:
                return
            
            # Add user message
            user_attachments = self.attachments.copy() if self.attachments else None
            self.add_message(text, is_user=True, attachments=user_attachments)
            
            # Clear input
            self.input_text.clear()
            current_attachments = self.attachments.copy()
            self.clear_attachments()
            
            # Show progress
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate
            
            # Send to backend with error handling
            self.send_to_backend(text, current_attachments)
            
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            QMessageBox.critical(self, "Error", f"Failed to send message: {e}")
            self.progress_bar.setVisible(False)
    
    def send_to_backend(self, text: str, attachments: List[Dict]):
        """Send message to backend with rate limit handling"""
        try:
            # Prepare request
            payload = {
                "question": text,
                "language": "auto",
                "attachments": attachments
            }
            
            # Add model preference
            payload["preferred_model"] = self.fallback_system.current_model
            
            # Send request
            response = requests.post(
                "http://localhost:8877/ask",
                json=payload,
                timeout=30
            )
            
            self.progress_bar.setVisible(False)
            
            if response.status_code == 200:
                data = response.json()
                self.add_message(data.get("answer", "No response"), is_user=False)
                
            elif response.status_code == 429:  # Rate limit
                self.handle_rate_limit_response()
                
            else:
                error_msg = f"Backend error: {response.status_code}"
                self.add_message(f"❌ {error_msg}", is_user=False)
                
        except requests.exceptions.ConnectionError:
            self.progress_bar.setVisible(False)
            self.add_message("❌ Backend not running. Please start the backend server first.", is_user=False)
            
        except requests.exceptions.Timeout:
            self.progress_bar.setVisible(False)
            self.add_message("⏰ Request timed out. Please try again.", is_user=False)
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            logger.error(f"Error sending to backend: {e}")
            self.add_message(f"❌ Error: {str(e)}", is_user=False)
    
    def handle_rate_limit_response(self):
        """Handle rate limit by falling back to next model"""
        fallback_result = self.fallback_system.handle_rate_limit()
        
        if fallback_result["status"] == "fallback":
            # Update model display
            self.model_label.setText(f"Model: {fallback_result['new_model']} (Fallback)")
            self.model_label.setStyleSheet("color: #ffc107; font-weight: bold;")
            
            # Show fallback message
            message = f"""🔄 **Switched to {fallback_result['new_model']}**

Your premium ChatGPT model hit rate limits, so I've automatically switched to {fallback_result['new_model']}.

**What this means:**
• Your API key is valid and working
• Premium model temporarily unavailable
• Continuing with {fallback_result['new_model']} 
• Same great legal research capabilities

**To get premium back:**
• Wait 1 hour for limits to reset
• Add credits at https://platform.openai.com/account/billing
• Or continue with current model

Please resend your message to continue."""
            
            self.add_message(message, is_user=False)
            
        else:
            # All models exhausted
            message = """🚨 **All ChatGPT Models Rate Limited**

All available ChatGPT models have hit rate limits.

**Immediate Solutions:**
1. ⏰ **Wait 1 hour** - Rate limits will reset
2. 💰 **Add credits** - https://platform.openai.com/account/billing  
3. 🔧 **Use offline mode** - Local AI models (no API needed)
4. 📊 **Check usage** - https://platform.openai.com/usage

**Offline Mode:**
I can switch to local AI models that don't use OpenAI API.
This provides basic legal research without rate limits.

Would you like to switch to offline mode?"""
            
            self.add_message(message, is_user=False)

def main():
    """Main function with comprehensive error handling"""
    try:
        if not PYSIDE6_AVAILABLE:
            print("❌ PySide6 not available")
            print("Desktop GUI requires PySide6")
            print("Install with: pip install PySide6")
            print("Or use web interface: http://localhost:8877")
            return
        
        app = QApplication(sys.argv)
        
        # Set application style
        app.setStyle('Fusion')
        
        # Create main window
        window = ChatGPTStyleInterface()
        window.show()
        
        # Run application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Failed to start desktop interface: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()