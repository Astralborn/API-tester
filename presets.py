import sys
import os
import json
from constants import PRESETS_FILE

def resource_path(relative_path):
    """
    Returns the absolute path to a resource, whether running as a script or an EXE.
    External files (JSONs) must be located next to the EXE or in a subfolder.
    """
    if getattr(sys, 'frozen', False):  # Running as EXE
        base_path = os.path.dirname(sys.executable)
    else:  # Running as script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class PresetManager:
    def __init__(self):
        self.presets = []
        self.load_presets()

    def load_presets(self):
        path = resource_path(PRESETS_FILE)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.presets = json.load(f)
            except Exception:
                self.presets = []
        else:
            self.presets = []

    def save_presets(self):
        path = resource_path(PRESETS_FILE)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.presets, f, indent=2)
        except Exception as e:
            print(f"Failed to save presets: {e}")

    def add_preset(self, preset):
        existing = self.get_by_name(preset["name"])
        if existing:
            self.presets.remove(existing)
        self.presets.append(preset)
        self.save_presets()

    def get_by_name(self, name):
        for p in self.presets:
            if p.get("name") == name:
                return p
        return None

    def get_names(self):
        return [p.get("name") for p in self.presets]
