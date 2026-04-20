import shutil
from typing import Optional, Tuple, Any, Callable, List
from file import Path


class FileOperations:
    """Handle file system operations with progress reporting and logging """

    @staticmethod
    def copy(source: Path, destination: Path, on_progress: Optional[Callable] = None) -> bool:
        """Copy file or directory with progress noticing"""
        try:
            if source.is_file():
                if on_progress:
                    total = source.stat().st_size
                    copied = 0
                    #TODO: Implement chunked copy with progress
                shutil.copy2(source, destination)
            else:
                shutil.copytree(source, destination)
            return True
        except Exception as e:
            print(f"Copy failed: {e}")
            return False
        
    @staticmethod
    def move(source: Path, destination: Path) -> bool:
        """Move/Rename file or dir """
        try:
            shutil.move(source, destination)
            return True
        except Exception as e:
            print(f"move failed: {e}")
            return False
    
    @staticmethod
    def delete(path: Path, permanently: bool = False) -> bool:
        """Delete file or dir"""
        try:
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)
            return True
        except Exception as e:
            print(f"delete failed: {e}")
            return False
    
    @staticmethod
    def create_directory(path: Path) -> bool:
        """Create new directory """
        try:
            path.mkdir(parents=True, exist_ok=False)
            return True
        except Exception:
            return False
    
    @staticmethod
    def create_empty_file(path: Path) -> bool:
        """Create new empty file"""
        try:
            path.touch()
            return True
        except Exception:
            return False
        