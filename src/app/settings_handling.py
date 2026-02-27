"""Settings handling mixin for API Test Tool."""
from __future__ import annotations

from PySide6.QtCore import QTimer


class SettingsHandlingMixin:

    def load_settings(self) -> None:
        self.ip_edit.setText(self.settings.get_last_ip())
        self.user_edit.setText(self.settings.get_last_user())
        self.simple_check.setChecked(self.settings.get_last_simple_format())
        self.test_mode_combo.setCurrentText(self.settings.get_last_test_mode())
        self.json_type_combo.setCurrentText(self.settings.get_last_json_type())

        last_endpoint = self.settings.get_last_endpoint()
        if last_endpoint:
            index = self.endpoint_combo.findText(last_endpoint)
            if index >= 0:
                self.endpoint_combo.setCurrentIndex(index)

        geometry = self.settings.get_window_geometry()
        if geometry:
            self.restoreGeometry(bytes.fromhex(geometry))

    def save_settings(self) -> None:
        self.settings.set_last_ip(self.ip_edit.text())
        self.settings.set_last_user(self.user_edit.text())
        self.settings.set_last_simple_format(self.simple_check.isChecked())
        self.settings.set_last_test_mode(self.test_mode_combo.currentText())
        self.settings.set_last_json_type(self.json_type_combo.currentText())
        self.settings.set_last_endpoint(self.endpoint_combo.currentText())
        self.settings.set_last_json_file(self.json_combo.currentText())
        geometry = self.saveGeometry().data().hex()
        self.settings.set_window_geometry(geometry)
        self.settings.save_settings()

    def _auto_save_connection_settings(self) -> None:
        self.settings.set_last_ip(self.ip_edit.text())
        self.settings.set_last_user(self.user_edit.text())
        self.settings.set_last_simple_format(self.simple_check.isChecked())
        self.settings.save_settings()

    def _auto_save_ui_settings(self) -> None:
        self.settings.set_last_test_mode(self.test_mode_combo.currentText())
        self.settings.set_last_json_type(self.json_type_combo.currentText())
        self.settings.set_last_endpoint(self.endpoint_combo.currentText())
        self.settings.set_last_json_file(self.json_combo.currentText())
        self.settings.save_settings()

    def _setup_geometry_auto_save(self) -> None:
        self._geometry_timer = QTimer()
        self._geometry_timer.setSingleShot(True)
        self._geometry_timer.timeout.connect(self._auto_save_geometry)

    def _auto_save_geometry(self) -> None:
        geometry = self.saveGeometry().data().hex()
        self.settings.set_window_geometry(geometry)
        self.settings.save_settings()
