"""
Path utilities and project name extraction.
"""

import os
import platform
import pathlib
from typing import Optional


def get_project_name() -> str:
    """Get the current project name from the current working directory."""
    try:
        current_dir = pathlib.Path.cwd()
        project_name = current_dir.name
        
        # Skip common container directory names
        container_dirs = ['Documents', 'Projects', 'Code', 'workspace', 'repos', 'git', 'src', 'codebase']
        if project_name in container_dirs and current_dir.parent.exists():
            project_name = current_dir.parent.name
        
        return project_name
    except Exception:
        return "unknown"


def normalize_path(path: str) -> pathlib.Path:
    """Normalize and resolve a path."""
    return pathlib.Path(path).expanduser().resolve()


def get_home_directory() -> pathlib.Path:
    """Get the user's home directory."""
    return pathlib.Path.home()


def get_cursor_root() -> pathlib.Path:
    """Get the Cursor application data root directory."""
    home = pathlib.Path.home()
    system = platform.system()
    
    if system == "Darwin":
        return home / "Library" / "Application Support" / "Cursor"
    elif system == "Windows":
        return home / "AppData" / "Roaming" / "Cursor"
    elif system == "Linux":
        return home / ".config" / "Cursor"
    else:
        raise RuntimeError(f"Unsupported OS: {system}")


def get_claude_history_path(project_path: Optional[str] = None) -> pathlib.Path:
    """Get the Claude Code history path for a project."""
    if project_path is None:
        project_path = os.getcwd()
    
    encoded_path = project_path.replace('/', '-')
    history_base = pathlib.Path.home() / '.claude' / 'projects'
    return history_base / encoded_path


def extract_project_name_from_path(root_path: str, debug: bool = False) -> str:
    """Extract a project name from a path, skipping user directories."""
    if not root_path or root_path == '/':
        return "Root"
        
    path_parts = [p for p in root_path.split('/') if p]
    
    # Skip common user directory patterns
    project_name = None
    home_dir_patterns = ['Users', 'home']
    
    # Get current username for comparison
    current_username = os.path.basename(os.path.expanduser('~'))
    
    # Find user directory in path
    username_index = -1
    for i, part in enumerate(path_parts):
        if part in home_dir_patterns:
            username_index = i + 1
            break
    
    # If this is just /Users/username with no deeper path, don't use username as project
    if username_index >= 0 and username_index < len(path_parts) and path_parts[username_index] == current_username:
        if len(path_parts) <= username_index + 1:
            return "Home Directory"
    
    if username_index >= 0 and username_index + 1 < len(path_parts):
        # First try specific project directories we know about by name
        known_projects = ['genaisf', 'cursor-view', 'cursor', 'cursor-apps', 'universal-github', 'inquiry']
        
        # Look at the most specific/deepest part of the path first
        for i in range(len(path_parts)-1, username_index, -1):
            if path_parts[i] in known_projects:
                project_name = path_parts[i]
                break
        
        # If no known project found, use the last part of the path as it's likely the project directory
        if not project_name and len(path_parts) > username_index + 1:
            # Check if we have a structure like /Users/username/Documents/codebase/project_name
            if 'Documents' in path_parts and 'codebase' in path_parts:
                doc_index = path_parts.index('Documents')
                codebase_index = path_parts.index('codebase')
                
                # If there's a path component after 'codebase', use that as the project name
                if codebase_index + 1 < len(path_parts):
                    project_name = path_parts[codebase_index + 1]
            
            # If no specific structure found, use the last component of the path
            if not project_name:
                project_name = path_parts[-1]
        
        # Skip username as project name
        if project_name == current_username:
            project_name = 'Home Directory'
        
        # Skip common project container directories
        project_containers = ['Documents', 'Projects', 'Code', 'workspace', 'repos', 'git', 'src', 'codebase']
        if project_name in project_containers:
            # Don't use container directories as project names
            # Try to use the next component if available
            container_index = path_parts.index(project_name)
            if container_index + 1 < len(path_parts):
                project_name = path_parts[container_index + 1]
        
        # If we still don't have a project name, use the first non-system directory after username
        if not project_name and username_index + 1 < len(path_parts):
            system_dirs = ['Library', 'Applications', 'System', 'var', 'opt', 'tmp']
            for i in range(username_index + 1, len(path_parts)):
                if path_parts[i] not in system_dirs and path_parts[i] not in project_containers:
                    project_name = path_parts[i]
                    break
    else:
        # If not in a user directory, use the basename
        project_name = path_parts[-1] if path_parts else "Root"
    
    # Final check: don't return username as project name
    if project_name == current_username:
        project_name = "Home Directory"
    
    return project_name if project_name else "Unknown Project" 