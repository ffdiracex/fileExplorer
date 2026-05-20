import os
import platform
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from file import File
class ThumbnailGenerator:
	"""
	Generate file thumbnails for the UI, a little hint for what type of file it is.
	"""
	def __init__(self, cache_dir: Optional[Path] = None):
		self.cache_dir = cache_dir or Path.home() / ".file_explorer_cache" / "thumbnails"
		self.cache_dir.mkdir(parents=True, exist_ok=True)

		#ASCII art for the different file types
		self.ascii_art = {
			'folder': [
				"---DIR---"
				],
			'image': [
				"---IMG---"
				],
			'video': [
				"---VID---"
				],
			'audio': [
				"---WAV---"
				],
			'pdf': [
				"---PDF---"
				],
			'archive': [
				"---ARC---"
				],
			'text': [
				"---TXT---"
				],
			'code': [
				"---<T>---"
				],
			'executable': [
				"---EXE---"
				],
			'spreadsheet': [
				"---CSV---"
				],
			'presentation': [
				"---PWP---"
				],
			'generic': [
				"---GEN---"
			]
		}

	def get_thumbnail(self, file: File) -> str:
		"""  Get ASCII thumbnail"""

		if file.is_directory:
			art_type = 'folder'
		else:
			art_type = self._get_file_type(file.extensions.lower())
		
		#Fallback to generic if not found
		if art_type not in self.ascii_art:
			art_type = 'generic'
		
		return "\n".join(self.ascii_art[art_type])
	
	def _get_file_type(self, extension: str) -> str:
		"""Determine file type based on its extension """
		if extension in { '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico', '.svg' }:
			return 'image'

		if extension in { '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg' }:
			return 'video'
		
		if extension in { '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus'}:
			return 'audio'
		
		if extension == 'pdf':
			return 'pdf'
		
		if extension in { '.txt', '.md', '.log', '.cfg', '.conf', '.rtf', '.rst', '.ini'}:
			return 'text'
		
		if extension in { '.doc', '.docx'}:
			return 'text'
		
		if extension in { '.xls', '.xlsx', '.csv', '.ods'}:
			return 'spreadsheet'
		
		if extension in { '.ppt', '.pptx', '.odp'}:
			return 'presentation'
		
		if extension in { '.exe', '.msi', '.app', '.deb', '.sh', '.rpm', '.bat', '.cmd', '.com'}:
			return 'executable'
		
		if extension in { '.py', '.js', '.html', '.css', '.java', '.c', '.cpp', '.h', '.hpp', '.hxx', '.cxx', '.php',
						'.rb', '.go', '.rs', '.swift', '.kt', '.ts', 'jsx', '.tsx', '.sql', '.sh', '.pl', '.lua', '.m',
							'.json', '.yaml', '.yml', '.r'}:
							return 'code'
		
		return 'generic'
	
	def get_colored_thumbnail(self, file: File) -> str:
		""" Get the colored version of the thumbnail, using escape codes """

		colors = {
			'folder': '\033[1;34m', #bold blue, dirs are often blue in editors on unix, like dolphin and gnome
			'image': '\033[1;35m', #bold magenta
			'video': '\033[1;31m', #bold red
			'audio': '\033[1;32m', #bold green
			'pdf': '\033[1;33m', #bold yellow
			'archive': '\033[1;36m', #bold cyan
			'executable': '\033[1;32m', #bold green
			'code': '\033[1;33m', #bold yellow
			'text': '\033[1;37m', #bold white
			'spreadsheet': '\033[1;32m', #bold green
			'presentation': '\033[1;35m', #bold magenta
			'generic': '\033[1;37m' #bold white
		}

		reset = '\033[0m'

		#Get the art and determine the type
		if file.is_directory:
			art_type = "folder"
		else:
			art_type = self._get_file_type(file.extensions.lower())
		
		if art_type not in colors:
			art_type = 'generic'
		
		art = self.get_thumbnail(file)
		color = colors.get(art_type, colors['generic'])

		#apply color to each line
		colored_lines = [color + line + reset for line in art.split('\n')]
		return "\n".join(colored_lines)
	
	def get_compact_thumbnail(self, file: File) -> str:
		"""Smaller version for smaller spaces """
		if file.is_directory:
			return "[D]"
		
		art_type = self._get_file_type(file.extensions.lower())

		compact_map = {
			'image': '[I]',
            'video': '[V]',
            'audio': '[A]',
            'pdf': '[P]',
            'archive': '[Z]',
            'text': '[T]',
            'code': '[C]',
            'executable': '[X]',
            'spreadsheet': '[S]',
            'presentation': '[O]',
            'generic': '[F]'
		}

		return compact_map.get(art_type, '[F]')
	
	def get_thumbnail_grid(self, files: List[File], cols: int = 4) -> str:
		"""Generate grids for multiple file thumbnails on same col """

		if not files: return ""

		#limit to a good amount
		files = files[:cols * 10]

		thumbnails = []
		for file in files:
			thumb_lines = self.get_thumbnail(file).split('\n')
			thumbnails.append((file, thumb_lines))
		
		#build grid
		grid_lines = []
		thumb_height: int = 3

		for row_start in range(0, len(thumbnails), cols):
			row_items = thumbnails[row_start:row_start + cols]

			#add each line
			for line_idx in range(thumb_height):
				line_parts = []
				for file, thumb_lines in row_items:
					if line_idx < len(thumb_lines):
						line_parts.append(thumb_lines[line_idx])
					else: #add some empty space
						line_parts.append("  ")
				
				#set some space between the thumbnails
				grid_lines.append("  ".join(line_parts))
			
			#add file names below the thumbnail
			name_parts = []
			for file, _ in row_items:
				name = file.name
				if len(name) > 11:
					name = name[:9] + "..."
				name_parts.append(name.center(7))
			grid_lines.append(" ".join(name_parts))
			grid_lines.append("") #some space between them

		return "\n".join(grid_lines)

	def get_tree_thumbnail(self, file: File, depth: int = 0, is_last: bool = False,
			prefix: str = "") -> str:
			"""Get thumbnail for directory trees """

			if depth == 0:
				#root level, i.e. beginning, so no prefix
				branch = ""
			else:
				if is_last:
					branch = prefix + "^_"
					new_prefix = prefix + "  "
				else:
					branch = prefix + "|-- " #NOTE: change this if it renders badly
					new_prefix = prefix + "|   "
			
			thumb = self.get_compact_thumbnail(file)

			if file.is_directory:
				color = '\033[1;34m' #blue
				reset = '\033[1;0m'
				name_display = f"{color}{file.name}{reset}"
			else:
				name_display = file.name
			
			return f"{branch}{thumb} {name_display}"
	
	def render_directory_tree(self, root_path: Path, max_depth: int = 3,
			current_depth: int = 0, prefix: str = "") -> str:
			""" render the directory tree """
			if current_depth > max_depth:
				return ""
			
			result = []
			try:
				root_file = File(root_path)
				items = sorted([File(p) for p in root_path.iterdir() if not p.name.startswith('.')],
					key=lambda x: (not x.is_directory, x.name.lower())) #FIXME: will this work?
				
				for i, item in enumerate(items):
					is_last = (i == len(items) - 1)

					#add current item
					result.append(self.get_tree_thumbnail(item, current_depth, is_last, prefix))

					#recurse into directories
					if item.is_directory and current_depth < max_depth:
						subtree = self.render_directory_tree(item.path, max_depth, current_depth + 1,
							prefix + ("  " if is_last else "|"))
						
						if subtree:
							result.append(subtree)
			except PermissionError:
				pass

			return "\n".join(result)
	
	def clear_cache(self):
		""" clear thumbnail cache """
		if self.cache_dir.exists():
			for cache_file in self.cache_dir.glob("*"):
				cache_file.unlink()



