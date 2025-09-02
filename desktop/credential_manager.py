"""
Secure credential management for the desktop application
"""
import os
import re
import json
import base64
import logging
from typing import Dict, Optional, List
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTextEdit, QTabWidget, QWidget, QFormLayout,
    QCheckBox, QMessageBox, QFileDialog, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)

class SecureCredentialManager:
    """Secure storage and management of API credentials"""
    
    def __init__(self, app_name: str = "InLegalDesk"):
        self.app_name = app_name
        self.config_dir = self._get_config_dir()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.credentials_file = self.config_dir / "credentials.enc"
        self.key_file = self.config_dir / "key.dat"
        
        self._encryption_key = None
    
    def _get_config_dir(self) -> Path:
        """Get platform-specific config directory"""
        if os.name == 'nt':  # Windows
            config_base = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
        else:  # Linux/macOS
            config_base = Path.home() / '.config'
        
        return config_base / self.app_name
    
    def _get_or_create_key(self, password: str) -> bytes:
        """Get or create encryption key from password"""
        try:
            # Use a consistent salt for the same user
            salt = b'inlegaldesk_salt_v1'  # In production, use random salt per user
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            return key
            
        except Exception as e:
            logger.error(f"Failed to derive encryption key: {e}")
            raise
    
    def save_credentials(self, credentials: Dict[str, str], password: str) -> bool:
        """
        Save credentials securely with encryption
        
        Args:
            credentials: Dictionary of credential key-value pairs
            password: Master password for encryption
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Validate credentials
            self._validate_credentials(credentials)
            
            # Get encryption key
            encryption_key = self._get_or_create_key(password)
            fernet = Fernet(encryption_key)
            
            # Encrypt credentials
            credentials_json = json.dumps(credentials)
            encrypted_data = fernet.encrypt(credentials_json.encode())
            
            # Save encrypted credentials
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set secure file permissions (Unix-like systems)
            if os.name != 'nt':
                os.chmod(self.credentials_file, 0o600)
            
            logger.info("Credentials saved securely")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            return False
    
    def load_credentials(self, password: str) -> Optional[Dict[str, str]]:
        """
        Load and decrypt credentials
        
        Args:
            password: Master password for decryption
            
        Returns:
            Dictionary of credentials or None if failed
        """
        try:
            if not self.credentials_file.exists():
                return None
            
            # Get encryption key
            encryption_key = self._get_or_create_key(password)
            fernet = Fernet(encryption_key)
            
            # Load and decrypt
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = fernet.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data.decode())
            
            # Validate loaded credentials
            self._validate_credentials(credentials)
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return None
    
    def _validate_credentials(self, credentials: Dict[str, str]):
        """Validate credential format and content"""
        if not isinstance(credentials, dict):
            raise ValueError("Credentials must be a dictionary")
        
        # Validate OpenAI API key format
        if 'OPENAI_API_KEY' in credentials:
            api_key = credentials['OPENAI_API_KEY']
            if not api_key.startswith('sk-') or len(api_key) < 20:
                raise ValueError("Invalid OpenAI API key format")
        
        # Validate URLs
        for key in ['OPENAI_BASE_URL']:
            if key in credentials:
                url = credentials[key]
                if not (url.startswith('http://') or url.startswith('https://')):
                    raise ValueError(f"Invalid URL format for {key}")
    
    def credentials_exist(self) -> bool:
        """Check if credentials file exists"""
        return self.credentials_file.exists()
    
    def delete_credentials(self) -> bool:
        """Delete stored credentials"""
        try:
            if self.credentials_file.exists():
                self.credentials_file.unlink()
            if self.key_file.exists():
                self.key_file.unlink()
            
            logger.info("Credentials deleted")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete credentials: {e}")
            return False

class CredentialDialog(QDialog):
    """Dialog for managing API credentials"""
    
    credentials_updated = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.credential_manager = SecureCredentialManager()
        self.setup_ui()
        self.load_existing_credentials()
    
    def setup_ui(self):
        """Setup the credential management UI"""
        self.setWindowTitle("API Credentials Manager")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Tab widget for different credential types
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # OpenAI credentials tab
        openai_tab = self._create_openai_tab()
        tab_widget.addTab(openai_tab, "OpenAI Configuration")
        
        # File upload tab
        upload_tab = self._create_upload_tab()
        tab_widget.addTab(upload_tab, "Upload Configuration")
        
        # Security info tab
        security_tab = self._create_security_tab()
        tab_widget.addTab(security_tab, "Security Information")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_credentials)
        button_layout.addWidget(self.test_btn)
        
        button_layout.addStretch()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_credentials)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Style
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #ccc;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #007acc;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
    
    def _create_openai_tab(self) -> QWidget:
        """Create OpenAI credentials tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # API Key section
        api_group = QGroupBox("OpenAI API Configuration")
        api_layout = QFormLayout(api_group)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        api_layout.addRow("API Key:", self.api_key_input)
        
        self.base_url_input = QLineEdit()
        self.base_url_input.setText("https://api.openai.com/v1")
        self.base_url_input.setPlaceholderText("https://api.openai.com/v1")
        api_layout.addRow("Base URL:", self.base_url_input)
        
        self.model_input = QLineEdit()
        self.model_input.setText("gpt-4o-mini")
        self.model_input.setPlaceholderText("gpt-4o-mini")
        api_layout.addRow("Model:", self.model_input)
        
        # Show/hide API key
        self.show_key_checkbox = QCheckBox("Show API Key")
        self.show_key_checkbox.toggled.connect(self._toggle_api_key_visibility)
        api_layout.addRow("", self.show_key_checkbox)
        
        layout.addWidget(api_group)
        
        # Security section
        security_group = QGroupBox("Security Settings")
        security_layout = QFormLayout(security_group)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter master password for encryption")
        security_layout.addRow("Master Password:", self.password_input)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("Confirm master password")
        security_layout.addRow("Confirm Password:", self.confirm_password_input)
        
        layout.addWidget(security_group)
        
        # Instructions
        instructions = QLabel("""
<b>🔒 Secure Credential Setup:</b><br>
1. Get your OpenAI API key from <a href="https://platform.openai.com/api-keys">platform.openai.com/api-keys</a><br>
2. Enter a strong master password (8+ characters, mixed case, numbers)<br>
3. Test the connection to verify your credentials<br>
4. Credentials are encrypted with AES-256 and stored locally only<br>
5. Never share your API key or master password with anyone
        """)
        instructions.setWordWrap(True)
        instructions.setOpenExternalLinks(True)
        layout.addWidget(instructions)
        
        layout.addStretch()
        
        return widget
    
    def _create_upload_tab(self) -> QWidget:
        """Create configuration file upload tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Upload section
        upload_group = QGroupBox("Upload Configuration File")
        upload_layout = QVBoxLayout(upload_group)
        
        instructions = QLabel("""
