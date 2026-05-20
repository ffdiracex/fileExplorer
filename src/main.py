#!/usr/bin/env python3
# main.py - Heavily OOP File Explorer with deep inheritance hierarchies
"""
Advanced File Explorer demonstrating OOP principles:
- Abstract Base Classes
- Multiple Inheritance
- Mixins
- Polymorphism
- Method Resolution Order (MRO)
- Factory Pattern
- Strategy Pattern
- Observer Pattern
- Template Method Pattern
"""

from datetime import datetime
import tkinter as tkinter
from typing import List, Tuple, Any, Optional, Dict
from file import Path, File
from fileDisplay import DisplayManager, SortBy, ViewMode
from clipboard import Clipboard, ClipboardAction
from settings import Settings
from fileSearch import FileSearch
from sideBar import DirectoryTree
from thumbnail import ThumbnailGenerator
from fileOp import FileOperations
from fileNav import FileNavigator
from dataclasses import dataclass, field
from enum import Enum, auto
from abc import ABC, abstractmethod
import platform
import argparse
import logging
import logging.handlers
import os
import sys
import traceback
import shutil
from functools import wraps
from collections import abc
import weakref


# ============================================================================
# TYPE ALIASES AND ENUMS
# ============================================================================

class FileType(Enum):
    """Enumeration of supported file categories."""
    DIRECTORY = auto()
    DOCUMENT = auto()
    IMAGE = auto()
    VIDEO = auto()
    AUDIO = auto()
    PDF = auto()
    ARCHIVE = auto()
    CODE = auto()
    EXECUTABLE = auto()
    UNKNOWN = auto()


class OSPlatform(Enum):
    """Enumeration of supported operating systems."""
    WINDOWS = "Windows"
    MACOS = "Darwin"
    LINUX = "Linux"
    UNKNOWN = "Unknown"


class ClipboardOperation(Enum):
    """Enumeration of clipboard operations."""
    COPY = auto()
    CUT = auto()
    NONE = auto()


# DECORATORS 

def log_method_call(func):
    """Decorator that logs method entry, exit, and exceptions."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        logger = getattr(self, 'logger', logging.getLogger(__name__))
        logger.debug(f"-> {self.__class__.__name__}.{func.__name__}() called")
        try:
            result = func(self, *args, **kwargs)
            logger.debug(f"<- {self.__class__.__name__}.{func.__name__}() completed")
            return result
        except Exception as e:
            logger.error(f"-X- {self.__class__.__name__}.{func.__name__}() failed: {e}")
            raise
    return wrapper


def require_selection(func):
    """Decorator that ensures files are selected before executing."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.get_selected_files():
            self.status_label.config(text="No items selected")
            return
        return func(self, *args, **kwargs)
    return wrapper

# MIXIN CLASSES (Horizontal Reuse)
class LoggingMixin:
    """Mixin that provides logging capabilities to any class."""
    
    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(
                f"{self.__class__.__module__}.{self.__class__.__name__}"
            )
        return self._logger

class ObservableMixin:
    """Mixin implementing the Observer pattern."""
    
    def __init__(self, *args, **kwargs):
        """ Pylint please get off my a$$, docstrings are not mandatory everywhere! """
        super().__init__(*args, **kwargs)
        self._observers: Dict[str, List[weakref.ref]] = {}
    
    def register_observer(self, event: str, observer) -> None:
        """Register an observer for a specific event."""
        if event not in self._observers:
            self._observers[event] = []
        self._observers[event].append(weakref.ref(observer))
    
    def notify_observers(self, event: str, data: Any = None) -> None:
        """Notify all observers of an event."""
        for ref in self._observers.get(event, []):
            observer = ref()
            if observer and hasattr(observer, 'on_notify'):
                observer.on_notify(event, data)
            elif observer is None:
                self._observers[event].remove(ref)


class ConfigurableMixin:
    """Mixin providing configuration persistence capabilities."""
    
    def save_config(self, config_path: Path) -> None:
        """Save configuration to disk."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            f.write(str(self.__dict__))
    
    def load_config(self, config_path: Path) -> None:
        """Load configuration from disk."""
        if config_path.exists():
            with open(config_path, 'r') as f:
                pass  # Implementation would parse config


# BASE CLASSES (Contracts)

class IFileSystem(ABC):
    """Abstract interface for file system operations."""
    
    @abstractmethod
    def exists(self, path: Path) -> bool:
        """Check if path exists."""
        ...
    
    @abstractmethod
    def is_directory(self, path: Path) -> bool:
        """Check if path is a directory."""
        ...
    
    @abstractmethod
    def list_directory(self, path: Path) -> List[Path]:
        """List contents of a directory."""
        ...
    
    @abstractmethod
    def get_file_info(self, path: Path) -> Dict[str, Any]:
        """Get metadata about a file."""
        ...


class IClipboard(ABC):
    """Abstract interface for clipboard operations."""
    
    @abstractmethod
    def copy(self, items: List['IFileItem']) -> None:
        """Copy items to clipboard."""
        ...
    
    @abstractmethod
    def cut(self, items: List['IFileItem']) -> None:
        """Cut items to clipboard."""
        ...
    
    @abstractmethod
    def paste(self, destination: 'IFileItem') -> None:
        """Paste items from clipboard."""
        ...
    
    @abstractmethod
    def clear(self) -> None:
        """Clear clipboard contents."""
        ...


class IFileItem(ABC):
    """Abstract interface for file system items."""
    @property
    @abstractmethod
    def path(self) -> Path:
        """Get the path of this item."""
        ...
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this item."""
        ...
    @property
    @abstractmethod
    def is_directory(self) -> bool:
        """Check if this item is a directory."""
        ...
    @property
    @abstractmethod
    def size(self) -> int:
        """Get the size in bytes."""
        ...
    @abstractmethod
    def get_file_type(self) -> FileType:
        """Get the file type category."""
        ...

class IUIComponent(ABC):
    """Abstract interface for UI components."""
    
    @abstractmethod
    def build(self, parent) -> None:
        """Build the UI component."""
        ...
    @abstractmethod
    def refresh(self) -> None:
        """Refresh the component's state."""
        ...
    @abstractmethod
    def destroy(self) -> None:
        """Clean up the component."""
        ...


#PLATFORM DETECTION / HANDLE PLATFORM SPECIFIC MISC.
class PlatformStrategy(ABC):
    """Abstract strategy for platform-specific operations.
    @note:
        THE BASE CLASSES WON'T IMPLEMENT THE FUNCTION BODY
        INSTEAD, CHECK THE CHILDREN'S IMPLEMENTATION OF THIS.

    """
    
    @abstractmethod
    def is_hidden(self, path: Path) -> bool:
        """Determine if a file is hidden."""
        ...
    
    @abstractmethod
    def open_file(self, path: Path) -> None:
        """Open a file with the default application."""
        ...
    
    @abstractmethod
    def get_drives(self) -> List[Path]:
        """Get available drives/root directories."""
        ...
    
    @abstractmethod
    def get_platform_type(self) -> OSPlatform:
        """Get the current platform type."""
        ...


