import json
from typing import Optional, List, Tuple, Any
from file import Path, File
from fileOp import FileOperations
from fileDisplay import ViewMode, SortBy

class Settings:
    """Manages application settings and preferences"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".file_explorer_config.json"
        self.settings = self._load()
    
    def _load(self) -> dict:
        """load settings from disk"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return self._defaults()
    
    def _defaults(self) -> dict:
        """Return default settings"""
        return {
            "default_view": ViewMode.DETAILS.value,
            "show_hidden": False,
            "sort_by": SortBy.NAME.value,
            "sort_reverse": False,
            "thumbnail_size": 64,
            "recent_locations": [],
            "bookmarks": [],
            "confirm_delete": True,
        }
    
    def save(self):
        """Save settings to disk"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass
    
    def get(self, key: str, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set(self, key:str, value):
        """Set a setting value"""
        self.settings[key] = value
        self.save()
