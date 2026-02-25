from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

from constants import resource_path
from logging_system import get_logger

_logger = get_logger("settings_manager")


# ================= Settings Manager =================

class SettingsManager:
    """Manages application settings persistence."""

    SETTINGS_FILE: Final[str] = "settings.json"

    def __init__(self) -> None:
        # resource_path already returns Path — no wrapping needed
        self.settings_file: Path = resource_path(self.SETTINGS_FILE)
        self.settings: dict[str, Any] = {}
        self.load_settings()

    def load_settings(self) -> None:
        """Load settings from JSON file."""
        if not self.settings_file.exists():
            self.settings = self._get_default_settings()
            return

        try:
            with self.settings_file.open("r", encoding="utf-8") as f:
                self.settings = json.load(f)
        except Exception as exc:
            _logger.error(
                "Failed to load settings — resetting to defaults",
                file=str(self.settings_file),
                error=str(exc),
            )
            self.settings = self._get_default_settings()

    def save_settings(self) -> None:
        """Save current settings to JSON file."""
        try:
            with self.settings_file.open("w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            _logger.error(
                "Failed to save settings",
                file=str(self.settings_file),
                error=str(exc),
            )

    def _get_default_settings(self) -> dict[str, Any]:
        """Return default settings."""
        return {
            "connection": {
                "last_ip": "",
                "last_user": "",
                "remember_password": False,
                "last_simple_format": False,
            },
            "ui": {
                "window_geometry": "",
                "window_state": "",
                "last_test_mode": "happy",
                "last_json_type": "normal",
            },
            "presets": {
                "last_preset": "",
                "last_endpoint": "",
                "last_json_file": "(none)",
            },
        }

    # ================= Connection Settings =================

    def get_last_ip(self) -> str:
        return self.settings.get("connection", {}).get("last_ip", "")

    def set_last_ip(self, ip: str) -> None:
        self.settings.setdefault("connection", {})["last_ip"] = ip

    def get_last_user(self) -> str:
        return self.settings.get("connection", {}).get("last_user", "")

    def set_last_user(self, user: str) -> None:
        self.settings.setdefault("connection", {})["last_user"] = user

    def get_remember_password(self) -> bool:
        return self.settings.get("connection", {}).get("remember_password", False)

    def set_remember_password(self, remember: bool) -> None:
        self.settings.setdefault("connection", {})["remember_password"] = remember

    def get_last_simple_format(self) -> bool:
        return self.settings.get("connection", {}).get("last_simple_format", False)

    def set_last_simple_format(self, simple: bool) -> None:
        self.settings.setdefault("connection", {})["last_simple_format"] = simple

    # ================= UI Settings =================

    def get_window_geometry(self) -> str:
        return self.settings.get("ui", {}).get("window_geometry", "")

    def set_window_geometry(self, geometry: str) -> None:
        self.settings.setdefault("ui", {})["window_geometry"] = geometry

    def get_window_state(self) -> str:
        return self.settings.get("ui", {}).get("window_state", "")

    def set_window_state(self, state: str) -> None:
        self.settings.setdefault("ui", {})["window_state"] = state

    def get_last_test_mode(self) -> str:
        return self.settings.get("ui", {}).get("last_test_mode", "happy")

    def set_last_test_mode(self, mode: str) -> None:
        self.settings.setdefault("ui", {})["last_test_mode"] = mode

    def get_last_json_type(self) -> str:
        return self.settings.get("ui", {}).get("last_json_type", "normal")

    def set_last_json_type(self, json_type: str) -> None:
        self.settings.setdefault("ui", {})["last_json_type"] = json_type

    # ================= Preset Settings =================

    def get_last_preset(self) -> str:
        return self.settings.get("presets", {}).get("last_preset", "")

    def set_last_preset(self, preset: str) -> None:
        self.settings.setdefault("presets", {})["last_preset"] = preset

    def get_last_endpoint(self) -> str:
        return self.settings.get("presets", {}).get("last_endpoint", "")

    def set_last_endpoint(self, endpoint: str) -> None:
        self.settings.setdefault("presets", {})["last_endpoint"] = endpoint

    def get_last_json_file(self) -> str:
        return self.settings.get("presets", {}).get("last_json_file", "(none)")

    def set_last_json_file(self, json_file: str) -> None:
        self.settings.setdefault("presets", {})["last_json_file"] = json_file