#main.py, main executable file for the file explorer. can be run in debug mode, NOTE: check the terminal for debug logs!.

import tkinter as tkinter
from typing import List, Tuple, Any, Optional
from file import Path, File
from fileDisplay import DisplayManager, SortBy, ViewMode
from clipboard import Clipboard, ClipboardAction
from settings import Settings
from fileSearch import FileSearch
from sideBar import DirectoryTree
from thumbnail import ThumbnailGenerator
from fileOp import FileOperations
from fileNav import FileNavigator


class FileExplorerGUI:
    """ Main GUI, not in seperate file due to the boilerplate setup for tkinter initialization """

    def __init__(self, root):
        self.root = root