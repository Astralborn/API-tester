from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

from constants import PRESETS_FILE


# ================= Resource Path =================

def resource_path(relative_path: str) -> Path:
    """
    Return absolute path to a resource whether running as script or PyInstaller EXE.
    External files must live next to the executable or in subfolders.
    """
    import sys

    base_dir = (
        Path(sys.executable).parent
        if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parent
    )
    return base_dir / relative_path


# ================= Preset Manager =================

class PresetManager:
    def __init__(self) -> None:
        self.presets: list[dict[str, Any]] = []
        self.load_presets()

    # ---------- Load / Save ----------

    def _preset_path(self) -> Path:
        """Return resolved presets file path."""
        return resource_path(PRESETS_FILE)

    def load_presets(self) -> None:
        """Load presets from JSON file."""
        path = self._preset_path()

        if not path.exists():
            self.presets = []
            return

        try:
            with path.open("r", encoding="utf-8") as f:
                self.presets = json.load(f)
        except Exception:
            # Corrupt JSON or read error → reset safely
            self.presets = []

    def save_presets(self) -> None:
        """Persist presets to disk."""
        path = self._preset_path()

        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump(self.presets, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            print(f"Failed to save presets: {exc}")

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
