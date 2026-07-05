"""
Settings Tab
------------
Allows configuring the Google Gemini API key and choosing the target Gemini model.
Configurations are stored securely using QSettings.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSettings, QThread, pyqtSignal
import urllib.request
import json

from .styles import BLUE_ACCENT, BORDER_COLOR, TEXT_DARK, TEXT_MUTED, WHITE


class TestConnectionWorker(QThread):
    """Background worker to verify the Gemini API key without freezing the UI."""
    finished = pyqtSignal(bool, str)

    def __init__(self, api_key: str, model_name: str):
        super().__init__()
        self.api_key = api_key
        self.model_name = model_name

    def run(self):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{
                "parts": [{"text": "Hello, confirm connection. Reply in under 5 words."}]
            }]
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    self.finished.emit(True, "Connection successful!")
                else:
                    self.finished.emit(False, f"HTTP Error: {response.status}")
        except Exception as e:
            self.finished.emit(False, str(e))


class SettingsTab(QWidget):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self._settings = QSettings("Daluvuyo", "CustomerInsightCMS")
        self._test_worker = None
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Page Header
        title = QLabel("Settings")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("Configure API keys, large language models, and system preferences.")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Settings Card
        card = QFrame()
        card.setObjectName("kpiCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)

        # API Key field
        key_label = QLabel("Gemini API Key:")
        key_label.setStyleSheet(f"color: {TEXT_DARK}; font-weight: 600;")
        
        key_row = QHBoxLayout()
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("Enter your Google AI Studio API Key")
        
        self.show_btn = QPushButton("Show")
        self.show_btn.setObjectName("secondary")
        self.show_btn.setFixedWidth(70)
        self.show_btn.clicked.connect(self._toggle_key_visibility)
        
        key_row.addWidget(self.key_input)
        key_row.addWidget(self.show_btn)

        # Model Selector
        model_label = QLabel("Gemini LLM Model:")
        model_label.setStyleSheet(f"color: {TEXT_DARK}; font-weight: 600;")
        
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ])

        card_layout.addWidget(key_label)
        card_layout.addLayout(key_row)
        card_layout.addWidget(model_label)
        card_layout.addWidget(self.model_combo)
        
        layout.addWidget(card)

        # Actions Row
        actions_row = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self._save_settings)
        
        self.test_btn = QPushButton("Test API Connection")
        self.test_btn.setObjectName("secondary")
        self.test_btn.clicked.connect(self._test_connection)
        
        actions_row.addWidget(self.save_btn)
        actions_row.addWidget(self.test_btn)
        actions_row.addStretch()
        
        layout.addLayout(actions_row)
        layout.addStretch()

    def _toggle_key_visibility(self):
        if self.key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_btn.setText("Hide")
        else:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_btn.setText("Show")

    def _load_settings(self):
        key = self._settings.value("gemini_api_key", "")
        model = self._settings.value("gemini_model", "gemini-2.5-flash")
        
        self.key_input.setText(key)
        self.model_combo.setCurrentText(model)

    def _save_settings(self):
        key = self.key_input.text().strip()
        model = self.model_combo.currentText()
        
        self._settings.setValue("gemini_api_key", key)
        self._settings.setValue("gemini_model", model)
        
        QMessageBox.information(self, "Settings Saved", "Preferences successfully updated.")

    def _test_connection(self):
        key = self.key_input.text().strip()
        model = self.model_combo.currentText()
        
        if not key:
            QMessageBox.warning(self, "Missing Key", "Please input a Gemini API Key to test.")
            return

        self.test_btn.setEnabled(False)
        self.test_btn.setText("Testing...")

        self._test_worker = TestConnectionWorker(key, model)
        self._test_worker.finished.connect(self._on_test_finished)
        self._test_worker.start()

    def _on_test_finished(self, success: bool, message: str):
        self.test_btn.setEnabled(True)
        self.test_btn.setText("Test API Connection")
        
        if success:
            QMessageBox.information(self, "Test Passed", "Connected successfully to Google Gemini API!")
        else:
            QMessageBox.critical(self, "Test Failed", f"Could not connect to Gemini API:\n\n{message}")