class WindowsPlatformStrategy(PlatformStrategy):
    """Windows-specific platform strategy.
    @note:
        WHILE IT DOES BRING MENTAL DISTRESS, WE WILL HANDLE THE WINDOWS FILE API
        (SPOILER: IT SUCKS).

    """
    
    def is_hidden(self, path: Path) -> bool:
        """Check Windows hidden attribute."""
        try:
            import ctypes
            FILE_ATTRIBUTE_HIDDEN = 0x2
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path)) # @opinion WHY is this nested inside 3 layers? 
            if attrs != -1:
                return bool(attrs & FILE_ATTRIBUTE_HIDDEN) # Alright now we are getting somewhere.
        except Exception:
            pass
        return path.name.startswith('.')
    
    def open_file(self, path: Path) -> None:
        """Open file with Windows default application."""
        os.startfile(str(path))
    
    def get_drives(self) -> List[Path]:
        """Get available Windows drive letters."""
        import string
        import ctypes
        
        drives = [] # hopefully $USER will not have 5+ drives, but let's just use a flat one-dimensional array.
        bitmask = ctypes.windll.kernel32.GetLogicalDrives() # @note this will not return a string like "C:", it will return @placeholder numerical.
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drives.append(Path(f"{letter}:\\"))
            bitmask >>= 1
        return drives
    
    def get_platform_type(self) -> OSPlatform:
        return OSPlatform.WINDOWS


class UnixPlatformStrategy(PlatformStrategy):
    """Unix/Linux-specific platform strategies, @note: we love this, finally a break from windows!"""
    
    def is_hidden(self, path: Path) -> bool:
        """Check if file starts with dot."""
        return path.name.startswith('.')
    
    def open_file(self, path: Path) -> None:
        """Open file with xdg-open."""
        os.system(f"xdg-open '{path}'")
    
    def get_drives(self) -> List[Path]:
        """Return root path for Unix systems."""
        return [Path("/")]
    
    def get_platform_type(self) -> OSPlatform:
        """ This is ridicolous pylint, literally require docstrings everywhere, just cortisol spike everything why don't you.  """
        return OSPlatform.LINUX


class MacOSPlatformStrategy(PlatformStrategy):
    """macOS-specific platform strategy. Very similar to Linux, but differences are still significant.  """
    
    def is_hidden(self, path: Path) -> bool:
        """Check if file starts with dot."""
        return path.name.startswith('.')
    
    def open_file(self, path: Path) -> None:
        """Open file with macOS open command."""
        os.system(f"open '{path}'")
    
    def get_drives(self) -> List[Path]:
        """Return root and volumes for macOS."""
        return [Path("/"), Path("/Volumes")]
    
    def get_platform_type(self) -> OSPlatform:
        return OSPlatform.MACOS


class PlatformStrategyFactory:
    """ Generate platform-specific strategies."""
    
    _strategies = {
        "Windows": WindowsPlatformStrategy,
        "Darwin": MacOSPlatformStrategy, # @note For some reason, MacOS is referred to as 'Darwin'.
        "Linux": UnixPlatformStrategy,
        "": WindowsPlatformStrategy,  # Default for Java environments
    }
    
    @classmethod
    def create(cls) -> PlatformStrategy:
        """Create appropriate platform strategy."""
        system = platform.system()
        strategy_class = cls._strategies.get(system, UnixPlatformStrategy)
        return strategy_class()


# ============================================================================
# STRATEGY PATTERN - File Sorting
# ============================================================================

class SortStrategy(ABC):
    """Abstract base for sorting strategies."""
    
    @abstractmethod
    def sort(self, items: List['FileSystemItem']) -> List['FileSystemItem']:
        """Sort a list of file items."""
        ...


class SortByName(SortStrategy):
    """Sort files by name, directories first."""
    
    def sort(self, items: List['FileSystemItem']) -> List['FileSystemItem']:
        return sorted(items, key=lambda x: (not x.is_directory, x.name.lower()))


class SortBySize(SortStrategy):
    """Sort files by size, directories first."""
    
    def sort(self, items: List['FileSystemItem']) -> List['FileSystemItem']:
        return sorted(items, key=lambda x: (not x.is_directory, x.size))


class SortByModified(SortStrategy):
    """Sort files by modification date, directories first."""
    
    def sort(self, items: List['FileSystemItem']) -> List['FileSystemItem']:
        return sorted(
            items, 
            key=lambda x: (not x.is_directory, x.modified_time),
            reverse=True
        )


class SortByType(SortStrategy):
    """Sort files by extension, directories first."""
    
    def sort(self, items: List['FileSystemItem']) -> List['FileSystemItem']:
        return sorted(
            items,
            key=lambda x: (
                not x.is_directory,
                x.path.suffix.lower() if not x.is_directory else ""
            )
        )


class SortStrategyFactory:
    """Factory for creating sort strategies."""
    
    _strategies = {
        SortBy.NAME: SortByName,
        SortBy.SIZE: SortBySize,
        SortBy.MODIFIED: SortByModified,
        SortBy.TYPE: SortByType,
    }
    
    @classmethod
    def create(cls, sort_by: SortBy) -> SortStrategy:
        """Create a sort strategy based on criteria."""
        strategy_class = cls._strategies.get(sort_by, SortByName)
        return strategy_class()


# ============================================================================
# CORE DOMAIN MODEL - Deep Inheritance Hierarchy
# ============================================================================

class FileSystemItem:
    """Base class for all filesystem items."""
    
    __slots__ = ['_path', '_stat', '_platform_strategy']
    
    def __init__(self, path: Path, platform_strategy: Optional[PlatformStrategy] = None):
        self._path = path
        self._platform_strategy = platform_strategy or PlatformStrategyFactory.create()
        self._stat = None
    
    @property
    def path(self) -> Path:
        return self._path
    
    @property
    def name(self) -> str:
        return self._path.name
    
    @property
    def is_directory(self) -> bool:
        return self._path.is_dir()
    
    @property
    def is_hidden(self) -> bool:
        return self._platform_strategy.is_hidden(self._path)
    
    @property
    def stat(self):
        if self._stat is None:
            try:
                self._stat = self._path.stat()
            except (OSError, PermissionError):
                self._stat = None
        return self._stat
    
    @property
    def size(self) -> int:
        if self.is_directory:
            return 0
        try:
            return self.stat.st_size if self.stat else 0
        except Exception:
            return 0
    
    @property
    def modified_time(self) -> datetime:
        try:
            return datetime.fromtimestamp(self.stat.st_mtime) if self.stat else datetime.now()
        except Exception:
            return datetime.now()
    
    @property
    def created_time(self) -> datetime:
        try:
            return datetime.fromtimestamp(self.stat.st_ctime) if self.stat else datetime.now()
        except Exception:
            return datetime.now()
    
    def get_file_type(self) -> FileType:
        """Override in subclasses for specific behavior."""
        if self.is_directory:
            return FileType.DIRECTORY
        return FileType.UNKNOWN
    
    def get_size_human(self) -> str:
        """Convert size to human-readable format."""
        if self.is_directory:
            return "—"
        
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(path={self._path})"
    
    def __eq__(self, other) -> bool:
        if isinstance(other, FileSystemItem):
            return self._path == other._path
        return False
    
    def __hash__(self) -> int:
        return hash(self._path)


