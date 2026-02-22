from __future__ import annotations

import json
from typing import Any
import ipaddress

from PySide6.QtGui import QFont, QTextCursor, QPalette, QColor, QIcon
from PySide6.QtWidgets import *

from constants import *
from dialogs import MultiSelectDialog
from requests_manager import RequestManager, RequestWorker
from settings import SettingsManager
from di_container import DIContainer, PresetManagerProtocol, RequestManagerProtocol, SettingsManagerProtocol
from logging_system import get_logger, set_logging_level



class ApiTestApp(QWidget):
    # ================= Init =================

    def __init__(self, 
                 preset_manager: PresetManagerProtocol | None = None,
                 request_manager: RequestManagerProtocol | None = None,
                 settings_manager: SettingsManagerProtocol | None = None,
                 container: DIContainer | None = None) -> None:
        super().__init__()

        # Use dependency injection or create defaults
        if container:
            self.container = container
            self.presets = preset_manager or container.get("preset_manager")
            self.requests = request_manager or container.get("request_manager")
            self.settings = settings_manager or container.get("settings_manager")
        else:
            # Fallback to direct instantiation for backward compatibility
            from presets import PresetManager
            from requests_manager import RequestManager
            from settings import SettingsManager
            
            self.presets = preset_manager or PresetManager()
            self.requests = request_manager or RequestManager()
            self.settings = settings_manager or SettingsManager()
            self.container = None

        # Initialize logging
        self.logger = get_logger("api_test_app")
        self.logger.log_application_event("application_started", 
                                         window_geometry="1200x720",
                                         python_version=sys.version)

        self.setWindowTitle("API Test Tool")
        self.setWindowIcon(QIcon(resource_path("api_tester_icon.ico")))
        self.resize(1200, 720)

        # Request tracking
        self.active_requests: list[RequestWorker] = []
        self.current_request_count = 0
        self.total_request_count = 0

        # Theme + UI
        self.apply_light_theme()
        self.build_ui()
        self.load_settings()
        self.update_presets_list()
        
        # Connect window geometry auto-save
        self._setup_geometry_auto_save()

    # ================= Theme =================

    def apply_light_theme(self) -> None:
        palette = QPalette()
        # Modern color palette
        palette.setColor(QPalette.Window, QColor("#ffffff"))
        palette.setColor(QPalette.Base, QColor("#ffffff"))
        palette.setColor(QPalette.AlternateBase, QColor("#f8f9fa"))
        palette.setColor(QPalette.Button, QColor("#0078d4"))
        palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
        palette.setColor(QPalette.Highlight, QColor("#0078d4"))
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        palette.setColor(QPalette.Text, QColor("#323130"))
        palette.setColor(QPalette.WindowText, QColor("#323130"))
        QApplication.setPalette(palette)

        # Modern styling with better visual hierarchy
        self.setStyleSheet(
            """
            /* Main window styling */
            QWidget {
                background-color: #ffffff;
                color: #323130;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            
            /* Button styling */
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                min-height: 32px;
            }
            
            QPushButton:hover {
                background-color: #106ebe;
            }
            
            QPushButton:pressed {
                background-color: #005a9e;
            }
            
            QPushButton:disabled {
                background-color: #f3f2f1;
                color: #a19f9d;
            }
            
            /* Special button styling */
            QPushButton#dangerButton {
                background-color: #d13438;
            }
            
            QPushButton#dangerButton:hover {
                background-color: #a4262c;
            }
            
            QPushButton#secondaryButton {
                background-color: #f3f2f1;
                color: #323130;
                border: 1px solid #d2d0ce;
            }
            
            QPushButton#secondaryButton:hover {
                background-color: #edebe9;
            }
            
            /* GroupBox styling */
            QGroupBox {
                border: 1px solid #d2d0ce;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: #faf9f8;
                font-weight: 600;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #323130;
            }
            
            /* Input field styling */
            QLineEdit, QComboBox, QTextEdit {
                border: 1px solid #d2d0ce;
                border-radius: 4px;
                padding: 6px 8px;
                background-color: #ffffff;
                selection-background-color: #0078d4;
            }
            
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
                border: 2px solid #0078d4;
                outline: none;
            }
            
            /* ComboBox styling */
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #605e5c;
                margin-right: 4px;
            }
            
            /* CheckBox styling */
            QCheckBox {
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #d2d0ce;
                border-radius: 3px;
                background-color: #ffffff;
            }
            
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #0078d4;
                image: none;
            }
            
            QCheckBox::indicator:checked::after {
                content: '✓';
                color: white;
                font-size: 10px;
            }
            
            /* Status bar styling */
            QStatusBar {
                background-color: #f3f2f1;
                border-top: 1px solid #d2d0ce;
                color: #323130;
            }
            """
        )

    # ================= UI =================

    def build_ui(self) -> None:
        outer = QVBoxLayout(self)
        top_layout = QHBoxLayout()

        # ----- Left panel -----
        left_group = QGroupBox("⚙️ Presets && Request Setup")
        left_form = QFormLayout(left_group)
        left_form.setSpacing(8)
        left_form.setContentsMargins(16, 20, 16, 16)

        self.preset_combo = QComboBox()
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)

        self.preset_search = QLineEdit()
        self.preset_search.setPlaceholderText("🔍 Search preset...")
        self.preset_search.textChanged.connect(self.update_presets_list)

        self.test_mode_combo = QComboBox()
        self.test_mode_combo.addItems(["happy", "unhappy"])
        self.test_mode_combo.currentTextChanged.connect(self.update_presets_list)
        self.test_mode_combo.currentTextChanged.connect(self._auto_save_ui_settings)

        self.endpoint_combo = QComboBox()
        self.endpoint_combo.addItems(API_ENDPOINTS)
        self.endpoint_combo.currentTextChanged.connect(self._auto_save_ui_settings)

        self.json_combo = QComboBox()
        self.json_combo.addItem("(none)")

        self.json_type_combo = QComboBox()
        self.json_type_combo.addItems(["normal", "google", "rpc"])
        self.json_type_combo.currentTextChanged.connect(self._auto_save_ui_settings)

        btn_load = QPushButton("📂 Load")
        btn_save = QPushButton("💾 Save")
        btn_load.clicked.connect(self.load_preset)
        btn_save.clicked.connect(self.save_preset)
        btn_load.setObjectName("secondaryButton")
        btn_save.setObjectName("secondaryButton")

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addWidget(btn_load)
        btn_row.addWidget(btn_save)

        left_form.addRow("🧪 Test Mode:", self.test_mode_combo)
        left_form.addRow("🔍 Search:", self.preset_search)
        left_form.addRow("📋 Preset:", self.preset_combo)
        left_form.addRow("", btn_row)
        left_form.addRow("🌐 Endpoint:", self.endpoint_combo)
        left_form.addRow("📄 JSON Config:", self.json_combo)
        left_form.addRow("🔧 JSON Type:", self.json_type_combo)

        top_layout.addWidget(left_group, 1)

        # ----- Right panel -----
        right_group = QGroupBox("🖥️ Device Connection")
        right_form = QFormLayout(right_group)
        right_form.setSpacing(8)
        right_form.setContentsMargins(16, 20, 16, 16)

        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("192.168.1.100")
        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("username")
        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("password")
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.simple_check = QCheckBox("Use format=simple")
        
        # Connect auto-save for connection settings
        self.ip_edit.textChanged.connect(self._auto_save_connection_settings)
        self.user_edit.textChanged.connect(self._auto_save_connection_settings)
        self.simple_check.toggled.connect(self._auto_save_connection_settings)

        right_form.addRow("🌍 Device IP:", self.ip_edit)
        right_form.addRow("👤 Username:", self.user_edit)
        right_form.addRow("🔐 Password:", self.pass_edit)
        right_form.addRow("", self.simple_check)

        top_layout.addWidget(right_group, 1)

        # ----- Buttons -----
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(12)
        btn_bar.setContentsMargins(0, 16, 0, 16)

        self.btn_send = QPushButton("📡 SEND REQUEST")
        self.btn_multi = QPushButton("🚀 RUN MULTIPLE PRESETS")
        self.btn_clear = QPushButton("🗑️ CLEAR RESPONSES")
        self.btn_cancel = QPushButton("❌ CANCEL ALL")
        
        # Set button IDs for styling
        self.btn_clear.setObjectName("secondaryButton")
        self.btn_cancel.setObjectName("dangerButton")
        
        # Set button sizes for better visual hierarchy
        self.btn_send.setMinimumWidth(180)
        self.btn_multi.setMinimumWidth(220)
        self.btn_clear.setMinimumWidth(160)
        self.btn_cancel.setMinimumWidth(140)
        
        # Initially disable cancel button
        self.btn_cancel.setEnabled(False)

        self.btn_send.clicked.connect(self.send_request)
        self.btn_multi.clicked.connect(self.run_multiple)
        self.btn_clear.clicked.connect(self.clear_response)
        self.btn_cancel.clicked.connect(self.cancel_all_requests)

        btn_bar.addWidget(self.btn_send)
        btn_bar.addWidget(self.btn_multi)
        btn_bar.addStretch()
        btn_bar.addWidget(self.btn_clear)
        btn_bar.addWidget(self.btn_cancel)

        # ----- Response -----
        response_group = QGroupBox("📋 API Response")
        response_layout = QVBoxLayout(response_group)
        
        self.response = QTextEdit(readOnly=True)
        self.response.setFont(QFont("Consolas", 10))
        self.response.setLineWrapMode(QTextEdit.NoWrap)
        self.response.setMinimumHeight(200)
        
        response_layout.addWidget(self.response)

        # ----- Status -----
        status_group = QGroupBox("📊 Status")
        status_layout = QHBoxLayout(status_group)
        status_layout.setContentsMargins(12, 8, 12, 8)
        
        self.status = QStatusBar()
        self.status.showMessage("🚀 Ready to test APIs")
        self.status.setStyleSheet("""
            QStatusBar {
                background-color: #f8f9fa;
                border: none;
                color: #5f6368;
                font-weight: 500;
            }
        """)
        
        status_layout.addWidget(self.status)

        outer.addLayout(top_layout)
        outer.addLayout(btn_bar)
        outer.addWidget(response_group, 1)
        outer.addWidget(status_group)

    # ================= Preset filtering =================

    def _preset_matches(self, preset: dict[str, Any], mode: str, search: str) -> bool:
        name = preset.get("name", "")
        json_file = preset.get("json_file", "")
        if not json_file:
            return False

        is_unhappy = "/unhappy/" in json_file.replace("\\", "/").lower()

        if (mode == "happy" and is_unhappy) or (mode == "unhappy" and not is_unhappy):
            return False

        return search in name.lower()

    def update_presets_list(self) -> None:
        search = self.preset_search.text().lower()
        mode = self.test_mode_combo.currentText().lower()

        self.preset_combo.clear()
        self.json_combo.clear()
        self.json_combo.addItem("(none)")

        for preset in self.presets.presets:
            if self._preset_matches(preset, mode, search):
                self.preset_combo.addItem(preset["name"])
                self.json_combo.addItem(preset["json_file"])

        if self.preset_combo.count():
            self.preset_combo.setCurrentIndex(0)
            self.on_preset_changed(self.preset_combo.currentText())

    def on_preset_changed(self, name: str) -> None:
        preset = self.presets.get_by_name(name)
        if not preset:
            return

        self.json_combo.clear()
        self.json_combo.addItem("(none)")

        json_file = preset.get("json_file")
        if json_file and json_file != "(none)":
            self.json_combo.addItem(json_file)
            self.json_combo.setCurrentText(json_file)

    # ================= Response =================

    def display_response(self, text: str, preset_name: str, tag: str) -> None:
        try:
            if "{" in text:
                idx = text.index("{")
                obj = json.loads(text[idx:])
                formatted_json = json.dumps(obj, indent=2, ensure_ascii=False)
                text = text[:idx] + formatted_json
        except Exception:
            pass

        # Determine background color based on response tag
        bg_colors = {
            "ok": "#e6f4ea",      # Green for success
            "warn": "#fef7e0",    # Yellow for warnings  
            "err": "#fce8e6"       # Red for errors
        }
        bg_color = bg_colors.get(tag, "#f8f9fa")
        
        # Create styled HTML response
        html = f'''
        <div style="
            background-color: {bg_color};
            border-left: 4px solid {'#34a853' if tag == 'ok' else '#fbbc04' if tag == 'warn' else '#ea4335'};
            margin: 8px 0;
            padding: 12px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            white-space: pre-wrap;
            word-wrap: break-word;
        ">
            <div style="
                font-weight: bold; 
                color: #202124; 
                margin-bottom: 8px;
                font-size: 13px;
            ">
                📡 {preset_name or 'Request'} - {tag.upper()}
            </div>
            <div style="color: #5f6368; line-height: 1.4;">
                {text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")}
            </div>
        </div>
        '''
        
        self.response.moveCursor(QTextCursor.End)
        self.response.insertHtml(html)
        self.response.moveCursor(QTextCursor.End)

    def clear_response(self) -> None:
        self.response.clear()

    # ================= Request Management =================

    def cancel_all_requests(self) -> None:
        """Cancel all active requests."""
        if not self.active_requests:
            return
        
        for worker in self.active_requests:
            worker.terminate()
            worker.wait()  # Wait for thread to finish
        
        self.active_requests.clear()
        self.current_request_count = 0
        self.total_request_count = 0
        
        self.btn_cancel.setEnabled(False)
        self.status.showMessage("❌ All requests cancelled")

    def _track_request(self, worker: RequestWorker) -> None:
        """Track a new request worker."""
        self.active_requests.append(worker)
        self.current_request_count += 1
        
        # Enable cancel button when there are active requests
        if len(self.active_requests) == 1:
            self.btn_cancel.setEnabled(True)

    def _untrack_request(self, worker: RequestWorker) -> None:
        """Remove completed request worker from tracking."""
        if worker in self.active_requests:
            self.active_requests.remove(worker)
        
        # Disable cancel button when no active requests
        if not self.active_requests:
            self.btn_cancel.setEnabled(False)
            self.current_request_count = 0
            self.total_request_count = 0

    def _update_progress(self, completed: int, total: int) -> None:
        """Update progress display."""
        if total > 1:  # Only show progress for multiple requests
            self.status.showMessage(f"⏳ Progress: {completed}/{total} requests")

    # ================= Settings Management =================

    def load_settings(self) -> None:
        """Load saved settings and apply them to UI."""
        # Connection settings
        self.ip_edit.setText(self.settings.get_last_ip())
        self.user_edit.setText(self.settings.get_last_user())
        self.simple_check.setChecked(self.settings.get_last_simple_format())
        
        # UI settings
        self.test_mode_combo.setCurrentText(self.settings.get_last_test_mode())
        self.json_type_combo.setCurrentText(self.settings.get_last_json_type())
        
        # Preset settings
        last_endpoint = self.settings.get_last_endpoint()
        if last_endpoint:
            index = self.endpoint_combo.findText(last_endpoint)
            if index >= 0:
                self.endpoint_combo.setCurrentIndex(index)
        
        # Window geometry (restore after UI is built)
        geometry = self.settings.get_window_geometry()
        if geometry:
            self.restoreGeometry(bytes.fromhex(geometry))
        
        # Note: Window state restoration would need QMainWindow for dock widgets

    def save_settings(self) -> None:
        """Save current UI state to settings."""
        # Connection settings
        self.settings.set_last_ip(self.ip_edit.text())
        self.settings.set_last_user(self.user_edit.text())
        self.settings.set_last_simple_format(self.simple_check.isChecked())
        
        # UI settings
        self.settings.set_last_test_mode(self.test_mode_combo.currentText())
        self.settings.set_last_json_type(self.json_type_combo.currentText())
        self.settings.set_last_endpoint(self.endpoint_combo.currentText())
        self.settings.set_last_json_file(self.json_combo.currentText())
        
        # Window geometry (also auto-saved on changes)
        geometry = self.saveGeometry().data().hex()
        self.settings.set_window_geometry(geometry)
        
        # Save to file
        self.settings.save_settings()

    def closeEvent(self, event) -> None:
        """Handle application close event - save settings."""
        self.save_settings()
        # Cancel any active requests
        if self.active_requests:
            self.cancel_all_requests()
        super().closeEvent(event)

    def _auto_save_connection_settings(self) -> None:
        """Auto-save connection settings when they change."""
        self.settings.set_last_ip(self.ip_edit.text())
        self.settings.set_last_user(self.user_edit.text())
        self.settings.set_last_simple_format(self.simple_check.isChecked())
        self.settings.save_settings()

    def _auto_save_ui_settings(self) -> None:
        """Auto-save UI settings when they change."""
        self.settings.set_last_test_mode(self.test_mode_combo.currentText())
        self.settings.set_last_json_type(self.json_type_combo.currentText())
        self.settings.set_last_endpoint(self.endpoint_combo.currentText())
        self.settings.set_last_json_file(self.json_combo.currentText())
        self.settings.save_settings()

    def _setup_geometry_auto_save(self) -> None:
        """Setup auto-save for window geometry changes."""
        # Use a timer to debounce rapid geometry changes
        from PySide6.QtCore import QTimer
        
        self._geometry_timer = QTimer()
        self._geometry_timer.setSingleShot(True)
        self._geometry_timer.timeout.connect(self._auto_save_geometry)
        
        # Connect to geometry change signals
        # Note: QWidget doesn't have direct geometry change signals
        # We'll save on close and periodically during use

    def _auto_save_geometry(self) -> None:
        """Auto-save window geometry."""
        geometry = self.saveGeometry().data().hex()
        self.settings.set_window_geometry(geometry)
        self.settings.save_settings()

    # ================= Requests =================

    def _validate_ip(self, ip: str) -> bool:
        """Validate IP address format."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def send_request(self) -> None:
        ip = self.ip_edit.text().strip()
        if not ip:
            self.logger.log_user_action("send_request_failed", reason="no_ip")
            QMessageBox.warning(self, "Error", "Device IP required")
            return

        # Validate IP format
        if not self._validate_ip(ip):
            self.logger.log_user_action("send_request_failed", reason="invalid_ip", ip=ip)
            QMessageBox.warning(self, "Error", "Invalid IP address format")
            return

        # Check if username is provided for authentication
        if not self.user_edit.text().strip():
            self.logger.log_user_action("send_request_failed", reason="no_username")
            QMessageBox.warning(self, "Error", "Username required for authentication")
            return

        # Log request start
        endpoint = self.endpoint_combo.currentText()
        self.logger.log_user_action("send_request_started", 
                                   ip=ip, 
                                   endpoint=endpoint,
                                   json_file=self.json_combo.currentText())

        self.status.showMessage("📡 Sending request...")

        def on_response(text: str, preset_name: str, tag: str) -> None:
            self.display_response(text, preset_name, tag)
            self.status.showMessage("✅ Request finished successfully")
            self.logger.log_request("POST", f"http://{ip}{endpoint}", 
                                   200 if tag == "ok" else 400, 0.0,
                                   preset_name=preset_name, response_tag=tag)

        try:
            worker = self.requests.send_request_async(
                ip,
                self.user_edit.text(),
                self.pass_edit.text(),
                endpoint,
                self.json_combo.currentText(),
                self.simple_check.isChecked(),
                self.json_type_combo.currentText(),
                on_response,
                preset_name=self.endpoint_combo.currentText(),
            )
            
            # Track the request for cancellation
            self._track_request(worker)
            
            # Handle request completion
            def on_finished():
                self._untrack_request(worker)
            
            worker.finished.connect(on_finished)
            
        except Exception as e:
            self.logger.exception("Failed to send request", ip=ip, endpoint=endpoint)
            QMessageBox.critical(self, "Error", f"Failed to send request: {str(e)}")
            self.status.showMessage("❌ Request failed")

    # ================= Presets =================

    def save_preset(self) -> None:
        name, ok = QInputDialog.getText(self, "Preset Name", "Enter preset name:")
        if not ok or not name:
            self.logger.log_user_action("save_preset_cancelled")
            return

        self.logger.log_preset_action("save_started", name)

        self.presets.add_preset(
            {
                "name": name,
                "endpoint": self.endpoint_combo.currentText(),
                "json_file": self.json_combo.currentText(),
                "simple_format": self.simple_check.isChecked(),
                "json_type": self.json_type_combo.currentText(),
            }
        )

        self.update_presets_list()
        self.logger.log_preset_action("save_completed", name,
                                     endpoint=self.endpoint_combo.currentText(),
                                     json_file=self.json_combo.currentText())

    def load_preset(self) -> None:
        name = self.preset_combo.currentText().strip()
        if not name:
            self.logger.log_user_action("load_preset_failed", reason="no_selection")
            QMessageBox.warning(self, "Error", "No preset selected")
            return

        self.logger.log_preset_action("load_started", name)

        preset = self.presets.get_by_name(name)
        if not preset:
            self.logger.log_preset_action("load_failed", name, reason="not_found")
            QMessageBox.warning(self, "Error", f"Preset '{name}' not found")
            return

        self.endpoint_combo.setCurrentText(preset["endpoint"])
        self.json_combo.setCurrentText(preset.get("json_file", "(none)"))
        self.json_type_combo.setCurrentText(preset.get("json_type", "normal"))

        self.status.showMessage(f"📋 Preset '{name}' loaded successfully")
        self.logger.log_preset_action("load_completed", name,
                                     endpoint=preset["endpoint"],
                                     json_file=preset.get("json_file", "(none)"))

    # ================= Multi run =================

    def run_multiple(self) -> None:
        names = [self.preset_combo.itemText(i) for i in range(self.preset_combo.count())]
        if not names:
            QMessageBox.warning(self, "Error", "No presets available")
            return

        dlg = MultiSelectDialog(names)
        if not dlg.exec() or not dlg.selected:
            return

        ip = self.ip_edit.text().strip()
        if not ip:
            QMessageBox.warning(self, "Error", "Device IP required")
            return

        # Validate IP format
        if not self._validate_ip(ip):
            QMessageBox.warning(self, "Error", "Invalid IP address format")
            return

        # Check if username is provided for authentication
        if not self.user_edit.text().strip():
            QMessageBox.warning(self, "Error", "Username required for authentication")
            return

        # Initialize progress tracking
        self.total_request_count = len(dlg.selected)
        self.current_request_count = 0
        
        self.status.showMessage(f"🚀 Running {self.total_request_count} presets...")
        
        try:
            log_file = self.requests.start_new_log("MultiPreset_Run")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create log file: {str(e)}")
            return

        def run_next(i: int = 0) -> None:
            if i >= len(dlg.selected):
                self.status.showMessage(f"✅ All presets finished")
                return

            # Update progress
            self.current_request_count = i + 1
            self._update_progress(self.current_request_count, self.total_request_count)

            preset = self.presets.get_by_name(dlg.selected[i])
            if not preset:
                self.status.showMessage(f"⚠️ Skipping invalid preset: {dlg.selected[i]}")
                run_next(i + 1)
                return

            def on_response(text: str, preset_name: str, tag: str) -> None:
                self.display_response(text, preset_name, tag)
                # Update progress after response
                self._update_progress(self.current_request_count, self.total_request_count)
                run_next(i + 1)

            try:
                worker = self.requests.send_request_async(
                    ip,
                    self.user_edit.text(),
                    self.pass_edit.text(),
                    preset["endpoint"],
                    preset["json_file"],
                    self.simple_check.isChecked(),
                    preset["json_type"],
                    on_response,
                    preset_name=dlg.selected[i],
                    log_file=log_file,
                )
                
                # Track the request
                self._track_request(worker)
                
                # Handle completion
                def on_finished():
                    self._untrack_request(worker)
                
                worker.finished.connect(on_finished)
                
            except Exception as e:
                self.status.showMessage(f"❌ Failed to send {dlg.selected[i]}: {str(e)}")
                run_next(i + 1)

        run_next()
