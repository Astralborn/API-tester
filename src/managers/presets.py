from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config.constants import PRESETS_FILE
from config.logging_system import get_logger

_logger = get_logger("preset_manager")


class PresetManager:
    def __init__(self) -> None:
        self.presets: list[dict[str, Any]] = []
        self.load_presets()

    def load_presets(self) -> None:
        """Load presets from JSON file."""
        if not PRESETS_FILE.exists():
            self.presets = []
            return
        try:
            with PRESETS_FILE.open("r", encoding="utf-8") as f:
                self.presets = json.load(f)
        except Exception as exc:
            _logger.error("Failed to load presets", error=str(exc))
            self.presets = []

    def save_presets(self) -> None:
        """Persist presets to disk."""
        try:
            with PRESETS_FILE.open("w", encoding="utf-8") as f:
                json.dump(self.presets, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            _logger.error("Failed to save presets", error=str(exc))

    def add_preset(self, preset: dict[str, Any]) -> None:
        """Add or replace preset by name."""
        name = preset.get("name")
        if not name:
            return
        existing = self.get_by_name(name)
        if existing:
            self.presets.remove(existing)
        self.presets.append(preset)
        self.save_presets()

    def get_by_name(self, name: str) -> dict[str, Any] | None:
        return next((p for p in self.presets if p.get("name") == name), None)

    def get_names(self) -> list[str]:
        return [p.get("name", "") for p in self.presets]

    def delete_preset(self, name: str) -> bool:
        existing = self.get_by_name(name)
        if existing:
            self.presets.remove(existing)
            self.save_presets()
            return True
        return False