#Directory vs File | Inheritance
class DirectoryItem(FileSystemItem):
    """Represents a directory in the file system."""
    
    __slots__ = ['_contents_cache', '_contents_count']
    
    def __init__(self, path: Path, platform_strategy: Optional[PlatformStrategy] = None):
        super().__init__(path, platform_strategy)
        self._contents_cache: Optional[List[FileSystemItem]] = None
        self._contents_count: int = -1
    
    def get_contents(self, show_hidden: bool = False, 
                     search_filter: str = "") -> List[FileSystemItem]:
        """Get contents of this directory."""
        if self._contents_cache is None:
            self._load_contents()
        
        items = self._contents_cache or []
        
        # Apply filters
        if not show_hidden:
            items = [i for i in items if not i.is_hidden]
        
        if search_filter:
            search_filter = search_filter.lower()
            items = [i for i in items if search_filter in i.name.lower()]
        
        return items
    
    def _load_contents(self) -> None:
        """Load directory contents. Template Method - override in subclasses."""
        items = []
        try:
            for entry in self._path.iterdir():
                try:
                    item = FileSystemItemFactory.create(entry, self._platform_strategy)
                    items.append(item)
                except (PermissionError, OSError):
                    continue
        except PermissionError:
            pass
        
        self._contents_cache = items
        self._contents_count = len(items)
    
    def invalidate_cache(self) -> None:
        """Invalidate the contents cache."""
        self._contents_cache = None
    
    def get_file_type(self) -> FileType:
        return FileType.DIRECTORY
    
    @property
    def item_count(self) -> int:
        """Get number of items in directory."""
        if self._contents_count < 0:
            self._load_contents()
        return self._contents_count


