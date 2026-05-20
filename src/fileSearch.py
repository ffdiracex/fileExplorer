from typing import List, Generator, Optional, Any, Tuple
from file import Path, File
import fnmatch
from datetime import datetime

class FileSearch:
    """search engine functioning for file lookup"""

    @staticmethod
    def search_by_name(root: Path, pattern: str, recursive: bool = True) -> Generator[File, None, None]:
        """Search files by name pattern, attempt at supporting wildcards e.g *.csv"""
        pattern = pattern.lower()

        if recursive:
            iterator = root.rglob("*")
        else:
            iterator = root.rglob("*")
        
        for item in iterator:
            if fnmatch.fnmatch(item.name.lower(), pattern):
                yield File(item)
    
    @staticmethod
    def search_by_size(root: Path, min_bytes: int = 0, max_bytes: Optional[int] = None) -> Generator[File, None, None]:
        """Search files by providing a size range"""
        for item in root.rglob("*"):
            if item.is_file():
                size = item.stat().st_size
                if size >= min_bytes and (max_bytes is None or size <= max_bytes):
                    yield File(item)
    
    @staticmethod
    def search_by_date(root: Path, after: Optional[datetime] = None, before: Optional[datetime] = None
    ) -> Generator[File, None, None]:
        """search files by modification date """
        for item in root.rglob("*"):
            if item.is_file():
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                if after and mtime < after:
                    continue
                if before and mtime > before:
                    continue
                yield File(item)
    
    @staticmethod
    def search_by_content(root: Path, text: str, extensions: Optional[List[str]] = None
    ) -> Generator[File, None, None]:
        """Search for text inside files """
        text = text.lower()
        for item in root.rglob("*"):
            if item.is_file():
                if extensions and item.suffix.lower() not in extensions:
                    continue
                try:
                    #For large files, read in chunks
                    content = item.read_text(encoding='utf-8', errors='ignore')
                    if text in content.lower():
                        yield File(item)
                except Exception:
                    continue
