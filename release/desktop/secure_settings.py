"""
Secure settings and configuration management for desktop app
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTextEdit, QTabWidget, QWidget, QFormLayout,
    QCheckBox, QMessageBox, QGroupBox, QSpinBox, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from credential_manager import SecureCredentialManager

logger = logging.getLogger(__name__)

class SecureSettingsDialog(QDialog):
    """Secure settings management dialog"""
    
    settings_updated = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.credential_manager = SecureCredentialManager()
        self.current_settings = self._load_current_settings()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the settings UI"""
        self.setWindowTitle("InLegalDesk Settings")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Security settings tab
        security_tab = self._create_security_tab()
        tab_widget.addTab(security_tab, "🔒 Security")
        
        # Performance settings tab
        performance_tab = self._create_performance_tab()
        tab_widget.addTab(performance_tab, "⚡ Performance")
        
        # Privacy settings tab
        privacy_tab = self._create_privacy_tab()
        tab_widget.addTab(privacy_tab, "🛡️ Privacy")
        
        # Advanced settings tab
        advanced_tab = self._create_advanced_tab()
        tab_widget.addTab(advanced_tab, "🔧 Advanced")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _create_security_tab(self) -> QWidget:
        """Create security settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # File security group
        file_group = QGroupBox("File Upload Security")
        file_layout = QFormLayout(file_group)
        
        self.max_file_size_spin = QSpinBox()
        self.max_file_size_spin.setRange(1, 1000)
        self.max_file_size_spin.setValue(100)
        self.max_file_size_spin.setSuffix(" MB")
        file_layout.addRow("Max File Size:", self.max_file_size_spin)
        
        self.validate_pdfs_check = QCheckBox("Validate PDF files")
        self.validate_pdfs_check.setChecked(True)
        file_layout.addRow("", self.validate_pdfs_check)
        
        self.quarantine_suspicious_check = QCheckBox("Quarantine suspicious files")
        self.quarantine_suspicious_check.setChecked(True)
        file_layout.addRow("", self.quarantine_suspicious_check)
        
        layout.addWidget(file_group)
        
        # Network security group
        network_group = QGroupBox("Network Security")
        network_layout = QFormLayout(network_group)
        
        self.verify_ssl_check = QCheckBox("Verify SSL certificates")
        self.verify_ssl_check.setChecked(True)
        network_layout.addRow("", self.verify_ssl_check)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setValue(120)
        self.timeout_spin.setSuffix(" seconds")
        network_layout.addRow("Request Timeout:", self.timeout_spin)
        
        layout.addWidget(network_group)
        
        # Credential security group
        cred_group = QGroupBox("Credential Security")
        cred_layout = QVBoxLayout(cred_group)
        
        cred_info = QLabel("""
<b>Credential Protection:</b><br>
• All API keys are encrypted with AES-256<br>
• Master password required for access<br>
• Credentials never logged or transmitted unencrypted<br>
• Local storage only - never sent to external servers
        """)
        cred_info.setWordWrap(True)
        cred_layout.addWidget(cred_info)
        
        cred_btn_layout = QHBoxLayout()
        
        manage_creds_btn = QPushButton("🔑 Manage Credentials")
        manage_creds_btn.clicked.connect(self.manage_credentials)
        cred_btn_layout.addWidget(manage_creds_btn)
        
        delete_creds_btn = QPushButton("🗑️ Delete All Credentials")
        delete_creds_btn.setStyleSheet("QPushButton { background-color: #dc3545; }")
        delete_creds_btn.clicked.connect(self.delete_credentials)
        cred_btn_layout.addWidget(delete_creds_btn)
        
        cred_layout.addLayout(cred_btn_layout)
        
        layout.addWidget(cred_group)
        
        layout.addStretch()
        return widget
    
    def _create_performance_tab(self) -> QWidget:
        """Create performance settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Processing group
        processing_group = QGroupBox("Document Processing")
        processing_layout = QFormLayout(processing_group)
        
        self.max_workers_spin = QSpinBox()
        self.max_workers_spin.setRange(0, 16)
        self.max_workers_spin.setValue(0)
        self.max_workers_spin.setSpecialValueText("Auto")
        processing_layout.addRow("Max Workers:", self.max_workers_spin)
        
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 16)
        self.batch_size_spin.setValue(4)
        processing_layout.addRow("Batch Size:", self.batch_size_spin)
        
        self.enable_gpu_check = QCheckBox("Enable GPU acceleration (if available)")
        self.enable_gpu_check.setChecked(True)
        processing_layout.addRow("", self.enable_gpu_check)
        
        layout.addWidget(processing_group)
        
        # Model selection group
        model_group = QGroupBox("AI Models")
        model_layout = QFormLayout(model_group)
        
        self.vlm_order_input = QLineEdit()
        self.vlm_order_input.setText("donut,pix2struct,openai,tesseract_fallback")
        self.vlm_order_input.setPlaceholderText("comma-separated model order")
        model_layout.addRow("VLM Order:", self.vlm_order_input)
        
        self.enable_ocr_check = QCheckBox("Enable OCR fallback")
        self.enable_ocr_check.setChecked(False)
        model_layout.addRow("", self.enable_ocr_check)
        
        layout.addWidget(model_group)
        
        layout.addStretch()
        return widget
    
    def _create_privacy_tab(self) -> QWidget:
        """Create privacy settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Data handling group
        data_group = QGroupBox("Data Handling")
        data_layout = QVBoxLayout(data_group)
        
        privacy_info = QLabel("""
