import json
from dialogs import MultiSelectDialog
from PySide6.QtWidgets import *
from PySide6.QtGui import QFont, QTextCursor, QPalette, QColor, QIcon
from constants import *
from presets import PresetManager
from requests_manager import RequestManager

class VapixApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VAPIX Test Tool")
        self.setWindowIcon(QIcon(resource_path("vapix_icon.ico")))
        self.resize(1200, 720)

        # ---------------- Managers ----------------
        self.presets = PresetManager()
        self.requests = RequestManager()

        # ---------------- Theme ----------------
        self.apply_light_theme()

        # ---------------- Build UI ----------------
        self.build_ui()

        # ---------------- Initial Preset List ----------------
        self.update_presets_list()  # populate combo boxes with presets

    # ---------------- Light Theme ----------------
    def apply_light_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#f4f4f4"))
        palette.setColor(QPalette.Base, QColor("#ffffff"))
        palette.setColor(QPalette.Button, QColor("#e0e0e0"))
        palette.setColor(QPalette.ButtonText, QColor("#000000"))
        palette.setColor(QPalette.Highlight, QColor("#4ca3e0"))
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        QApplication.setPalette(palette)

        self.setStyleSheet("""
            QPushButton {
                border-radius: 6px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #4ca3e0;
                color: #ffffff;
            }
            QGroupBox {
                border: 1px solid #4ca3e0;
                border-radius: 6px;
                margin-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)

    # ---------------- Build UI ----------------
    def build_ui(self):
        outer = QVBoxLayout(self)
        top_layout = QHBoxLayout()

        # ---------------- Left Panel ----------------
        left_group = QGroupBox("Presets && Request Setup")
        left_form = QFormLayout(left_group)

        # Preset selection
        self.preset_combo = QComboBox()
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)

        self.preset_search = QLineEdit()
        self.preset_search.setPlaceholderText("Search preset...")
        self.preset_search.textChanged.connect(self.update_presets_list)

        # Test mode
        self.test_mode_combo = QComboBox()
        self.test_mode_combo.addItems(["happy", "unhappy"])
        self.test_mode_combo.currentTextChanged.connect(self.update_presets_list)

        # Endpoint
        self.endpoint_combo = QComboBox()
        self.endpoint_combo.addItems(VAPIX_ENDPOINTS)

        # JSON
        self.json_combo = QComboBox()
        self.json_combo.addItem("(none)")

        self.json_type_combo = QComboBox()
        self.json_type_combo.addItems(["normal", "google", "rpc"])

        # Load/Save buttons
        btn_load = QPushButton("Load")
        btn_save = QPushButton("Save")
        btn_load.clicked.connect(self.load_preset)
        btn_save.clicked.connect(self.save_preset)
        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_load)
        btn_row.addWidget(btn_save)

        # Add to left form layout
        left_form.addRow("Test Mode:", self.test_mode_combo)
        left_form.addRow("Search:", self.preset_search)
        left_form.addRow("Preset:", self.preset_combo)
        left_form.addRow("", btn_row)
        left_form.addRow("Endpoint:", self.endpoint_combo)
        left_form.addRow("JSON Config:", self.json_combo)
        left_form.addRow("JSON Type:", self.json_type_combo)

        top_layout.addWidget(left_group, 1)

        # ---------------- Right Panel ----------------
        right_group = QGroupBox("Device Connection")
        right_form = QFormLayout(right_group)

        self.ip_edit = QLineEdit()
        self.user_edit = QLineEdit("admin")
        self.pass_edit = QLineEdit("Test1234")
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.simple_check = QCheckBox("Use format=simple")

        right_form.addRow("Device IP:", self.ip_edit)
        right_form.addRow("Username:", self.user_edit)
        right_form.addRow("Password:", self.pass_edit)
        right_form.addRow("", self.simple_check)

        top_layout.addWidget(right_group, 1)

        # ---------------- Buttons Bar ----------------
        btn_bar = QHBoxLayout()
        self.btn_send = QPushButton("SEND REQUEST")
        self.btn_multi = QPushButton("RUN MULTIPLE PRESETS")
        self.btn_clear = QPushButton("CLEAR RESPONSES")

        self.btn_send.clicked.connect(self.send_request)
        self.btn_multi.clicked.connect(self.run_multiple)
        self.btn_clear.clicked.connect(self.clear_response)

        btn_bar.addWidget(self.btn_send)
        btn_bar.addWidget(self.btn_multi)
        btn_bar.addWidget(self.btn_clear)

        # ---------------- Response Area ----------------
        self.response = QTextEdit()
        self.response.setReadOnly(True)
        self.response.setFont(QFont("Consolas", 10))
        self.response.setLineWrapMode(QTextEdit.NoWrap)

        # ---------------- Status Bar ----------------
        self.status = QStatusBar()
        self.status.showMessage("Ready")

        # ---------------- Assemble Layout ----------------
        outer.addLayout(top_layout)
        outer.addLayout(btn_bar)
        outer.addWidget(self.response, 1)
        outer.addWidget(self.status)


    def update_presets_list(self):
        """Filter presets by current test mode and search text, update both combo boxes."""
        search_text = self.preset_search.text().lower()
        mode = self.test_mode_combo.currentText().lower()  # 'happy' or 'unhappy'

        self.preset_combo.clear()
        self.json_combo.clear()
        self.json_combo.addItem("(none)")

        for preset in self.presets.presets:
            name = preset.get("name", "")
            json_file = preset.get("json_file", "")

            if not json_file:
                continue

            # Normalize path to detect unhappy folder
            json_file_norm = json_file.replace("\\", "/").lower()
            is_unhappy = "/unhappy/" in json_file_norm

            # Apply mode filter
            if (mode == "happy" and is_unhappy) or (mode == "unhappy" and not is_unhappy):
                continue

            # Apply search filter
            if search_text in name.lower():
                self.preset_combo.addItem(name)
                self.json_combo.addItem(json_file)

        # Automatically select first preset if available
        if self.preset_combo.count() > 0:
            self.preset_combo.setCurrentIndex(0)
            self.on_preset_changed(self.preset_combo.currentText())

    def on_preset_changed(self, name):
        preset = self.presets.get_by_name(name)
        if not preset:
            return

        json_file = preset.get("json_file", "(none)")

        # Rebuild JSON combo so it always matches preset
        self.json_combo.clear()
        self.json_combo.addItem("(none)")

        if json_file and json_file != "(none)":
            self.json_combo.addItem(json_file)
            self.json_combo.setCurrentText(json_file)


    # ---------------- Filter Presets / JSON ----------------
    def filter_presets_by_mode(self):
        mode = self.test_mode_combo.currentText().lower()  # happy / unhappy
        self.preset_combo.clear()
        self.json_combo.clear()
        self.json_combo.addItem("(none)")

        for preset in self.presets.presets:
            json_file = preset.get("json_file", "")
            if not json_file or json_file == "(none)":
                continue

            # Normalize path separators
            json_file_norm = json_file.replace("\\", "/").lower()

            # Check if it is unhappy
            is_unhappy = "/unhappy/" in json_file_norm

            if (mode == "happy" and not is_unhappy) or (mode == "unhappy" and is_unhappy):
                self.preset_combo.addItem(preset["name"])
                self.json_combo.addItem(json_file)

        # After filtering by mode, apply search filter if any
        self.filter_presets(self.preset_search.text())

    def filter_presets(self, text):
        text = text.lower()

        # Reset UI lists
        self.preset_combo.clear()
        self.json_combo.clear()
        self.json_combo.addItem("(none)")

        # Current mode: happy / unhappy
        mode = self.test_mode_combo.currentText().lower()

        for preset in self.presets.presets:
            name = preset.get("name", "")
            json_file = preset.get("json_file", "")

            if not json_file:
                continue

            # Normalize path to detect unhappy folder
            json_file_norm = json_file.replace("\\", "/").lower()
            is_unhappy = "/unhappy/" in json_file_norm

            # Apply mode filter
            if mode == "happy" and is_unhappy:
                continue
            if mode == "unhappy" and not is_unhappy:
                continue

            # Apply text search
            if text in name.lower():
                self.preset_combo.addItem(name)
                self.json_combo.addItem(json_file)
    # ---------------- Display Response ----------------
    def display_response(self, text, preset_name, tag):
        try:
            if "{" in text:
                idx = text.index("{")
                obj = json.loads(text[idx:])
                pretty = json.dumps(obj, indent=2)
                text = text[:idx] + pretty
        except Exception:
            pass

        text_html = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        html = (
            f'<div style="padding:4px; margin:2px; font-family:Consolas; white-space:pre;">'
            f'{text_html}'
            f'</div>'
            '<pre style="font-family:Consolas; color:#888; margin:8px 4px;">'
            '----------------------------------------\n\n'
            '</pre>'
        )
        self.response.moveCursor(QTextCursor.End)
        self.response.insertHtml(html)
        self.response.moveCursor(QTextCursor.End)

    def clear_response(self):
        self.response.clear()

    # ---------------- Requests ----------------
    def send_request(self):
        ip = self.ip_edit.text().strip()
        if not ip:
            QMessageBox.warning(self, "Error", "Device IP required")
            return

        endpoint = self.endpoint_combo.currentText()
        json_file = self.json_combo.currentText()
        json_type = self.json_type_combo.currentText()
        use_simple = self.simple_check.isChecked()

        self.status.showMessage(f"Sending request...")

        def on_response(text, preset_name, tag):
            self.display_response(text, preset_name, tag)
            self.status.showMessage("Request finished")

        self.requests.send_request_async(
            ip,
            self.user_edit.text(),
            self.pass_edit.text(),
            endpoint,
            json_file,
            use_simple,
            json_type,
            on_response,
            preset_name=endpoint
        )

    # ---------------- Presets ----------------
    def save_preset(self):
        name, ok = QInputDialog.getText(self, "Preset Name", "Enter preset name:")
        if not ok or not name:
            return
        preset = {
            "name": name,
            "endpoint": self.endpoint_combo.currentText(),
            "json_file": self.json_combo.currentText(),
            "simple_format": self.simple_check.isChecked(),
            "json_type": self.json_type_combo.currentText()
        }
        self.presets.add_preset(preset)
        self.filter_presets_by_mode()

    def load_preset(self):
        name = self.preset_combo.currentText().strip()
        if not name:
            QMessageBox.warning(self, "Error", "No preset selected")
            return

        preset = self.presets.get_by_name(name)
        if not preset:
            QMessageBox.warning(self, "Error", f"Preset '{name}' not found")
            return

        if self.endpoint_combo.findText(preset["endpoint"]) == -1:
            self.endpoint_combo.addItem(preset["endpoint"])
        self.endpoint_combo.setCurrentText(preset["endpoint"])

        json_file = preset.get("json_file", "(none)")
        if self.json_combo.findText(json_file) == -1:
            self.json_combo.addItem(json_file)
        self.json_combo.setCurrentText (json_file)

        json_type = preset.get("json_type", "normal")
        if self.json_type_combo.findText(json_type) == -1:
            self.json_type_combo.addItem(json_type)
        self.json_type_combo.setCurrentText(json_type)

        self.status.showMessage(f"Preset '{name}' loaded")

    # ---------------- Multi-Preset ----------------
    def run_multiple(self):
        if not self.presets.presets:
            QMessageBox.warning(self, "Error", "No presets saved")
            return

        dlg = MultiSelectDialog([self.preset_combo.itemText(i) for i in range(self.preset_combo.count())])
        if not dlg.exec():
            return

        selected = dlg.selected
        if not selected:
            QMessageBox.information(self, "Info", "No presets selected")
            return

        ip = self.ip_edit.text().strip()
        if not ip:
            QMessageBox.warning(self, "Error", "Device IP required")
            return

        self.status.showMessage("Running multiple presets...")
        log_file = self.requests.start_new_log("MultiPreset_Run")

        def run_next(i=0):
            if i >= len(selected):
                self.status.showMessage("All presets finished")
                return

            preset = self.presets.get_by_name(selected[i])

            def on_response(text, preset_name, tag):
                self.display_response(text, preset_name, tag)
                self.status.showMessage(f"Finished preset {preset_name} ({i+1}/{len(selected)})")
                run_next(i+1)

            use_simple = self.simple_check.isChecked()

            self.requests.send_request_async(
                ip,
                self.user_edit.text(),
                self.pass_edit.text(),
                preset["endpoint"],
                preset["json_file"],
                use_simple,
                preset["json_type"],
                on_response,
                preset_name=selected[i],
                log_file=log_file
            )

        run_next()
