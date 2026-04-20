from typing import Optional, Union, Tuple, Any, List
from file import Path, File
import os


class FileNavigator:
    """Manage navigation through filesystems and directories"""

    def __init__(self, root_path: Optional[str] = None):
        self.current_path = Path(root_path or os.path.expanduser("~"))
        self.history = [] #Back navigation stack
        self.forward_stack = [] #Forward navigation stack, opposite to history
        self.bookmarks = [] #saved locations, favorites

    def list_current_dir(self) -> List[File]:
        """Get all files/directories in current path"""
        items = []
        try:
            for item in self.current_path.iterdir():
                #Optionally filter hidden files
                items.append(File(item))
        except PermissionError:
            pass #handle gracefully
        return sorted(items, key=lambda x: (not x.is_directory, x.name.lower()))
    
    def go_to(self, path: Union[str, Path]) -> bool:
        """Navigate to specified path"""
        new_path = Path(path)
        if new_path.exists() and new_path.is_dir():
            self.history.append(self.current_path)
            self.current_path = new_path
            self.forward_stack.clear()
            return True
        return False
    
    def go_back(self) -> bool:
        """Navigate to previous location, undo action"""
        if self.history:
            self.forward_stack.append(self.current_path)
            self.current_path = self.history.pop()
            return True
        return False
    
    def go_forward(self) -> bool:
        """Navigate forwardd in history"""
        if self.forward_stack:
            self.history.append(self.current_path)
            self.current_path = self.forward_stack.pop()
            return True
        return False
    
    def get_parent(self) -> Optional[Path]:
        """Get the parent of current dir / path """
        parent = self.current_path.parent
        if parent != self.current_path: #not in root, root do not have parent
            return parent
        return None
