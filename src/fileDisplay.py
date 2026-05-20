from enum import Enum
from typing import List
from file import File
from datetime import datetime

class ViewMode(Enum):
    ICON = "icon"
    LIST = "list"
    DETAILS = "details"
    GRID = "grid"

class SortBy(Enum):
    NAME = "name"
    SIZE = "size"
    MODIFIED = "modified"
    TYPE = "type"

class DisplayManager:
    """manage display settings and how files are sorted / displayed"""
    
    def __init__(self):
        """ Default settings"""
        self.view_mode = ViewMode.DETAILS
        self.sort_by = SortBy.NAME
        self.show_hidden = False
        self.thumbnail_size = 64 #size for the icon view

    def sort_items(self, items: List[File]) -> List[File]:
        """Sort files according to current settings """
        def get_sort_key(item: File):
            if self.sort_by == SortBy.NAME:
                return (not item.is_directory, item.name.lower())
            elif self.sort_by == SortBy.SIZE:
                return (not item.is_directory, item.size)
            elif self.sort_by == SortBy.MODIFIED:
                modified = item.modified_time or datetime.min
                return (not item.is_directory, modified)
            elif self.sort_by == SortBy.TYPE:
                return (not item.is_directory, item.extensions.lower(), item.name.lower())
            return (not item.is_directory, item.name.lower())
        
        sorted_items = sorted(items, key=get_sort_key)
        if self.sort_reverse:
            sorted_items.reverse()
        return sorted_items

    def filter_items(self, items: List[File]) -> List[File]:
        """Apply filters, ex. hide hidden files[True]"""
        if not self.show_hidden:
            items = [f for f in items if not f.is_hidden]
        return items
    