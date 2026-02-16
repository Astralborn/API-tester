from __future__ import annotations

import json
from typing import Any

from PySide6.QtGui import QFont, QTextCursor, QPalette, QColor, QIcon
from PySide6.QtWidgets import *

from constants import *
from dialogs import MultiSelectDialog
from presets import PresetManager
from requests_manager import RequestManager


class VapixApp(QWidget):
    # ================= Init =================

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("VAPIX Test Tool")
        self.setWindowIcon(QIcon(resource_path("vapix_icon.ico")))
        self.resize(1200, 720)

        # Managers
        self.presets = PresetManager()
        self.requests = RequestManager()

        # Theme + UI
        self.apply_light_theme()
        self.build_ui()
        self.update_presets_list()

    # ================= Theme =================

    def apply_light_theme(self) -> None:
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#f4f4f4"))
        palette.setColor(QPalette.Base, QColor("#ffffff"))
        palette.setColor(QPalette.Button, QColor("#e0e0e0"))
        palette.setColor(QPalette.ButtonText, QColor("#000000"))
        palette.setColor(QPalette.Highlight, QColor("#4ca3e0"))
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        QApplication.setPalette(palette)

        self.setStyleSheet(
            """
            QPushButton { border-radius: 6px; padding: 4px 10px; }
            QPushButton:hover { background-color: #4ca3e0; color: #ffffff; }
            QGroupBox { border: 1px solid #4ca3e0; border-radius: 6px; margin-top: 6px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
            """
        )

    # ================= UI =================

    def build_ui(self) -> None:
        outer = QVBoxLayout(self)
        top_layout = QHBoxLayout()

        # ----- Left panel -----
        left_group = QGroupBox("Presets && Request Setup")
        left_form = QFormLayout(left_group)

        self.preset_combo = QComboBox()
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)

        self.preset_search = QLineEdit()
        self.preset_search.setPlaceholderText("Search preset...")
        self.preset_search.textChanged.connect(self.update_presets_list)

        self.test_mode_combo = QComboBox()
        self.test_mode_combo.addItems(["happy", "unhappy"])
        self.test_mode_combo.currentTextChanged.connect(self.update_presets_list)

        self.endpoint_combo = QComboBox()
        self.endpoint_combo.addItems(VAPIX_ENDPOINTS)

        self.json_combo = QComboBox()
        self.json_combo.addItem("(none)")

        self.json_type_combo = QComboBox()
        self.json_type_combo.addItems(["normal", "google", "rpc"])

        btn_load = QPushButton("Load")
        btn_save = QPushButton("Save")
        btn_load.clicked.connect(self.load_preset)
        btn_save.clicked.connect(self.save_preset)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_load)
        btn_row.addWidget(btn_save)

        left_form.addRow("Test Mode:", self.test_mode_combo)
        left_form.addRow("Search:", self.preset_search)
        left_form.addRow("Preset:", self.preset_combo)
        left_form.addRow("", btn_row)
        left_form.addRow("Endpoint:", self.endpoint_combo)
        left_form.addRow("JSON Config:", self.json_combo)
        left_form.addRow("JSON Type:", self.json_type_combo)

        top_layout.addWidget(left_group, 1)

        # ----- Right panel -----
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

        # ----- Buttons -----
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

        # ----- Response -----
        self.response = QTextEdit(readOnly=True)
        self.response.setFont(QFont("Consolas", 10))
        self.response.setLineWrapMode(QTextEdit.NoWrap)

        # ----- Status -----
        self.status = QStatusBar()
        self.status.showMessage("Ready")

        outer.addLayout(top_layout)
        outer.addLayout(btn_bar)
        outer.addWidget(self.response, 1)
        outer.addWidget(self.status)

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

    def display_response(self, text: str, _: str, __: str) -> None:
        try:
            if "{" in text:
                idx = text.index("{")
                obj = json.loads(text[idx:])
                text = text[:idx] + json.dumps(obj, indent=2)
        except Exception:
            pass

        html = (
            f'<div style="padding:4px;margin:2px;font-family:Consolas;white-space:pre;">'
            f'{text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")}'
            f"</div>"
            '<pre style="font-family:Consolas;color:#888;margin:8px 4px;">'
            "----------------------------------------\n\n</pre>"
        )

        self.response.moveCursor(QTextCursor.End)
        self.response.insertHtml(html)
        self.response.moveCursor(QTextCursor.End)

    def clear_response(self) -> None:
        self.response.clear()

    # ================= Requests =================

    def send_request(self) -> None:
        ip = self.ip_edit.text().strip()
        if not ip:
            QMessageBox.warning(self, "Error", "Device IP required")
            return

        self.status.showMessage("Sending request...")

        def on_response(text: str, preset_name: str, tag: str) -> None:
            self.display_response(text, preset_name, tag)
            self.status.showMessage("Request finished")

        self.requests.send_request_async(
            ip,
            self.user_edit.text(),
            self.pass_edit.text(),
            self.endpoint_combo.currentText(),
            self.json_combo.currentText(),
            self.simple_check.isChecked(),
            self.json_type_combo.currentText(),
            on_response,
            preset_name=self.endpoint_combo.currentText(),
        )

    # ================= Presets =================

    def save_preset(self) -> None:
        name, ok = QInputDialog.getText(self, "Preset Name", "Enter preset name:")
        if not ok or not name:
            return

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

    def load_preset(self) -> None:
        name = self.preset_combo.currentText().strip()
        if not name:
            QMessageBox.warning(self, "Error", "No preset selected")
            return

        preset = self.presets.get_by_name(name)
        if not preset:
            QMessageBox.warning(self, "Error", f"Preset '{name}' not found")
            return

        self.endpoint_combo.setCurrentText(preset["endpoint"])
        self.json_combo.setCurrentText(preset.get("json_file", "(none)"))
        self.json_type_combo.setCurrentText(preset.get("json_type", "normal"))

        self.status.showMessage(f"Preset '{name}' loaded")

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

        self.status.showMessage("Running multiple presets...")
        log_file = self.requests.start_new_log("MultiPreset_Run")

        def run_next(i: int = 0) -> None:
            if i >= len(dlg.selected):
                self.status.showMessage("All presets finished")
                return

            preset = self.presets.get_by_name(dlg.selected[i])
            if not preset:
                run_next(i + 1)
                return

            def on_response(text: str, preset_name: str, tag: str) -> None:
                self.display_response(text, preset_name, tag)
                self.status.showMessage(f"Finished {preset_name} ({i+1}/{len(dlg.selected)})")
                run_next(i + 1)

            self.requests.send_request_async(
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

        run_next()
