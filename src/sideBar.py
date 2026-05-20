from file import Path, File, platform
from typing import List
import os

class DirectoryTree:
    """Manages the folder tree structure for sidebar navigation"""

    def __init__(self):
        self.root_nodes = [] #drive roots on windows, linux
        self._initialize_roots()
    
    def _initialize_roots(self):
        """Initialize root nodes, i.e. the drive, like C:\\ on windows for instance """
        if platform.system() == "Windows":
            import string
            from ctypes import windll

            drives = []
            bitmask = windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    drives.append(f"{letter}:\\")
                bitmask >>=1
        else:
            self.root_nodes = ["/"]
    
    def get_children(self, path: Path) -> List[Path]:
        """Get subdirectories for expanding a node"""
        try:
            return [item for item in path.iterdir()
                    if item.is_dir() and not item.name.startswith('.')]
        except PermissionError:
            return []
    
    def get_common_location(self) -> List[Path]:
        """Return common user locations, e.g. Downloads, Documents etc."""
        home = Path.home()
        common = [
            home,
            home / "Downloads",
            home / "Documents",
            home / "Pictures",
            home / "Music",
            home / "Videos",
            home / "Desktop",
        ]

        return [p for p in common if p.exists()]
