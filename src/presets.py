from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from constants import PRESETS_FILE
from logging_system import get_logger

_logger = get_logger("preset_manager")


# ================= Preset Manager =================

class PresetManager:
    def __init__(self) -> None:
        self.presets: list[dict[str, Any]] = []
        self.load_presets()

    # ---------- Load / Save ----------

    def _preset_path(self) -> Path:
        """Return resolved presets file path."""
        # PRESETS_FILE is already a Path (built by constants.resource_path)
        return PRESETS_FILE

    def load_presets(self) -> None:
        """Load presets from JSON file."""
        path = self._preset_path()

        if not path.exists():
            self.presets = []
            return

        try:
            with path.open("r", encoding="utf-8") as f:
                self.presets = json.load(f)
        except Exception as exc:
            _logger.error(
                "Failed to load presets — resetting to empty list",
                file=str(path),
                error=str(exc),
            )
            self.presets = []

    def save_presets(self) -> None:
        """Persist presets to disk."""
        path = self._preset_path()

        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump(self.presets, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            _logger.error(
                "Failed to save presets",
                file=str(path),
                error=str(exc),
            )

    # ---------- CRUD ----------

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
        """Return preset dict by name."""
        return next((p for p in self.presets if p.get("name") == name), None)

    def get_names(self) -> list[str]:
        """Return list of preset names."""
        return [p.get("name", "") for p in self.presets]