<b>Privacy Protection:</b><br>
• Documents processed locally by default<br>
• No data sent to external services except OpenAI API<br>
• Chat history stored locally only<br>
• No telemetry or usage tracking<br>
• Temporary files automatically cleaned
        """)
        privacy_info.setWordWrap(True)
        data_layout.addWidget(privacy_info)
        
        self.local_processing_check = QCheckBox("Prefer local processing (disable OpenAI when possible)")
        self.local_processing_check.setChecked(False)
        data_layout.addWidget(self.local_processing_check)
        
        self.clear_temp_check = QCheckBox("Automatically clear temporary files")
        self.clear_temp_check.setChecked(True)
        data_layout.addWidget(self.clear_temp_check)
        
        self.save_chat_history_check = QCheckBox("Save chat history")
        self.save_chat_history_check.setChecked(True)
        data_layout.addWidget(self.save_chat_history_check)
        
        layout.addWidget(data_group)
        
        # Data management buttons
        mgmt_group = QGroupBox("Data Management")
        mgmt_layout = QVBoxLayout(mgmt_group)
        
        mgmt_btn_layout = QHBoxLayout()
        
        clear_cache_btn = QPushButton("🗑️ Clear Cache")
        clear_cache_btn.clicked.connect(self.clear_cache)
        mgmt_btn_layout.addWidget(clear_cache_btn)
        
        clear_history_btn = QPushButton("🗑️ Clear Chat History")
        clear_history_btn.clicked.connect(self.clear_chat_history)
        mgmt_btn_layout.addWidget(clear_history_btn)
        
        mgmt_layout.addLayout(mgmt_btn_layout)
        layout.addWidget(mgmt_group)
        
        layout.addStretch()
        return widget
    
    def _create_advanced_tab(self) -> QWidget:
        """Create advanced settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Backend configuration
        backend_group = QGroupBox("Backend Configuration")
        backend_layout = QFormLayout(backend_group)
        
        self.backend_url_input = QLineEdit()
        self.backend_url_input.setText(os.getenv("BACKEND_URL", ""))
        self.backend_url_input.setPlaceholderText("Leave empty for auto-start")
        backend_layout.addRow("Backend URL:", self.backend_url_input)
        
        self.backend_port_spin = QSpinBox()
        self.backend_port_spin.setRange(1024, 65535)
        self.backend_port_spin.setValue(int(os.getenv("BACKEND_PORT", 8877)))
        backend_layout.addRow("Backend Port:", self.backend_port_spin)
        
        layout.addWidget(backend_group)
        
        # Logging configuration
        logging_group = QGroupBox("Logging")
        logging_layout = QFormLayout(logging_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        logging_layout.addRow("Log Level:", self.log_level_combo)
        
        self.enable_file_logging_check = QCheckBox("Enable file logging")
        self.enable_file_logging_check.setChecked(False)
        logging_layout.addRow("", self.enable_file_logging_check)
        
        layout.addWidget(logging_group)
        
        # Developer options
        dev_group = QGroupBox("Developer Options")
        dev_layout = QVBoxLayout(dev_group)
        
        self.debug_mode_check = QCheckBox("Enable debug mode")
        self.debug_mode_check.setChecked(False)
        dev_layout.addWidget(self.debug_mode_check)
        
        self.show_api_responses_check = QCheckBox("Show raw API responses")
        self.show_api_responses_check.setChecked(False)
        dev_layout.addWidget(self.show_api_responses_check)
        
        layout.addWidget(dev_group)
        
        layout.addStretch()
        return widget
    
    def _load_current_settings(self) -> Dict[str, Any]:
        """Load current application settings"""
        return {
            "max_file_size_mb": 100,
            "validate_pdfs": True,
            "quarantine_suspicious": True,
            "verify_ssl": True,
            "request_timeout": 120,
            "max_workers": 0,
            "batch_size": 4,
            "enable_gpu": True,
            "vlm_order": "donut,pix2struct,openai,tesseract_fallback",
            "enable_ocr": False,
            "local_processing": False,
            "clear_temp": True,
            "save_chat_history": True,
            "backend_url": "",
            "backend_port": 8877,
            "log_level": "INFO",
            "enable_file_logging": False,
            "debug_mode": False,
            "show_api_responses": False
        }
    
    def manage_credentials(self):
        """Open credential management dialog"""
        from credential_manager import CredentialDialog
        
        dialog = CredentialDialog(self)
        dialog.exec()
    
    def delete_credentials(self):
        """Delete all stored credentials"""
        reply = QMessageBox.question(
            self,
            "Delete Credentials",
            "Are you sure you want to delete all stored API credentials?\n\n"
            "This will remove all encrypted credential data.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.credential_manager.delete_credentials():
                QMessageBox.information(self, "Success", "All credentials deleted successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to delete credentials")
    
    def clear_cache(self):
        """Clear application cache"""
        reply = QMessageBox.question(
            self,
            "Clear Cache",
            "Clear all cached data including embeddings and temporary files?\n\n"
            "This will free up disk space but may slow down future operations.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Clear various cache directories
                cache_dirs = [
                    "data/embeddings",
                    "data/temp",
                    "logs"
                ]
                
                cleared_size = 0
                for cache_dir in cache_dirs:
                    cache_path = Path(cache_dir)
                    if cache_path.exists():
                        for file_path in cache_path.rglob("*"):
                            if file_path.is_file():
                                cleared_size += file_path.stat().st_size
                                file_path.unlink()
                
                QMessageBox.information(
                    self, 
                    "Cache Cleared", 
                    f"Cache cleared successfully!\nFreed {cleared_size / (1024*1024):.1f} MB of disk space"
                )
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear cache: {e}")
    
    def clear_chat_history(self):
        """Clear chat history"""
        reply = QMessageBox.question(
            self,
            "Clear Chat History",
            "Delete all chat history?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Clear chat history files
                history_dir = Path("data/chat_history")
                if history_dir.exists():
                    for file_path in history_dir.glob("*.json"):
                        file_path.unlink()
                
                QMessageBox.information(self, "Success", "Chat history cleared successfully")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear chat history: {e}")
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Reset all settings to default values?\n\n"
            "This will not affect your saved credentials.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.current_settings = self._load_current_settings()
            self._populate_form()
            QMessageBox.information(self, "Success", "Settings reset to defaults")
    
    def _populate_form(self):
        """Populate form with current settings"""
        # Security tab
        self.max_file_size_spin.setValue(self.current_settings.get("max_file_size_mb", 100))
        self.validate_pdfs_check.setChecked(self.current_settings.get("validate_pdfs", True))
        self.quarantine_suspicious_check.setChecked(self.current_settings.get("quarantine_suspicious", True))
        self.verify_ssl_check.setChecked(self.current_settings.get("verify_ssl", True))
        self.timeout_spin.setValue(self.current_settings.get("request_timeout", 120))
        
        # Performance tab
        self.max_workers_spin.setValue(self.current_settings.get("max_workers", 0))
        self.batch_size_spin.setValue(self.current_settings.get("batch_size", 4))
        self.enable_gpu_check.setChecked(self.current_settings.get("enable_gpu", True))
        self.vlm_order_input.setText(self.current_settings.get("vlm_order", "donut,pix2struct,openai,tesseract_fallback"))
        self.enable_ocr_check.setChecked(self.current_settings.get("enable_ocr", False))
        
        # Privacy tab
        self.local_processing_check.setChecked(self.current_settings.get("local_processing", False))
        self.clear_temp_check.setChecked(self.current_settings.get("clear_temp", True))
        self.save_chat_history_check.setChecked(self.current_settings.get("save_chat_history", True))
        
        # Advanced tab
        self.backend_url_input.setText(self.current_settings.get("backend_url", ""))
        self.backend_port_spin.setValue(self.current_settings.get("backend_port", 8877))
        self.log_level_combo.setCurrentText(self.current_settings.get("log_level", "INFO"))
        self.enable_file_logging_check.setChecked(self.current_settings.get("enable_file_logging", False))
        self.debug_mode_check.setChecked(self.current_settings.get("debug_mode", False))
        self.show_api_responses_check.setChecked(self.current_settings.get("show_api_responses", False))
    
    def apply_settings(self):
        """Apply settings without saving"""
        settings = self._collect_settings()
        self._apply_settings_to_environment(settings)
        self.settings_updated.emit(settings)
        QMessageBox.information(self, "Applied", "Settings applied for this session")
    
    def save_settings(self):
        """Save settings permanently"""
        settings = self._collect_settings()
        
        if self._save_settings_to_file(settings):
            self._apply_settings_to_environment(settings)
            self.settings_updated.emit(settings)
            QMessageBox.information(self, "Saved", "Settings saved successfully")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save settings")
    
    def _collect_settings(self) -> Dict[str, Any]:
        """Collect settings from form"""
        return {
            "max_file_size_mb": self.max_file_size_spin.value(),
            "validate_pdfs": self.validate_pdfs_check.isChecked(),
            "quarantine_suspicious": self.quarantine_suspicious_check.isChecked(),
            "verify_ssl": self.verify_ssl_check.isChecked(),
            "request_timeout": self.timeout_spin.value(),
            "max_workers": self.max_workers_spin.value(),
            "batch_size": self.batch_size_spin.value(),
            "enable_gpu": self.enable_gpu_check.isChecked(),
            "vlm_order": self.vlm_order_input.text().strip(),
            "enable_ocr": self.enable_ocr_check.isChecked(),
            "local_processing": self.local_processing_check.isChecked(),
            "clear_temp": self.clear_temp_check.isChecked(),
            "save_chat_history": self.save_chat_history_check.isChecked(),
            "backend_url": self.backend_url_input.text().strip(),
            "backend_port": self.backend_port_spin.value(),
            "log_level": self.log_level_combo.currentText(),
            "enable_file_logging": self.enable_file_logging_check.isChecked(),
            "debug_mode": self.debug_mode_check.isChecked(),
            "show_api_responses": self.show_api_responses_check.isChecked()
        }
    
    def _apply_settings_to_environment(self, settings: Dict[str, Any]):
        """Apply settings to environment variables"""
        env_mapping = {
            "max_workers": "MAX_WORKERS",
            "batch_size": "VLM_BATCH_SIZE",
            "vlm_order": "VLM_ORDER",
            "enable_ocr": "ENABLE_OCR_FALLBACK",
            "backend_port": "BACKEND_PORT",
            "log_level": "LOG_LEVEL",
            "enable_file_logging": "ENABLE_FILE_LOGGING"
        }
        
        for setting_key, env_key in env_mapping.items():
            value = settings.get(setting_key)
            if value is not None:
                if isinstance(value, bool):
                    os.environ[env_key] = "true" if value else "false"
                else:
                    os.environ[env_key] = str(value)
    
    def _save_settings_to_file(self, settings: Dict[str, Any]) -> bool:
        """Save settings to file"""
        try:
            config_dir = self.credential_manager.config_dir
            settings_file = config_dir / "settings.json"
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False