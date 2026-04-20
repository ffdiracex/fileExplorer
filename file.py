'''
Class representing the file hierarchy and properties about a file (s)
'''
#ifndef file_py LARP
#define file_py LARP
#pragma once LARP

import os
import stat
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Union, Any


class File:
    """
    A cross-platform file representation for a file explorer.
    Represent metadata, permissions, ownership etc.
    """

    def __init__(self, path: Union[str, Path]):
        """ init a File object from a path provided by user
        @arg1 path: Path to the file or directory
        """
        self.path = Path(path)
        self._stat_result = None
        self._refresh()
    
    def _refresh(self) -> None:
        """ Refresh the file statistics from the filesystem """
        try:
            self._stat_result = self.path.stat()
        except OSError:
            self._stat_result = None
    
    @property
    def exists(self) -> bool:
        """does file exist? bool """
        return self.path.exists()
    
    @property
    def name(self) -> str:
        """Return the name of file """
        return self.path.name
    
    @property
    def extensions(self) -> str:
        """Get the file extension, including the dot """
        return self.path.suffix
    
    @property
    def is_directory(self) -> bool:
        """IS path DIR? bool """
        return self.path.is_dir()
    
    @property
    def is_file(self) -> bool:
        """Check if this is a regular file """
        return self.path.is_file()
    
    @property
    def is_symlink(self) -> bool:
        """Check if this is a symbolic link"""
        return self.path.is_symlink()
    
    @property
    def size(self) -> int:
        """
        Get the file size, in bytes
        return file size as int, or 0 if it doesn't exist (exists() == 0)
        """
        if self._stat_result:
            return self._stat_result.st_size
        return 0
    
    @property
    def size_human(self) -> str:
        """
        Make the file size human-readable (i.e. "2.0 MiB" for instance )
        return a formatted string
        """
        size_bytes = self.size
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'] #hopefully user doesn't use PB
        unit_index = 0 #default

        while size_bytes >= 1024 and unit_index < len(units) - 1:
            size_bytes /= 1024.0
            unit_index += 1 #increment by 1 until we find the right unit

        return f"{size_bytes:.1f} {units[unit_index]}"
    
    @property
    def created_time(self) -> Optional[datetime]:
        """Get the time of creation, i.e. when was file created? OPTIONAL"""
        if self._stat_result:
            try:
                # st_ctime on windows is creation time,
                # but on linux it is metadata change time 
                return datetime.fromtimestamp(self._stat_result.st_birthtime)
            except OSError:
                pass
        return None
    
    @property
    def modified_time(self) -> Optional[datetime]:
        """ modified time ? """
        if self._stat_result:
            try:
                return datetime.fromtimestamp(self._stat_result.st_mtime)
            except OSError:
                pass
        return None
    
    @property
    def accessed_time(self) -> Optional[datetime]:
        """Get last accessed time"""
        if self._stat_result:
            try:
                return datetime.fromtimestamp(self._stat_result.st_atime)
            except OSError:
                pass
        return None
    
    @property
    def mode(self) -> int:
        """
        Get file mode/permission as integer bitmask

        returns:
            st_mode bitmask or 0 if unavailable
        """

        if self._stat_result:
            return self._stat_result.st_mode
        return 0
    
    @property
    def permission_octal(self) -> str:
        """
        Get file permission in octal format, e.g 0o644 0o543
        for unix-systems
        """
        if platform.system() != "Windows" and self._stat_result:
            return oct(stat.S_IMODE(self._stat_result.st_mode)) #get the result of chmod
        return "N/A"
    
    @property
    def permissions_rwx(self) -> str:
        """
        Get file permission in rwx format (eg. 'rw-r--r--')
        On Windows, only indicates read-only status """
        if not self._stat_result:
            return "----------"
        
        if platform.system() == "Windows":
            #for windows we only need to check read-only attribute
            is_readonly = not (self.path.stat().st_mode & stat.S_IWRITE)
            perms = "r--" if is_readonly else "rw-"
            #windows doesn't have group permissions like unix
            return f"{perms}{perms}{perms}"
        else:
            #unix
            mode = self._stat_result.st_mode
            perms = []
            for who in [stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR,
                        stat.S_IRGRP, stat.S_IWGRP, stat.IXGRP,
                        stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH]:
                perms.append('r' if mode & who else '-')
            return ''.join(perms)
    
    @property
    def is_readable(self) -> bool:
        """ Check if file is readable by current user, check: $whoami """
        return os.access(self.path, os.R_OK)
    
    @property
    def is_writable(self) -> bool:
        """Check if file is writable by the current user. """
        return os.access(self.path, os.W_OK)
    
    @property
    def is_executable(self) -> bool:
        """Check if file is executable {$chmod +x }"""
        if platform.system() == "Windows":
            #On windows, check by the file extension
            executable_extensions = { '.exe', '.bat', '.cmd', '.ps1', '.com'}
            return self.extensions.lower() in executable_extensions
        else:
            return os.access(self.path, os.X_OK)
    
    @property
    def owner(self) -> str:
        """
        Who owns the file? return the owner of $file, "N/A" if None
        """
        if platform.system() == "Windows":
            return self._get_windows_owner()
        else:
            return self._get_unix_owner()
    
    def _get_unix_owner(self) -> str:
        """For unix, get owner """
        try:
            import pwd
            if self._stat_result:
                return pwd.getpwuid(self._stat_result.st_uid).pw_name
        except (ImportError, KeyError, OSError):
            pass
        return "N/A"
    
    def _get_windows_owner(self) -> str:
        """ get the owner on windows system"""
        try:
            import win32security
            import win32file

            sd = win32security.GetFileSecurity(
                str(self.path),
                win32security.OWNER_SECURITY_INFORMATION
            )

            owner_sid = sd.GetSecurityDescriptorOwner()
            name, domain, _ = win32security.LookupAccountSid(None, owner_sid)
            return f"{domain}\\{name}"
        except ImportError:
            #Fallback when pywin32 is not installed
            return "Windows (pywin32 required)"
        except Exception:
            return "Unknown"
    
    @property
    def group(self) -> str:
        """
        Get file group name.
        Only meaningful on Unix-like systems.
        """
        if platform.system() == "Windows":
            return "N/A" # windows doesn't have the typical group hierarchy
        
        try:
            import grp
            if self._stat_result:
                return grp.getgrgid(self._stat_result.st_gid).gr_name
        except (ImportError, KeyError, OSError):
            pass
        return "Unknown"
    
    @property
    def is_hidden(self) -> bool:
        """
        check if file is hidden, probably via '.file' attribute
        """
        if platform.system() == "Windows":
            return self._is_hidden_windows()
        else:
            #On unix, hidden file start with '.'
            return self.name.startswith('.')

    def  _is_hidden_winows(self) -> bool:
        """check hidden attributes on windows """
        try:
            if platform.system() == "Windows":
                import ctypes
                #GetFileAttributesW is the Windows API for file attributes
                GetFileAttributesW = ctypes.windll.kernel32.GetFileAttributesW
                GetFileAttributesW.argtypes = [ctypes.c_wchar_p]
                GetFileAttributesW.restype = ctypes.c_uint32

                FILE_ATTRIBUTE_HIDDEN = 0x2
                attrs = GetFileAttributesW(str(self.path))
                return bool(attrs & FILE_ATTRIBUTE_HIDDEN)
        except Exception:
            pass
        return False
    
    def get_icon_name(self) -> str:
        """Get an appropriate icon name based on file type"""
        if self.is_directory:
            return "folder"
        icon_map = {
            '.txt': 'text-file',
            '.pdf': 'pdf-file',
            '.jpg': 'image-file', '.jpeg': 'image-file', '.png': 'image-file',
            '.gif': 'image-file', '.bmp': 'image-file', '.svg': 'image-file',
            '.mp3': 'audio-file', '.wav': 'audio-file', '.flac': 'audio-file',
            '.mp4': 'video-file', '.avi': 'video-file', '.mov': 'video-file',
            '.py': 'python-file',
            '.html': 'html-file', '.css': 'css-file', '.js': 'javascript-file',
            '.exe': 'executable-file', '.msi': 'installer-file',
            '.zip': 'archive-file', '.rar': 'archive-file', '.7z': 'archive-file',
            '.doc': 'word-file', '.docx': 'word-file',
            '.xls': 'excel-file', '.xlsx': 'excel-file',
            '.ppt': 'powerpoint-file', '.pptx': 'powerpoint-file',
        }

        return icon_map.get(self.extensions.lower(), 'generic-file')
    
    def as_dict(self) -> dict:
        """For serialization"""
        return {
            'name': self.name,
            'path': self.path,
            'size_bytes': self.size,
            'size_human': self.size_human,
            'is_directory': self.is_directory,
            'is_file': self.is_file,
            'is_symlink': self.is_symlink,
            'is_hidden': self.is_hidden,
            'extension': self.extensions,
            'created': self.created_time.isoformat() if self.created_time else None,
            'modified': self.modified_time.isoformat() if self.modified_time else None,
            'accessed': self.accessed_time.isoformat() if self.accessed_time else None,
            'permission_rwx': self.permissions_rwx,
            'permission_octal': self.permission_octal,
            'owner': self.owner,
            'group': self.group,
            'is_readable': self.is_readable,
            'is_writable': self.is_writable,
            'is_executable': self.is_executable,
            'icon': self.get_icon_name(),
        }
    
    def __str__(self) -> str:
        """String representation of the file """
        if self.is_directory:
            return f"[DIR] {self.name}"
        else:
            return f"[FILE] {self.name} ({self.size_human})"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging"""
        return f"File(path='{self.path}', size={self.size}, is_dir={self.is_directory})"

#endif