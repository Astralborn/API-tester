"""UI builder module for API Test Tool - Minimalistic design."""
from __future__ import annotations

from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QLineEdit, QPushButton, QCheckBox, QTextEdit,
    QLabel, QWidget, QSizePolicy
)

from constants import API_ENDPOINTS


class UIBuilderMixin:
    """Mixin providing minimalistic UI building and theming."""

    def apply_light_theme(self) -> None:
        """Apply minimal light theme."""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#ffffff"))
        palette.setColor(QPalette.Base, QColor("#ffffff"))
        palette.setColor(QPalette.AlternateBase, QColor("#f5f5f5"))
        palette.setColor(QPalette.Text, QColor("#1a1a1a"))
        palette.setColor(QPalette.WindowText, QColor("#1a1a1a"))
        palette.setColor(QPalette.Button, QColor("#f0f0f0"))
        palette.setColor(QPalette.ButtonText, QColor("#1a1a1a"))
        palette.setColor(QPalette.Highlight, QColor("#0066cc"))
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        QApplication.setPalette(palette)

        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                color: #1a1a1a;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-size: 13px;
                border: none;
            }

            QLineEdit, QComboBox {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 6px 10px;
                min-height: 28px;
            }

            QLineEdit:focus, QComboBox:focus {
                border-color: #0066cc;
                background-color: #ffffff;
            }

            QLineEdit::placeholder {
                color: #999999;
            }

            QComboBox::drop-down {
                border: none;
                width: 20px;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #666666;
                margin-right: 6px;
            }

            QPushButton {
                background-color: #1a1a1a;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }

            QPushButton:hover {
                background-color: #333333;
            }

            QPushButton:pressed {
                background-color: #000000;
            }

            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }

            QPushButton#secondary {
                background-color: transparent;
                color: #1a1a1a;
                border: 1px solid #d0d0d0;
            }

            QPushButton#secondary:hover {
                background-color: #f5f5f5;
                border-color: #b0b0b0;
            }

            QCheckBox {
                spacing: 6px;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                background-color: #ffffff;
            }

            QCheckBox::indicator:checked {
                background-color: #1a1a1a;
                border-color: #1a1a1a;
            }

            QTextEdit {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 12px;
                font-family: 'SF Mono', Monaco, 'Cascadia Code', Consolas, monospace;
                font-size: 12px;
                line-height: 1.5;
            }

            QTextEdit:focus {
                border-color: #0066cc;
                background-color: #ffffff;
            }

            QLabel {
                color: #666666;
                font-size: 12px;
            }

            QLabel#header {
                color: #1a1a1a;
                font-size: 20px;
                font-weight: 600;
            }

            QLabel#section {
                color: #666666;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
        """)

    def build_ui(self) -> None:
        """Build minimalistic UI."""
        outer = QVBoxLayout(self)
        outer.setSpacing(0)
        outer.setContentsMargins(40, 32, 40, 24)

        # ===== Header =====
        header = QLabel("API Tester")
        header.setObjectName("header")
        outer.addWidget(header)

        # Subtitle / status
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("section")
        outer.addWidget(self.status_label)
        outer.addSpacing(24)

        # ===== Connection Row =====
        conn_label = QLabel("Connection")
        conn_label.setObjectName("section")
        outer.addWidget(conn_label)

        conn_row = QHBoxLayout()
        conn_row.setSpacing(8)

        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("192.168.1.100")
        self.ip_edit.setFixedWidth(140)
        self.ip_edit.textChanged.connect(self._auto_save_connection_settings)

        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("username")
        self.user_edit.setFixedWidth(120)
        self.user_edit.textChanged.connect(self._auto_save_connection_settings)

        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("password")
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.pass_edit.setFixedWidth(120)

        self.simple_check = QCheckBox("Simple format")
        self.simple_check.toggled.connect(self._auto_save_connection_settings)

        conn_row.addWidget(self.ip_edit)
        conn_row.addWidget(self.user_edit)
        conn_row.addWidget(self.pass_edit)
        conn_row.addWidget(self.simple_check)
        conn_row.addStretch()

        outer.addLayout(conn_row)
        outer.addSpacing(20)

        # ===== Preset Section =====
        preset_label = QLabel("Preset")
        preset_label.setObjectName("section")
        outer.addWidget(preset_label)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)

        self.test_mode_combo = QComboBox()
        self.test_mode_combo.addItems(["happy", "unhappy"])
        self.test_mode_combo.setFixedWidth(100)
        self.test_mode_combo.currentTextChanged.connect(self.update_presets_list)
        self.test_mode_combo.currentTextChanged.connect(self._auto_save_ui_settings)

        self.preset_search = QLineEdit()
        self.preset_search.setPlaceholderText("Search...")
        self.preset_search.setFixedWidth(120)
        self.preset_search.textChanged.connect(self.update_presets_list)

        self.preset_combo = QComboBox()
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)

        btn_load = QPushButton("Load")
        btn_load.setObjectName("secondary")
        btn_load.setFixedWidth(60)
        btn_load.clicked.connect(self.load_preset)

        btn_save = QPushButton("Save")
        btn_save.setObjectName("secondary")
        btn_save.setFixedWidth(60)
        btn_save.clicked.connect(self.save_preset)

        preset_row.addWidget(self.test_mode_combo)
        preset_row.addWidget(self.preset_search)
        preset_row.addWidget(self.preset_combo, 1)
        preset_row.addWidget(btn_load)
        preset_row.addWidget(btn_save)

        outer.addLayout(preset_row)
        outer.addSpacing(20)

        # ===== Request Section =====
        req_label = QLabel("Request")
        req_label.setObjectName("section")
        outer.addWidget(req_label)

        req_row = QHBoxLayout()
        req_row.setSpacing(8)

        self.endpoint_combo = QComboBox()
        self.endpoint_combo.addItems(API_ENDPOINTS)
        self.endpoint_combo.currentTextChanged.connect(self._auto_save_ui_settings)

        self.json_type_combo = QComboBox()
        self.json_type_combo.addItems(["normal", "google", "rpc"])
        self.json_type_combo.setFixedWidth(100)
        self.json_type_combo.currentTextChanged.connect(self._auto_save_ui_settings)

        self.json_combo = QComboBox()
        self.json_combo.addItem("(none)")
        self.json_combo.setFixedWidth(150)

        req_row.addWidget(self.endpoint_combo, 1)
        req_row.addWidget(self.json_type_combo)
        req_row.addWidget(self.json_combo)

        outer.addLayout(req_row)
        outer.addSpacing(16)

        # ===== Action Buttons =====
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.btn_send = QPushButton("Send")
        self.btn_send.setFixedWidth(100)
        self.btn_send.clicked.connect(self.send_request)

        self.btn_multi = QPushButton("Run Multiple")
        self.btn_multi.setObjectName("secondary")
        self.btn_multi.setFixedWidth(100)
        self.btn_multi.clicked.connect(self.run_multiple)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("secondary")
        self.btn_cancel.setFixedWidth(80)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_all_requests)

        action_row.addWidget(self.btn_send)
        action_row.addWidget(self.btn_multi)
        action_row.addStretch()
        action_row.addWidget(self.btn_cancel)

        outer.addLayout(action_row)
        outer.addSpacing(16)

        # ===== Response =====
        resp_header = QHBoxLayout()
        resp_label = QLabel("Response")
        resp_label.setObjectName("section")
        resp_header.addWidget(resp_label)
        resp_header.addStretch()

        btn_clear = QPushButton("Clear")
        btn_clear.setObjectName("secondary")
        btn_clear.setFixedWidth(60)
        btn_clear.clicked.connect(self.clear_response)
        resp_header.addWidget(btn_clear)

        outer.addLayout(resp_header)

        self.response = QTextEdit(readOnly=True)
        self.response.setFont(QFont("SF Mono", 10))
        self.response.setLineWrapMode(QTextEdit.NoWrap)
        self.response.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        outer.addWidget(self.response, 1)

        # Store status reference for updates
        self.status = self.status_label
