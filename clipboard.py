from enum import Enum
from typing import List, Tuple, Optional
from file import File, Path
from fileOp import FileOperations

class ClipboardAction(Enum):
    COPY = "copy"
    CUT = "cut"

class Clipboard:
    """Manages copy/cut operations between different locations """
    def __init__(self):
        self.items: List[Path] = []
        self.action: Optional[ClipboardAction] = None
    
    def copy(self, items: List[Path]):
        """copy items to clipboard"""
        self.items = items
        self.action = ClipboardAction.COPY
    
    def cut(self, items: List[Path]):
        """cut items to clipboard"""
        self.items = items
        self.action = ClipboardAction.CUT

    def paste(self, destination: Path) -> bool:
        """paste clipboard items to destination"""
        if not self.items or not self.action:
            return False
        
        success = True
        for item in self.items:
            dest = destination / item.name
            if self.action == ClipboardAction.COPY:
                if not FileOperations.copy(item, dest):
                    success = False
            else: #i.e CUT
                if not FileOperations.move(item, dest):
                    success = False
        if self.action == ClipboardAction.CUT and success:
            self.clear()

        return success

    def clear(self):
        """Clear clipboard"""
        self.items = []
        self.action = None