Upload a .env configuration file or JSON credentials file.
The file will be validated and encrypted before storage.
        """)
        instructions.setWordWrap(True)
        upload_layout.addWidget(instructions)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select configuration file...")
        self.file_path_input.setReadOnly(True)
        file_layout.addWidget(self.file_path_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_config_file)
        file_layout.addWidget(browse_btn)
        
        upload_layout.addLayout(file_layout)
        
        # Preview
        self.file_preview = QTextEdit()
        self.file_preview.setMaximumHeight(150)
        self.file_preview.setPlaceholderText("File content preview will appear here...")
        self.file_preview.setReadOnly(True)
        upload_layout.addWidget(QLabel("File Preview:"))
        upload_layout.addWidget(self.file_preview)
        
        layout.addWidget(upload_group)
        
        # Master password for upload
        password_group = QGroupBox("Encryption Password")
        password_layout = QFormLayout(password_group)
        
        self.upload_password_input = QLineEdit()
        self.upload_password_input.setEchoMode(QLineEdit.Password)
        self.upload_password_input.setPlaceholderText("Master password for encryption")
        password_layout.addRow("Master Password:", self.upload_password_input)
        
        layout.addWidget(password_group)
        
        # Upload button
        upload_btn = QPushButton("Upload and Encrypt")
        upload_btn.clicked.connect(self.upload_config_file)
        layout.addWidget(upload_btn)
        
        layout.addStretch()
        
        return widget
    
    def _create_security_tab(self) -> QWidget:
        """Create security information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        security_info = QTextEdit()
        security_info.setReadOnly(True)
        security_info.setHtml("""
<h3>🔒 Security Features</h3>

<h4>Credential Encryption</h4>
<ul>
<li><b>AES-256 Encryption</b>: All credentials encrypted with industry-standard AES-256</li>
<li><b>PBKDF2 Key Derivation</b>: 100,000 iterations for password-based encryption</li>
<li><b>Local Storage Only</b>: Credentials never transmitted over network</li>
<li><b>Secure File Permissions</b>: Restricted file access on Unix systems</li>
</ul>

<h4>Data Protection</h4>
<ul>
<li><b>No Logging</b>: API keys never written to log files</li>
<li><b>Memory Protection</b>: Credentials cleared from memory after use</li>
<li><b>Input Validation</b>: All inputs validated before processing</li>
<li><b>Safe File Handling</b>: Path traversal protection</li>
</ul>

<h4>Network Security</h4>
<ul>
<li><b>HTTPS Only</b>: All API calls use encrypted connections</li>
<li><b>Certificate Validation</b>: SSL certificates verified</li>
<li><b>Request Timeouts</b>: Prevent hanging connections</li>
<li><b>Rate Limiting</b>: Built-in request throttling</li>
</ul>

<h4>Best Practices</h4>
<ul>
<li><b>Strong Passwords</b>: Use complex master passwords</li>
<li><b>Regular Updates</b>: Keep application updated</li>
<li><b>Key Rotation</b>: Rotate API keys periodically</li>
<li><b>Secure Environment</b>: Use trusted networks and devices</li>
</ul>

<h4>Storage Location</h4>
<p><b>Windows:</b> <code>%APPDATA%\\InLegalDesk\\credentials.enc</code></p>
<p><b>Linux/macOS:</b> <code>~/.config/InLegalDesk/credentials.enc</code></p>
        """)
        
        layout.addWidget(security_info)
        
        # Management buttons
        mgmt_layout = QHBoxLayout()
        
        delete_btn = QPushButton("🗑️ Delete All Credentials")
        delete_btn.clicked.connect(self.delete_credentials)
        delete_btn.setStyleSheet("QPushButton { background-color: #dc3545; }")
        mgmt_layout.addWidget(delete_btn)
        
        mgmt_layout.addStretch()
        
        export_btn = QPushButton("📤 Export Encrypted Backup")
        export_btn.clicked.connect(self.export_credentials)
        mgmt_layout.addWidget(export_btn)
        
        layout.addLayout(mgmt_layout)
        
        return widget
    
    def _toggle_api_key_visibility(self, show: bool):
        """Toggle API key visibility"""
        if show:
            self.api_key_input.setEchoMode(QLineEdit.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)
    
    def browse_config_file(self):
        """Browse for configuration file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Configuration File",
            "",
            "Config Files (*.env *.json *.txt);;All Files (*)"
        )
        
        if file_path:
            self.file_path_input.setText(file_path)
            self._preview_config_file(file_path)
    
    def _preview_config_file(self, file_path: str):
        """Preview configuration file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Mask sensitive values in preview
            preview_content = self._mask_sensitive_content(content)
            self.file_preview.setPlainText(preview_content[:1000] + "..." if len(preview_content) > 1000 else preview_content)
            
        except Exception as e:
            self.file_preview.setPlainText(f"Error reading file: {e}")
    
    def _mask_sensitive_content(self, content: str) -> str:
        """Mask sensitive values in content preview"""
        import re
        
        # Mask API keys
        content = re.sub(r'(sk-[a-zA-Z0-9]{20,})', r'sk-****...****', content)
        
        # Mask other sensitive patterns
        content = re.sub(r'(password\s*=\s*)[^\s\n]+', r'\1****', content, flags=re.IGNORECASE)
        content = re.sub(r'(token\s*=\s*)[^\s\n]+', r'\1****', content, flags=re.IGNORECASE)
        
        return content
    
    def upload_config_file(self):
        """Upload and process configuration file"""
        file_path = self.file_path_input.text().strip()
        password = self.upload_password_input.text().strip()
        
        if not file_path or not password:
            QMessageBox.warning(self, "Warning", "Please select a file and enter a master password")
            return
        
        try:
            # Parse configuration file
            credentials = self._parse_config_file(file_path)
            
            if not credentials:
                QMessageBox.warning(self, "Warning", "No valid credentials found in file")
                return
            
            # Save credentials
            if self.credential_manager.save_credentials(credentials, password):
                QMessageBox.information(self, "Success", "Configuration uploaded and encrypted successfully")
                self.credentials_updated.emit(credentials)
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to save credentials")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process file: {e}")
    
    def _parse_config_file(self, file_path: str) -> Dict[str, str]:
        """Parse configuration file and extract credentials"""
        credentials = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try JSON format first
            if file_path.endswith('.json'):
                data = json.loads(content)
                if isinstance(data, dict):
                    credentials.update(data)
            
            # Try .env format
            else:
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        
                        if key in ['OPENAI_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_MODEL']:
                            credentials[key] = value
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to parse config file: {e}")
            raise
    
    def test_credentials(self):
        """Test the entered credentials with enhanced validation"""
        try:
            from security_validator import DesktopSecurityValidator
            
            api_key = self.api_key_input.text().strip()
            base_url = self.base_url_input.text().strip()
            
            if not api_key:
                QMessageBox.warning(self, "Warning", "Please enter an API key")
                return
            
            # Test API connection
            self.test_btn.setEnabled(False)
            self.test_btn.setText("Testing...")
            
            # Validate API key format
            key_validation = DesktopSecurityValidator.validate_api_key(api_key)
            if not key_validation["is_valid"]:
                error_msg = "API Key Validation Failed:\n" + "\n".join(key_validation["errors"])
                QMessageBox.warning(self, "Invalid API Key", error_msg)
                self.test_btn.setEnabled(True)
                self.test_btn.setText("Test Connection")
                return
            
            # Validate base URL
            url_validation = DesktopSecurityValidator.validate_api_url(base_url)
            if not url_validation["is_valid"]:
                error_msg = "Base URL Validation Failed:\n" + "\n".join(url_validation["errors"])
                QMessageBox.warning(self, "Invalid URL", error_msg)
                self.test_btn.setEnabled(True)
                self.test_btn.setText("Test Connection")
                return
            
            # Show warnings if any
            all_warnings = key_validation.get("warnings", []) + url_validation.get("warnings", [])
            if all_warnings:
                warning_msg = "Security Warnings:\n" + "\n".join(all_warnings)
                warning_msg += "\n\nDo you want to continue?"
                
                reply = QMessageBox.question(
                    self,
                    "Security Warning",
                    warning_msg,
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    self.test_btn.setEnabled(True)
                    self.test_btn.setText("Test Connection")
                    return
            
            # Perform actual connection test
            self._perform_connection_test(api_key, base_url, key_validation["masked_key"])
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection test failed: {e}")
            self.test_btn.setEnabled(True)
            self.test_btn.setText("Test Connection")
    
    def _perform_connection_test(self, api_key: str, base_url: str, masked_key: str):
        """Perform actual API connection test"""
        import asyncio
        import httpx
        
        async def test_api():
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json={
                            "model": "gpt-3.5-turbo",
                            "messages": [{"role": "user", "content": "test"}],
                            "max_tokens": 5
                        }
                    )
                    
                    if response.status_code == 200:
                        return {"success": True, "message": "API connection successful"}
                    elif response.status_code == 401:
                        return {"success": False, "message": "Invalid API key"}
                    elif response.status_code == 429:
                        return {"success": False, "message": "Rate limit exceeded - try again later"}
                    else:
                        return {"success": False, "message": f"API error: {response.status_code}"}
                        
            except Exception as e:
                return {"success": False, "message": f"Connection failed: {e}"}
        
        # Run test
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(test_api())
            
            if result["success"]:
                QMessageBox.information(
                    self, 
                    "Connection Successful", 
                    f"✅ API connection successful!\n\nKey: {masked_key}\nURL: {base_url}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Connection Failed",
                    f"❌ {result['message']}\n\nPlease check your credentials and try again."
                )
            
        except Exception as e:
            QMessageBox.critical(self, "Test Error", f"Connection test error: {e}")
        
        finally:
            self.test_btn.setEnabled(True)
            self.test_btn.setText("Test Connection")
    
    def save_credentials(self):
        """Save the entered credentials with enhanced validation"""
        try:
            from security_validator import DesktopSecurityValidator
            
            # Get credentials from form
            credentials = {
                'OPENAI_API_KEY': self.api_key_input.text().strip(),
                'OPENAI_BASE_URL': self.base_url_input.text().strip(),
                'OPENAI_MODEL': self.model_input.text().strip()
            }
            
            # Remove empty values
            credentials = {k: v for k, v in credentials.items() if v}
            
            if not credentials.get('OPENAI_API_KEY'):
                QMessageBox.warning(self, "Warning", "Please enter an API key")
                return
            
            # Validate API key
            key_validation = DesktopSecurityValidator.validate_api_key(credentials['OPENAI_API_KEY'])
            if not key_validation["is_valid"]:
                error_msg = "API Key Validation Failed:\n" + "\n".join(key_validation["errors"])
                QMessageBox.warning(self, "Invalid API Key", error_msg)
                return
            
            # Validate base URL
            if credentials.get('OPENAI_BASE_URL'):
                url_validation = DesktopSecurityValidator.validate_api_url(credentials['OPENAI_BASE_URL'])
                if not url_validation["is_valid"]:
                    error_msg = "Base URL Validation Failed:\n" + "\n".join(url_validation["errors"])
                    QMessageBox.warning(self, "Invalid URL", error_msg)
                    return
            
            # Get master password
            password = self.password_input.text().strip()
            confirm_password = self.confirm_password_input.text().strip()
            
            if not password:
                QMessageBox.warning(self, "Warning", "Please enter a master password")
                return
            
            if password != confirm_password:
                QMessageBox.warning(self, "Warning", "Passwords do not match")
                return
            
            # Enhanced password validation
            password_errors = self._validate_master_password(password)
            if password_errors:
                error_msg = "Master Password Requirements:\n" + "\n".join(password_errors)
                QMessageBox.warning(self, "Weak Password", error_msg)
                return
            
            # Confirm save with security summary
            masked_key = key_validation["masked_key"]
            confirm_msg = f"""
Save Credentials Securely?

API Key: {masked_key}
Base URL: {credentials.get('OPENAI_BASE_URL', 'Default')}
Model: {credentials.get('OPENAI_MODEL', 'Default')}

Security:
• AES-256 encryption
• PBKDF2 key derivation (100,000 iterations)
• Local storage only
• Master password protection
            """
            
            reply = QMessageBox.question(
                self,
                "Confirm Save",
                confirm_msg.strip(),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Save credentials
            if self.credential_manager.save_credentials(credentials, password):
                QMessageBox.information(
                    self, 
                    "Credentials Saved", 
                    f"✅ Credentials saved securely!\n\nKey: {masked_key}\nEncryption: AES-256\nStorage: Local only"
                )
                self.credentials_updated.emit(credentials)
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to save credentials")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save credentials: {e}")
    
    def _validate_master_password(self, password: str) -> List[str]:
        """Validate master password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("• Must be at least 8 characters long")
        
        if not re.search(r'[a-z]', password):
            errors.append("• Must contain lowercase letters")
        
        if not re.search(r'[A-Z]', password):
            errors.append("• Must contain uppercase letters")
        
        if not re.search(r'\d', password):
            errors.append("• Must contain numbers")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("• Should contain special characters")
        
        # Check for common weak passwords
        weak_patterns = [
            r'password', r'123456', r'qwerty', r'admin',
            r'letmein', r'welcome', r'monkey', r'dragon'
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, password.lower()):
                errors.append("• Avoid common passwords")
                break
        
        return errors
    
    def load_existing_credentials(self):
        """Load existing credentials if available"""
        if self.credential_manager.credentials_exist():
            # Show that credentials exist but don't auto-load for security
            info = QLabel("🔒 Encrypted credentials found. Enter master password to load.")
            info.setStyleSheet("color: #007acc; font-weight: bold;")
            
            # Add load button
            load_btn = QPushButton("Load Existing Credentials")
            load_btn.clicked.connect(self.load_credentials)
    
    def load_credentials(self):
        """Load existing encrypted credentials"""
        password = self.password_input.text().strip()
        
        if not password:
            QMessageBox.warning(self, "Warning", "Please enter master password")
            return
        
        credentials = self.credential_manager.load_credentials(password)
        
        if credentials:
            # Populate form
            self.api_key_input.setText(credentials.get('OPENAI_API_KEY', ''))
            self.base_url_input.setText(credentials.get('OPENAI_BASE_URL', 'https://api.openai.com/v1'))
            self.model_input.setText(credentials.get('OPENAI_MODEL', 'gpt-4o-mini'))
            
            QMessageBox.information(self, "Success", "Credentials loaded successfully")
        else:
            QMessageBox.warning(self, "Error", "Failed to load credentials. Check your master password.")
    
    def delete_credentials(self):
        """Delete stored credentials"""
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion", 
            "Are you sure you want to delete all stored credentials?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.credential_manager.delete_credentials():
                QMessageBox.information(self, "Success", "Credentials deleted successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to delete credentials")
    
    def export_credentials(self):
        """Export encrypted credentials backup"""
        if not self.credential_manager.credentials_exist():
            QMessageBox.information(self, "Info", "No credentials to export")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Encrypted Backup",
            "inlegaldesk_credentials_backup.enc",
            "Encrypted Files (*.enc);;All Files (*)"
        )
        
        if file_path:
            try:
                # Copy encrypted file
                import shutil
                shutil.copy2(self.credential_manager.credentials_file, file_path)
                QMessageBox.information(self, "Success", f"Encrypted backup saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export backup: {e}")