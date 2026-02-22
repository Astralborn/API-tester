"""Preset handling module for API Test Tool."""
from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QInputDialog, QMessageBox

from dialogs import MultiSelectDialog


class PresetHandlingMixin:
    """Mixin providing preset and multi-run functionality."""

    def _preset_matches(self, preset: dict[str, Any], mode: str, search: str) -> bool:
        """Check if a preset matches the given mode and search criteria."""
        name = preset.get("name", "")
        json_file = preset.get("json_file", "")
        if not json_file:
            return False

        is_unhappy = "/unhappy/" in json_file.replace("\\", "/").lower()

        if (mode == "happy" and is_unhappy) or (mode == "unhappy" and not is_unhappy):
            return False

        return search in name.lower()

    def update_presets_list(self) -> None:
        """Update the preset list based on current filter settings."""
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
        """Handle preset selection change."""
        preset = self.presets.get_by_name(name)
        if not preset:
            return

        self.json_combo.clear()
        self.json_combo.addItem("(none)")

        json_file = preset.get("json_file")
        if json_file and json_file != "(none)":
            self.json_combo.addItem(json_file)
            self.json_combo.setCurrentText(json_file)

    def save_preset(self) -> None:
        """Save current configuration as a preset."""
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
        """Load a saved preset into the UI."""
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

        self.status.setText(f"Preset '{name}' loaded")
        self.logger.log_preset_action("load_completed", name,
                                     endpoint=preset["endpoint"],
                                     json_file=preset.get("json_file", "(none)"))

    def run_multiple(self) -> None:
        """Run multiple presets in sequence."""
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
        
        self.status.setText(f"Running {self.total_request_count} presets...")
        
        try:
            log_file = self.requests.start_new_log("MultiPreset_Run")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create log file: {str(e)}")
            return

        def run_next(i: int = 0) -> None:
            if i >= len(dlg.selected):
                self.status.setText("All presets finished")
                return

            # Update progress
            self.current_request_count = i + 1
            self._update_progress(self.current_request_count, self.total_request_count)

            preset = self.presets.get_by_name(dlg.selected[i])
            if not preset:
                self.status.setText(f"Skipping invalid preset: {dlg.selected[i]}")
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
                self.status.setText(f"Failed to send {dlg.selected[i]}: {str(e)}")
                run_next(i + 1)

        run_next()