class RegularFile(FileSystemItem):
    """Represents a regular file."""
    
    __slots__ = ['_file_type', '_extension']
    
    def __init__(self, path: Path, platform_strategy: Optional[PlatformStrategy] = None):
        super().__init__(path, platform_strategy)
        self._extension = path.suffix.lower()
        self._file_type = self._determine_file_type()
    
    def get_file_type(self) -> FileType:
        return self._file_type
    
    def get_icon(self) -> str:
        """Get icon identifier for this file type."""
        return self._file_type.name.lower()
    
    @property
    def extension(self) -> str:
        return self._extension
    
    def _determine_file_type(self) -> FileType:
        """Determine file type based on extension."""
        ext_map = {   # TODO: Add support for more extensions. These are the ones the Author can come up with.
            FileType.DOCUMENT: {'.txt', '.md', '.rst', '.doc', '.docx', '.odt'},
            FileType.IMAGE: {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg', '.webp'},
            FileType.VIDEO: {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'},
            FileType.AUDIO: {'.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac', '.wma'},
            FileType.PDF: {'.pdf'},
            FileType.ARCHIVE: {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'},
            FileType.CODE: {
                '.py', '.js', '.html', '.css', '.cpp', '.java', '.rs', '.go',
                '.ts', '.jsx', '.tsx', '.rb', '.php', '.swift', '.kt', '.c',
                '.h', '.hpp', '.cs', '.sql', '.sh', '.bash', '.zsh', '.yml',
                '.yaml', '.json', '.xml', '.toml', '.ini', '.cfg'
            },
            FileType.EXECUTABLE: {'.exe', '.msi', '.app', '.bat', '.cmd', '.ps1', '.sh'},
        }
        
        for file_type, extensions in ext_map.items():
            if self._extension in extensions:
                return file_type
        
        return FileType.UNKNOWN #Not found in the ext_map dict.


# Second Inheritance Level: Specialized File Types

class ImageFile(RegularFile):
    """Specialized class for image files with metadata."""
    
    __slots__ = ['_dimensions', '_has_transparency']
    
    def __init__(self, path: Path, platform_strategy: Optional[PlatformStrategy] = None):
        """ declare the type of important properties. @note this can be made more advanced / more support for images. """
        super().__init__(path, platform_strategy)
        self._dimensions: Optional[Tuple[int, int]] = None
        self._has_transparency: bool = False
    
    @property
    def dimensions(self) -> Optional[Tuple[int, int]]:
        """Get image dimensions (width, height)."""
        if self._dimensions is None:
            self._load_image_metadata()
        return self._dimensions
    
    @property
    def has_transparency(self) -> bool:
        """Check if image has transparency."""
        return self._has_transparency
    
    @log_method_call
    def _load_image_metadata(self) -> None:
        """Load image metadata lazily."""
        try:
            from PIL import Image
            with Image.open(self.path) as img:
                self._dimensions = img.size
                self._has_transparency = img.mode in ('RGBA', 'LA', 'PA')
        except Exception:
            self._dimensions = None


class CodeFile(RegularFile):
    """Specialized class for source code files."""
    
    __slots__ = ['_language', '_line_count', '_is_test']
    
    _language_map = {
        '.py': 'Python', '.js': 'JavaScript', '.html': 'HTML',
        '.css': 'CSS', '.cpp': 'C++', '.java': 'Java',
        '.rs': 'Rust', '.go': 'Go', '.ts': 'TypeScript',
    }
    
    def __init__(self, path: Path, platform_strategy: Optional[PlatformStrategy] = None):
        super().__init__(path, platform_strategy)
        self._language = self._language_map.get(self.extension, 'Unknown')
        self._line_count: int = -1
        self._is_test = 'test' in self.name.lower() or self.name.startswith('test_')
    
    @property
    def language(self) -> str: 
        """pylint wants this """
        return self._language
    
    @property
    def line_count(self) -> int:
        """Get number of lines (lazy loaded)."""
        if self._line_count < 0:
            self._count_lines()
        return self._line_count
    
    @property
    def is_test_file(self) -> bool:
        """pylint wants this """
        return self._is_test
    
    def _count_lines(self) -> None:
        """Count lines in source file."""
        try:
            with open(self.path, 'r', encoding='utf-8', errors='ignore') as f:
                self._line_count = sum(1 for _ in f)
        except Exception:
            self._line_count = 0


class ArchiveFile(RegularFile):
    """Specialized class for archive files."""
    
    __slots__ = ['_content_count', '_compressed_size']
    
    def __init__(self, path: Path, platform_strategy: Optional[PlatformStrategy] = None):
        super().__init__(path, platform_strategy)
        self._content_count: int = -1
        self._compressed_size: int = self.size
    
    @property
    def content_count(self) -> int:
        """Get number of files in archive."""
        if self._content_count < 0:
            self._scan_archive()
        return self._content_count
    
    @property
    def compression_ratio(self) -> float:
        """Get compression ratio."""
        try:
            return self._compressed_size / max(self.stat.st_size if self.stat else 1, 1)
        except Exception:
            return 1.0
    
    def _scan_archive(self) -> None:
        """Scan archive contents."""
        try:
            import zipfile
            if self.extension == '.zip':
                with zipfile.ZipFile(self.path, 'r') as zf:
                    self._content_count = len(zf.namelist())
        except Exception:
            self._content_count = 0


class ExecutableFile(RegularFile):
    """Specialized class for executable files."""
    
    __slots__ = ['_is_signed', '_requires_admin']
    
    def __init__(self, path: Path, platform_strategy: Optional[PlatformStrategy] = None):
        super().__init__(path, platform_strategy)
        self._is_signed: bool = False
        self._requires_admin: bool = False
    
    @property
    def is_signed(self) -> bool:
        return self._is_signed
    
    @property
    def requires_admin(self) -> bool:
        return self._requires_admin


# ============================================================================
# FACTORY PATTERN - File System Item Creation
# ============================================================================

class FileSystemItemFactory:
    """Factory for creating appropriate FileSystemItem subclasses."""
    
    _type_mapping = {
        FileType.IMAGE: ImageFile,
        FileType.CODE: CodeFile,
        FileType.ARCHIVE: ArchiveFile,
        FileType.EXECUTABLE: ExecutableFile,
    }
    
    @classmethod
    def create(cls, path: Path, 
               platform_strategy: Optional[PlatformStrategy] = None) -> FileSystemItem:
        """Create appropriate FileSystemItem subclass based on path."""
        if path.is_dir():
            return DirectoryItem(path, platform_strategy)
        
        # Determine file type first
        temp_file = RegularFile(path, platform_strategy)
        file_type = temp_file.get_file_type()
        
        # Get specialized class if available
        item_class = cls._type_mapping.get(file_type, RegularFile)
        return item_class(path, platform_strategy)


# ============================================================================
# COMMAND PATTERN - Undoable Operations
# ============================================================================

class Command(ABC):
    """Abstract base for undoable commands."""
    
    __slots__ = ['_description']
    
    def __init__(self, description: str = ""):
        self._description = description
    
    @abstractmethod
    def execute(self) -> bool:
        """Execute the command."""
        ...
    
    @abstractmethod
    def undo(self) -> bool:
        """Undo the command."""
        ...
    
    @abstractmethod
    def redo(self) -> bool:
        """Redo the command (defaults to execute)."""
        return self.execute()
    
    @property
    def description(self) -> str:
        return self._description


class CopyCommand(Command):
    """Command for copying files."""
    
    def __init__(self, source_items: List[FileSystemItem], 
                 destination: DirectoryItem, platform_strategy: PlatformStrategy):
        super().__init__(f"Copy {len(source_items)} item(s)")
        self._sources = source_items
        self._destination = destination
        self._platform = platform_strategy
        self._copied_paths: List[Path] = []
    
    def execute(self) -> bool:
        try:
            for item in self._sources:
                dest = self._destination.path / item.name
                if item.is_directory:
                    shutil.copytree(item.path, dest)
                else:
                    shutil.copy2(item.path, dest)
                self._copied_paths.append(dest)
            return True
        except Exception:
            self._rollback()
            return False
    
    def undo(self) -> bool:
        return self._rollback()
    
    def redo(self) -> bool:
        self._copied_paths = []
        return self.execute()
    
    def _rollback(self) -> bool:
        """Remove copied files."""
        for path in self._copied_paths:
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
            except Exception:
                pass
        self._copied_paths = []
        return True


class MoveCommand(Command):
    """Command for moving files."""
    
    def __init__(self, source_items: List[FileSystemItem],
                 destination: DirectoryItem, platform_strategy: PlatformStrategy):
        super().__init__(f"Move {len(source_items)} item(s)")
        self._sources = source_items
        self._destination = destination
        self._platform = platform_strategy
        self._moved_paths: List[Tuple[Path, Path]] = []
    
    def execute(self) -> bool:
        try:
            for item in self._sources:
                dest = self._destination.path / item.name
                original = item.path
                shutil.move(str(original), str(dest))
                self._moved_paths.append((original, dest))
            return True
        except Exception:
            self._rollback()
            return False
    
    def undo(self) -> bool:
        return self._rollback()
    
    def redo(self) -> bool:
        new_moves = []
        for orig, dest in self._moved_paths:
            shutil.move(str(dest), str(orig))
            new_moves.append((orig, dest))
        self._moved_paths = new_moves
        return True
    
    def _rollback(self) -> bool:
        """Move files back to original locations."""
        for orig, dest in reversed(self._moved_paths):
            try:
                shutil.move(str(dest), str(orig))
            except Exception:
                pass
        self._moved_paths = []
        return True


class DeleteCommand(Command):
    """Command for deleting files."""
    
    def __init__(self, items: List[FileSystemItem], platform_strategy: PlatformStrategy):
        super().__init__(f"Delete {len(items)} item(s)")
        self._items = items
        self._platform = platform_strategy
        self._trash_path: Optional[Path] = None
    
    def execute(self) -> bool:
        import tempfile
        self._trash_path = Path(tempfile.mkdtemp(prefix="filex_trash_"))
        
        try:
            for item in self._items:
                dest = self._trash_path / item.name
                shutil.move(str(item.path), str(dest))
            return True
        except Exception:
            return False
    
    def undo(self) -> bool:
        if not self._trash_path or not self._trash_path.exists():
            return False
        
        try:
            for item in self._trash_path.iterdir():
                for original in self._items:
                    if item.name == original.name:
                        shutil.move(str(item), str(original.path))
                        break
            shutil.rmtree(self._trash_path)
            return True
        except Exception:
            return False
    
    def redo(self) -> bool:
        return self.execute()


class RenameCommand(Command):
    """Command for renaming a file."""
    
    def __init__(self, item: FileSystemItem, new_name: str):
        super().__init__(f"Rename '{item.name}' to '{new_name}'")
        self._item = item
        self._old_name = item.name
        self._new_name = new_name
        self._old_path = item.path
        self._new_path = item.path.parent / new_name
    
    def execute(self) -> bool:
        try:
            self._old_path.rename(self._new_path)
            return True
        except Exception:
            return False
    
    def undo(self) -> bool:
        try:
            self._new_path.rename(self._old_path)
            return True
        except Exception:
            return False


class NewFolderCommand(Command):
    """Command for creating a new folder."""
    
    def __init__(self, parent: DirectoryItem, folder_name: str):
        super().__init__(f"Create folder '{folder_name}'")
        self._parent = parent
        self._folder_name = folder_name
        self._folder_path = parent.path / folder_name
    
    def execute(self) -> bool:
        try:
            self._folder_path.mkdir()
            return True
        except Exception:
            return False
    
    def undo(self) -> bool:
        try:
            if self._folder_path.exists():
                self._folder_path.rmdir()
            return True
        except Exception:
            return False


# ============================================================================
# STATE PATTERN - Clipboard State Management
# ============================================================================

class ClipboardState(ABC):
    """Abstract state for clipboard."""
    
    def __init__(self, clipboard: 'ClipboardManager'):
        self._clipboard = clipboard
    
    @abstractmethod
    def copy(self, items: List[FileSystemItem]) -> None:
        ...
    
    @abstractmethod
    def cut(self, items: List[FileSystemItem]) -> None:
        ...
    
    @abstractmethod
    def paste(self, destination: DirectoryItem) -> Optional[Command]:
        ...
    
    @abstractmethod
    def get_status_text(self) -> str:
        ...


class EmptyClipboardState(ClipboardState):
    """State when clipboard is empty."""
    
    def copy(self, items: List[FileSystemItem]) -> None:
        self._clipboard._items = items
        self._clipboard._operation = ClipboardOperation.COPY
        self._clipboard._state = self._clipboard._filled_state
    
    def cut(self, items: List[FileSystemItem]) -> None:
        self._clipboard._items = items
        self._clipboard._operation = ClipboardOperation.CUT
        self._clipboard._state = self._clipboard._filled_state
    
    def paste(self, destination: DirectoryItem) -> Optional[Command]:
        return None
    
    def get_status_text(self) -> str:
        return "Clipboard is empty"


class FilledClipboardState(ClipboardState):
    """State when clipboard has items."""
    
    def copy(self, items: List[FileSystemItem]) -> None:
        self._clipboard._items = items
        self._clipboard._operation = ClipboardOperation.COPY
    
    def cut(self, items: List[FileSystemItem]) -> None:
        self._clipboard._items = items
        self._clipboard._operation = ClipboardOperation.CUT
    
    def paste(self, destination: DirectoryItem) -> Optional[Command]:
        items = self._clipboard._items
        platform = self._clipboard._platform_strategy
        
        if self._clipboard._operation == ClipboardOperation.CUT:
            command = MoveCommand(items, destination, platform)
            self._clipboard.clear()
        else:
            command = CopyCommand(items, destination, platform)
        
        return command
    
    def get_status_text(self) -> str:
        count = len(self._clipboard._items)
        op = "Cut" if self._clipboard._operation == ClipboardOperation.CUT else "Copied"
        return f"{op} {count} item(s)"


class ClipboardManager:
    """Manages clipboard with state pattern."""
    
    def __init__(self, platform_strategy: PlatformStrategy):
        self._platform_strategy = platform_strategy
        self._items: List[FileSystemItem] = []
        self._operation = ClipboardOperation.NONE
        
        # States
        self._empty_state = EmptyClipboardState(self)
        self._filled_state = FilledClipboardState(self)
        self._state: ClipboardState = self._empty_state
    
    @property
    def is_empty(self) -> bool:
        return len(self._items) == 0
    
    @property
    def item_count(self) -> int:
        return len(self._items)
    
    def copy(self, items: List[FileSystemItem]) -> None:
        self._state.copy(items)
    
    def cut(self, items: List[FileSystemItem]) -> None:
        self._state.cut(items)
    
    def paste(self, destination: DirectoryItem) -> Optional[Command]:
        return self._state.paste(destination)
    
    def clear(self) -> None:
        self._items = []
        self._operation = ClipboardOperation.NONE
        self._state = self._empty_state
    
    def get_status_text(self) -> str:
        return self._state.get_status_text()


# ============================================================================
# OBSERVER PATTERN - Event System
# ============================================================================

class FileSystemEvent(Enum):
    """Events that can occur in the file system."""
    NAVIGATED = auto()
    FILES_CHANGED = auto()
    SELECTION_CHANGED = auto()
    CLIPBOARD_CHANGED = auto()
    COMMAND_EXECUTED = auto()
    COMMAND_UNDONE = auto()
    ERROR_OCCURRED = auto()


class EventBus:
    """Singleton event bus for application-wide communication."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._listeners: Dict[FileSystemEvent, List[callable]] = {}
        return cls._instance
    
    def subscribe(self, event: FileSystemEvent, callback: callable) -> None:
        """Subscribe to an event."""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
    
    def publish(self, event: FileSystemEvent, data: Any = None) -> None:
        """Publish an event to all subscribers."""
        for callback in self._listeners.get(event, []):
            try:
                callback(data)
            except Exception as e:
                logging.error(f"Event handler failed for {event}: {e}")


# ============================================================================
# COMPOSITE PATTERN - UI Components
# ============================================================================

class UIComponent(IUIComponent, LoggingMixin):
    """Base class for all UI components."""
    
    def __init__(self, app: 'FileExplorer', parent: Any):
        self._app = app
        self._parent = parent
        self._widget = None
        self._children: List[UIComponent] = []
    
    def add_child(self, child: 'UIComponent') -> None:
        """Add a child component."""
        self._children.append(child)
    
    def remove_child(self, child: 'UIComponent') -> None:
        """Remove a child component."""
        if child in self._children:
            self._children.remove(child)
    
    def build(self, parent=None) -> None:
        """Build the component and its children."""
        target = parent or self._parent
        self._build_impl(target)
        for child in self._children:
            child.build()
    
    @abstractmethod
    def _build_impl(self, parent) -> None:
        """Implementation-specific build logic."""
        ...
    
    def refresh(self) -> None:
        """Refresh the component."""
        for child in self._children:
            child.refresh()
    
    def destroy(self) -> None:
        """Destroy the component."""
        for child in self._children:
            child.destroy()
        if self._widget:
            try:
                self._widget.destroy()
            except Exception:
                pass
    
    @property
    def app(self) -> 'FileExplorer':
        return self._app


class ToolbarComponent(UIComponent):
    """Toolbar UI component."""
    
    def __init__(self, app: 'FileExplorer', parent: Any):
        super().__init__(app, parent)
        self._buttons: Dict[str, Any] = {}
    
    def _build_impl(self, parent) -> None:
        self._widget = self.app.ttk.Frame(parent)
        self._widget.pack(fill='x', pady=(0, 5))
        
        self._add_navigation_buttons()
        self._add_separator()
        self._add_action_buttons()
        self._add_separator()
        self._add_hidden_toggle()
        self._add_separator()
        self._add_search_box()
    
    def _add_navigation_buttons(self) -> None:
        app = self._app
        
        back_btn = app.ttk.Button(self._widget, text="← Back", 
                                   command=app.go_back, width=8)
        back_btn.pack(side='left', padx=2)
        self._buttons['back'] = back_btn
        
        forward_btn = app.ttk.Button(self._widget, text="Forward →", 
                                      command=app.go_forward, width=8)
        forward_btn.pack(side='left', padx=2)
        self._buttons['forward'] = forward_btn
        
        up_btn = app.ttk.Button(self._widget, text="↑ Up", 
                                 command=app.go_up, width=8)
        up_btn.pack(side='left', padx=2)
        self._buttons['up'] = up_btn
    
    def _add_action_buttons(self) -> None:
        app = self._app
        
        refresh_btn = app.ttk.Button(self._widget, text="⟳ Refresh", 
                                      command=app.refresh, width=10)
        refresh_btn.pack(side='left', padx=2)
        self._buttons['refresh'] = refresh_btn
    
    def _add_hidden_toggle(self) -> None:
        app = self._app
        
        app.show_hidden_var = app.tk.BooleanVar(value=False)
        hidden_check = app.ttk.Checkbutton(
            self._widget,
            text="Show Hidden",
            variable=app.show_hidden_var,
            command=app.toggle_hidden
        )
        hidden_check.pack(side='left', padx=5)
    
    def _add_search_box(self) -> None:
        app = self._app
        
        app.ttk.Label(self._widget, text="Search:").pack(side='left', padx=(20, 5))
        app.search_var = app.tk.StringVar()
        app.search_var.trace('w', lambda *args: app.refresh())
        app.search_entry = app.ttk.Entry(self._widget, textvariable=app.search_var, width=25)
        app.search_entry.pack(side='left', padx=2)
    
    def _add_separator(self) -> None:
        self._app.ttk.Separator(self._widget, orient='vertical').pack(
            side='left', padx=5, fill='y'
        )
    
    def update_navigation_buttons(self, can_go_back: bool, can_go_forward: bool) -> None:
        """Update navigation button states."""
        self._buttons['back'].config(state='normal' if can_go_back else 'disabled')
        self._buttons['forward'].config(state='normal' if can_go_forward else 'disabled')


class PathBarComponent(UIComponent):
    """Path bar UI component."""
    
    def _build_impl(self, parent) -> None:
        app = self._app
        
        self._widget = app.ttk.Frame(parent)
        self._widget.pack(fill='x', pady=(0, 5))
        
        app.ttk.Label(self._widget, text="Path:").pack(side='left', padx=5)
        
        app.path_var = app.tk.StringVar()
        app.path_entry = app.ttk.Entry(self._widget, textvariable=app.path_var)
        app.path_entry.pack(side='left', fill='x', expand=True, padx=5)
        app.path_entry.bind('<Return>', lambda e: app.navigate_to_path())
        
        go_btn = app.ttk.Button(self._widget, text="Go", 
                                 command=app.navigate_to_path, width=6)
        go_btn.pack(side='left', padx=2)


class FileListComponent(UIComponent):
    """File list UI component."""
    
    def _build_impl(self, parent) -> None:
        app = self._app
        
        list_frame = app.ttk.Frame(parent)
        list_frame.pack(side='left', fill='both', expand=True)
        self._widget = list_frame
        
        columns = ('size', 'type', 'modified')
        app.file_tree = app.ttk.Treeview(
            list_frame,
            columns=columns,
            show='tree headings',
            selectmode='extended'
        )
        
        app.file_tree.heading('#0', text='Name')
        app.file_tree.heading('size', text='Size')
        app.file_tree.heading('type', text='Type')
        app.file_tree.heading('modified', text='Modified')
        
        app.file_tree.column('#0', width=400, minwidth=200)
        app.file_tree.column('size', width=100, anchor='e')
        app.file_tree.column('type', width=100, anchor='w')
        app.file_tree.column('modified', width=150, anchor='w')
        
        vsb = app.ttk.Scrollbar(list_frame, orient='vertical', 
                                 command=app.file_tree.yview)
        hsb = app.ttk.Scrollbar(list_frame, orient='horizontal', 
                                 command=app.file_tree.xview)
        app.file_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        app.file_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        app.file_tree.bind('<Double-1>', lambda e: app.open_selected())
        app.file_tree.bind('<Button-3>', app.show_context_menu)
        app.file_tree.bind('<<TreeviewSelect>>', app.on_item_select)


# ============================================================================
# MAIN APPLICATION CLASS (Composition of All Components)
# ============================================================================

class FileExplorer(LoggingMixin, ObservableMixin, ConfigurableMixin):
    """Main file explorer application using heavy OOP composition."""
    
    def __init__(self, start_path: Optional[Path] = None):
        """Initialize the file explorer with all subsystems."""
        LoggingMixin.__init__(self)
        ObservableMixin.__init__(self)
        
        # Platform strategy
        self._platform_strategy = PlatformStrategyFactory.create()
        
        # Initialize tkinter
        import tkinter as tk
        from tkinter import ttk, messagebox, filedialog, simpledialog
        
        self.tk = tk
        self.ttk = ttk
        self.messagebox = messagebox
        self.filedialog = filedialog
        self.simpledialog = simpledialog
        
        # Event bus
        self._event_bus = EventBus()
        
        # Clipboard manager
        self._clipboard_manager = ClipboardManager(self._platform_strategy)
        
        # Command history for undo/redo
        self._command_history: List[Command] = []
        self._undo_index: int = -1
        
        # Navigation state
        self._current_directory: Optional[DirectoryItem] = None
        self.history: List[Path] = []
        self.history_index: int = -1
        self.show_hidden: bool = False
        
        # File storage
        self.file_items: Dict[str, FileSystemItem] = {}
        
        # Sort strategy
        self._sort_strategy: SortStrategy = SortStrategyFactory.create(SortBy.NAME)
        
        # UI Components
        self._ui_components: List[UIComponent] = []
        
        # Build main window
        self._build_window(start_path)
        
        # Setup keyboard shortcuts
        self._setup_shortcuts()
        
        self.logger.info(f"File Explorer initialized: {self._platform_strategy.get_platform_type().value}")
    
    def _build_window(self, start_path: Optional[Path]) -> None:
        """Build the main application window."""
        self.root = self.tk.Tk()
        self.root.title("FelixFs - File Explorer")
        self.root.geometry("1000x700")
        self.root.minsize(600, 400)
        
        # Create UI components
        main_frame = self.ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self._toolbar = ToolbarComponent(self, main_frame)
        self._pathbar = PathBarComponent(self, main_frame)
        
        content_frame = self.ttk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True, pady=5)
        
        self._sidebar = SidebarComponent(self, content_frame)
        self._file_list = FileListComponent(self, content_frame)
        
        self._statusbar = StatusBarComponent(self, main_frame)
        
        # Build all components
        self._toolbar.build()
        self._pathbar.build()
        self._sidebar.build()
        self._file_list.build()
        self._statusbar.build()
        
        # Navigate to initial path
        initial_path = start_path if start_path and start_path.exists() else Path.home()
        self.navigate_to(initial_path)
    
    # ------------------------------------------------------------------------
    # Navigation Methods
    # ------------------------------------------------------------------------
    
    @log_method_call
    def navigate_to(self, path: Path) -> None:
        """Navigate to a directory."""
        if not path.exists() or not path.is_dir():
            self.logger.warning(f"Invalid path: {path}")
            return
        
        # Update history
        if self.history_index == -1 or \
           (self.history and self.history[self.history_index] != self.current_path):
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]
            if self._current_directory:
                self.history.append(self._current_directory.path)
                self.history_index = len(self.history) - 1
        
        # Create directory item
        self._current_directory = DirectoryItem(path, self._platform_strategy)
        self._current_directory.invalidate_cache()
        
        # Update UI
        self._update_file_list()
        self._update_navigation_buttons()
        
        # Publish event
        self._event_bus.publish(FileSystemEvent.NAVIGATED, path)
        
        self.logger.info(f"Navigated to: {path}")
    
    def navigate_to_path(self) -> None:
        """Navigate to path from entry bar."""
        new_path = Path(self.path_var.get())
        if new_path.exists() and new_path.is_dir():
            self.navigate_to(new_path)
        else:
            self.messagebox.showerror("Invalid Path", 
                                       f"Path does not exist:\n{new_path}")
    
    def go_back(self) -> None:
        """Navigate back in history."""
        if self.history_index > 0 and self.history:
            self.history_index -= 1
            self._current_directory = DirectoryItem(
                self.history[self.history_index], 
                self._platform_strategy
            )
            self._update_file_list()
            self._update_navigation_buttons()
    
    def go_forward(self) -> None:
        """Navigate forward in history."""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self._current_directory = DirectoryItem(
                self.history[self.history_index],
                self._platform_strategy
            )
            self._update_file_list()
            self._update_navigation_buttons()
    
    def go_up(self) -> None:
        """Navigate to parent directory."""
        if self._current_directory:
            parent = self._current_directory.path.parent
            if parent != self._current_directory.path:
                self.navigate_to(parent)
    
    def refresh(self) -> None:
        """Refresh current view."""
        if self._current_directory:
            self._current_directory.invalidate_cache()
        self._update_file_list()
        self._statusbar.set_status("Refreshed", 2000)
    
    def toggle_hidden(self) -> None:
        """Toggle hidden file visibility."""
        self.show_hidden = self.show_hidden_var.get()
        self.refresh()
    
    # ------------------------------------------------------------------------
    # File Operations (Delegate to Commands)
    # ------------------------------------------------------------------------
    
    @require_selection
    def copy_selected(self) -> None:
        """Copy selected items to clipboard."""
        selected = self.get_selected_files()
        if selected:
            self._clipboard_manager.copy(selected)
            self._statusbar.set_status(self._clipboard_manager.get_status_text())
            self._event_bus.publish(FileSystemEvent.CLIPBOARD_CHANGED, selected)
    
    @require_selection
    def cut_selected(self) -> None:
        """Cut selected items to clipboard."""
        selected = self.get_selected_files()
        if selected:
            self._clipboard_manager.cut(selected)
            self._statusbar.set_status(self._clipboard_manager.get_status_text())
            self._event_bus.publish(FileSystemEvent.CLIPBOARD_CHANGED, selected)
    
    def paste(self) -> None:
        """Paste items from clipboard."""
        if self._clipboard_manager.is_empty:
            self._statusbar.set_status("Clipboard is empty")
            return
        
        command = self._clipboard_manager.paste(self._current_directory)
        if command:
            self._execute_command(command)
            self.refresh()
    
    @require_selection
    def delete_selected(self) -> None:
        """Delete selected items."""
        selected = self.get_selected_files()
        result = self.messagebox.askyesno(
            "Confirm Delete",
            f"Delete {len(selected)} item(s)?\n\nThis can be undone!",
            icon='warning'
        )
        
        if result:
            command = DeleteCommand(selected, self._platform_strategy)
            if self._execute_command(command):
                self.refresh()
    
    @require_selection
    def rename_selected(self) -> None:
        """Rename selected item."""
        selected = self.get_selected_files()
        if len(selected) != 1:
            self.messagebox.showinfo("Rename", "Select exactly one item to rename")
            return
        
        item = selected[0]
        new_name = self.simpledialog.askstring(
            "Rename", "Enter new name:", initialvalue=item.name
        )
        
        if new_name and new_name != item.name:
            command = RenameCommand(item, new_name)
            if self._execute_command(command):
                self.refresh()
    
    def create_new_folder(self) -> None:
        """Create a new folder."""
        name = self.simpledialog.askstring("New Folder", "Enter folder name:")
        if name:
            command = NewFolderCommand(self._current_directory, name)
            if self._execute_command(command):
                self.refresh()
    
    def open_selected(self) -> None:
        """Open selected file or directory."""
        selected = self.get_selected_files()
        if not selected:
            return
        
        item = selected[0]
        if item.is_directory:
            self.navigate_to(item.path)
        else:
            try:
                self._platform_strategy.open_file(item.path)
                self.logger.info(f"Opened: {item.path}")
            except Exception as e:
                self.logger.error(f"Failed to open {item.path}: {e}")
                self.messagebox.showerror("Open Failed", str(e))
    
    # ------------------------------------------------------------------------
    # Command Execution
    # ------------------------------------------------------------------------
    
    def _execute_command(self, command: Command) -> bool:
        """Execute a command and add to history."""
        success = command.execute()
        if success:
            # Clear redo stack
            if self._undo_index < len(self._command_history) - 1:
                self._command_history = self._command_history[:self._undo_index + 1]
            
            self._command_history.append(command)
            self._undo_index = len(self._command_history) - 1
            
            self._event_bus.publish(FileSystemEvent.COMMAND_EXECUTED, command)
            self._statusbar.set_status(f"Executed: {command.description}")
            
            self.logger.info(f"Command executed: {command.description}")
        else:
            self.logger.error(f"Command failed: {command.description}")
            self._statusbar.set_status("Operation failed")
        
        return success
    
    def undo(self) -> None:
        """Undo the last command."""
        if self._undo_index >= 0:
            command = self._command_history[self._undo_index]
            if command.undo():
                self._undo_index -= 1
                self._event_bus.publish(FileSystemEvent.COMMAND_UNDONE, command)
                self._statusbar.set_status(f"Undone: {command.description}")
                self.refresh()
    
    def redo(self) -> None:
        """Redo the last undone command."""
        if self._undo_index < len(self._command_history) - 1:
            self._undo_index += 1
            command = self._command_history[self._undo_index]
            if command.redo():
                self._event_bus.publish(FileSystemEvent.COMMAND_EXECUTED, command)
                self._statusbar.set_status(f"Redone: {command.description}")
                self.refresh()
    
    # ------------------------------------------------------------------------
    # UI Update Methods
    # ------------------------------------------------------------------------
    
    def _update_file_list(self) -> None:
        """Update the file list display."""
        if not self._current_directory:
            return
        
        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        self.file_items.clear()
        
        # Get and sort contents
        items = self._current_directory.get_contents(
            show_hidden=self.show_hidden,
            search_filter=self.search_var.get()
        )
        items = self._sort_strategy.sort(items)
        
        # Populate treeview
        for file_item in items:
            icon = file_item.get_file_type().name.lower() if hasattr(file_item, 'get_file_type') else "unknown"
            
            item_id = self.file_tree.insert(
                '', 'end',
                text=f"{icon} {file_item.name}",
                values=(
                    file_item.get_size_human(),
                    'Directory' if file_item.is_directory else 
                    file_item.path.suffix.upper()[1:] or 'File',
                    file_item.modified_time.strftime('%Y-%m-%d %H:%M:%S')
                )
            )
            self.file_items[item_id] = file_item
        
        # Update status
        total_size = sum(f.size for f in items if not f.is_directory)
        self._statusbar.update_file_stats(len(items), total_size, self._current_directory.path)
        
        # Update path bar
        self.path_var.set(str(self._current_directory.path))
    
    def _update_navigation_buttons(self) -> None:
        """Update navigation button states."""
        self._toolbar.update_navigation_buttons(
            self.history_index > 0,
            self.history_index < len(self.history) - 1
        )
    
    def _update_tree_selection(self) -> None:
        """Update sidebar tree selection."""
        if not self._current_directory:
            return
        
        current_str = str(self._current_directory.path)
        
        def find_path(node=''):
            for item in self.tree.get_children(node):
                values = self.tree.item(item)['values']
                if values and len(values) > 0 and values[0] == current_str:
                    self.tree.selection_set(item)
                    self.tree.see(item)
                    return True
                if find_path(item):
                    return True
            return False
        
        find_path()
    
    # ------------------------------------------------------------------------
    # Selection Methods
    # ------------------------------------------------------------------------
    
    def get_selected_files(self) -> List[FileSystemItem]:
        """Get list of selected file system items."""
        selected = []
        for item_id in self.file_tree.selection():
            if item_id in self.file_items:
                selected.append(self.file_items[item_id])
        return selected
    
    def select_all(self) -> None:
        """Select all items in the file list."""
        for item in self.file_tree.get_children():
            self.file_tree.selection_add(item)
    
    def on_item_select(self, event) -> None:
        """Handle file selection change."""
        selected = self.get_selected_files()
        if selected:
            self._statusbar.set_status(f"Selected {len(selected)} item(s)")
        self._event_bus.publish(FileSystemEvent.SELECTION_CHANGED, selected)
    
    # ------------------------------------------------------------------------
    # Context Menu
    # ------------------------------------------------------------------------
    
    def show_context_menu(self, event) -> None:
        """Show right-click context menu."""
        item = self.file_tree.identify_row(event.y)
        if item:
            self.file_tree.selection_set(item)
        
        menu = self.tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Open", command=self.open_selected)
        menu.add_separator()
        menu.add_command(label="Copy", command=self.copy_selected)
        menu.add_command(label="Cut", command=self.cut_selected)
        menu.add_command(label="Paste", command=self.paste)
        menu.add_separator()
        menu.add_command(label="Rename", command=self.rename_selected)
        menu.add_command(label="Delete", command=self.delete_selected)
        menu.add_separator()
        menu.add_command(label="Properties", command=self.show_properties)
        menu.add_command(label="Undo", command=self.undo)
        menu.add_command(label="Redo", command=self.redo)
        
        menu.post(event.x_root, event.y_root)
    
    # ------------------------------------------------------------------------
    # Properties Dialog
    # ------------------------------------------------------------------------
    
    def show_properties(self) -> None:
        """Show file properties dialog."""
        selected = self.get_selected_files()
        if not selected:
            return
        
        item = selected[0]
        
        prop_window = self.tk.Toplevel(self.root)
        prop_window.title(f"Properties - {item.name}")
        prop_window.geometry("500x450")
        prop_window.transient(self.root)
        prop_window.grab_set()
        
        row = 0
        properties = [
            ("Name:", item.name),
            ("Path:", str(item.path)),
            ("Type:", item.get_file_type().name if hasattr(item, 'get_file_type') else "Unknown"),
            ("Size:", item.get_size_human()),
            ("Modified:", item.modified_time.strftime('%Y-%m-%d %H:%M:%S')),
            ("Created:", item.created_time.strftime('%Y-%m-%d %H:%M:%S')),
            ("Hidden:", "Yes" if item.is_hidden else "No"),
        ]
        
        # Add type-specific properties
        if isinstance(item, ImageFile):
            properties.append(("Dimensions:", str(item.dimensions or "Unknown")))
            properties.append(("Transparency:", "Yes" if item.has_transparency else "No"))
        elif isinstance(item, CodeFile):
            properties.append(("Language:", item.language))
            properties.append(("Lines:", str(item.line_count)))
            properties.append(("Test File:", "Yes" if item.is_test_file else "No"))
        elif isinstance(item, ArchiveFile):
            properties.append(("Contents:", str(item.content_count)))
        elif isinstance(item, DirectoryItem):
            properties.append(("Items:", str(item.item_count)))
        
        for label, value in properties:
            self.ttk.Label(prop_window, text=label, 
                          font=('TkDefaultFont', 10, 'bold')).grid(
                row=row, column=0, sticky='e', padx=10, pady=5
            )
            self.ttk.Label(prop_window, text=str(value), wraplength=300).grid(
                row=row, column=1, sticky='w', padx=10, pady=5
            )
            row += 1
        
        close_btn = self.ttk.Button(prop_window, text="Close", 
                                     command=prop_window.destroy)
        close_btn.grid(row=row, column=0, columnspan=2, pady=20)
    
    # ------------------------------------------------------------------------
    # Keyboard Shortcuts
    # ------------------------------------------------------------------------
    
    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        self.root.bind('<Control-c>', lambda e: self.copy_selected())
        self.root.bind('<Control-x>', lambda e: self.cut_selected())
        self.root.bind('<Control-v>', lambda e: self.paste())
        self.root.bind('<Control-z>', lambda e: self.undo())
        self.root.bind('<Control-y>', lambda e: self.redo())
        self.root.bind('<Delete>', lambda e: self.delete_selected())
        self.root.bind('<F5>', lambda e: self.refresh())
        self.root.bind('<BackSpace>', lambda e: self.go_back())
        self.root.bind('<Control-a>', lambda e: self.select_all())
        self.root.bind('<F2>', lambda e: self.rename_selected())
        self.root.bind('<Return>', lambda e: self.open_selected())
    
    # ------------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------------
    
    @property
    def current_path(self) -> Optional[Path]:
        """Get current directory path."""
        return self._current_directory.path if self._current_directory else None
    
    @property
    def platform_strategy(self) -> PlatformStrategy:
        return self._platform_strategy
    
    @property
    def sort_strategy(self) -> SortStrategy:
        return self._sort_strategy
    
    @sort_strategy.setter
    def sort_strategy(self, strategy: SortStrategy) -> None:
        self._sort_strategy = strategy
        self.refresh()
    
    # ------------------------------------------------------------------------
    # Application Lifecycle
    # ------------------------------------------------------------------------
    
    def run(self) -> None:
        """Run the application."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {e}", exc_info=True)
            raise


# ============================================================================
# REMAINING UI COMPONENTS
# ============================================================================

class SidebarComponent(UIComponent):
    """Directory tree sidebar UI component."""
    
    def _build_impl(self, parent) -> None:
        app = self._app
        
        sidebar_frame = app.ttk.LabelFrame(parent, text="Directories", width=200)
        sidebar_frame.pack(side='left', fill='y', padx=(0, 5))
        sidebar_frame.pack_propagate(False)
        self._widget = sidebar_frame
        
        app.tree = app.ttk.Treeview(sidebar_frame, show='tree', height=20)
        tree_scroll = app.ttk.Scrollbar(sidebar_frame, orient='vertical', 
                                         command=app.tree.yview)
        app.tree.configure(yscrollcommand=tree_scroll.set)
        
        app.tree.pack(side='left', fill='both', expand=True)
        tree_scroll.pack(side='right', fill='y')
        
        app.tree.bind('<<TreeviewSelect>>', app.on_item_select)
        
        self._populate_tree()
    
    def on_tree_select(self, event) -> None:
        """Handle tree selection (delegated from app)."""
        app = self._app
        selection = app.tree.selection()
        if selection:
            item = selection[0]
            values = app.tree.item(item)['values']
            if values and len(values) > 0:
                path = Path(values[0])
                if path.exists() and path.is_dir():
                    app.navigate_to(path)
    
    def _populate_tree(self) -> None:
        """Populate the directory tree."""
        app = self._app
        try:
            for item in app.tree.get_children():
                app.tree.delete(item)
            
            drives = app.platform_strategy.get_drives()
            for drive in drives:
                if drive.exists():
                    node = app.tree.insert('', 'end', text=str(drive), 
                                           values=(str(drive),), open=False)
                    app.tree.insert(node, 'end', text='loading...')
        except Exception as e:
            app.logger.error(f"Failed to populate tree: {e}")
    
    def refresh(self) -> None:
        """Refresh the directory tree."""
        super().refresh()
        self._populate_tree()


class StatusBarComponent(UIComponent):
    """Status bar UI component."""
    
    def __init__(self, app: 'FileExplorer', parent: Any):
        super().__init__(app, parent)
        self._after_id = None
    
    def _build_impl(self, parent) -> None:
        app = self._app
        
        self._widget = app.ttk.Frame(parent)
        self._widget.pack(fill='x', pady=(5, 0))
        
        app.status_label = app.ttk.Label(self._widget, text="Ready", relief='sunken')
        app.status_label.pack(side='left', fill='x', expand=True)
        
        app.item_count_label = app.ttk.Label(self._widget, text="0 items", 
                                              relief='sunken', width=15)
        app.item_count_label.pack(side='right')
    
    def set_status(self, text: str, timeout_ms: int = 0) -> None:
        """Set status text with optional auto-clear."""
        app = self._app
        app.status_label.config(text=text)
        
        if self._after_id:
            app.root.after_cancel(self._after_id)
        
        if timeout_ms > 0:
            self._after_id = app.root.after(timeout_ms, 
                                             lambda: app.status_label.config(text="Ready"))
    
    def update_file_stats(self, item_count: int, total_size: int, path: Path) -> None:
        """Update status bar with file statistics."""
        app = self._app
        size_str = self._format_size(total_size)
        app.item_count_label.config(text=f"{item_count} items")
        app.status_label.config(
            text=f"{item_count} items | Total size: {size_str} | Location: {path}"
        )
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format size to human readable string."""
        if size_bytes == 0:
            return "0 B"
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1
        return f"{size:.1f} {units[unit_index]}"


# ============================================================================
# SETUP AND ENTRY POINT
# ============================================================================

def setup_logging(debug_mode: bool = False) -> None:
    """Set up logging configuration."""
    log_dir = Path.home() / ".file_explorer" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"explorer_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.DEBUG if debug_mode else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AetherFS - Advanced File Explorer")
    parser.add_argument('--debug', '-d', action='store_true', 
                       help='Enable debug logging')
    parser.add_argument('--path', '-p', type=str, 
                       help='Starting directory path')
    args = parser.parse_args()
    
    setup_logging(debug_mode=args.debug)
    logger = logging.getLogger(__name__)
    
    try:
        start_path = Path(args.path) if args.path else None
        logger.info("Starting AetherFS File Explorer")
        
        app = FileExplorer(start_path=start_path)
        app.run()
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
