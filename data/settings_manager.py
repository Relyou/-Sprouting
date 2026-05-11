"""JSON 用户配置管理器"""

import json
import os
from config import APP_DATA_DIR

_PREFS_PATH = os.path.join(APP_DATA_DIR, "preferences.json")

_DEFAULTS = {
    "theme": "light",
    "window_width": None,
    "window_height": None,
    "window_x": None,
    "window_y": None,
    "sidebar_width": 220,
    "last_page": "schedule",
    "recent_files": [],
}


class SettingsManager:
    def __init__(self, path: str = _PREFS_PATH):
        self._path = path
        self._data = {}
        self._load()

    def _load(self):
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._data = {}

    def save(self):
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default=None):
        if default is None:
            default = _DEFAULTS.get(key)
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self.save()

    def reset(self, key: str = None):
        if key is None:
            self._data.clear()
        elif key in self._data:
            del self._data[key]
        self.save()
