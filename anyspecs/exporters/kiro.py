"""
Kiro exporter
"""

import os
import datetime
from pathlib import Path
from typing import Dict, Any, List

from ..core.extractors import BaseExtractor
from ..utils.paths import get_project_name


class KiroExtractor(BaseExtractor):
    """Kiro record extractor"""
    
    def __init__(self):
        super().__init__('kiro')
    
    def extract_chats(self) -> List[Dict[str, Any]]:
        """Extract chats from .kiro directory"""
        kiro_path = Path.cwd() / '.kiro'
        
        if not kiro_path.exists() or not kiro_path.is_dir():
            self.logger.debug(f"No .kiro directory found at: {kiro_path}")
            return []
        
        # Get all markdown files
        markdown_files = self._get_markdown_files(kiro_path)
        if not markdown_files:
            self.logger.debug("No markdown files found in .kiro directory")
            return []
        
        # Combine all document contents into a chat session
        combined_content = self._combine_markdown_files(markdown_files)
        
        if not combined_content:
            self.logger.debug("No content found in markdown files")
            return []
        
        # Create chat session
        chat_session = self._create_chat_session(combined_content, kiro_path)
        
        return [chat_session]
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List available Kiro sessions"""
        kiro_path = Path.cwd() / '.kiro'
        
        if not kiro_path.exists():
            return []
        
        markdown_files = self._get_markdown_files(kiro_path)
        if not markdown_files:
            return []
        
        # Get latest modification time
        latest_mtime = max(f.stat().st_mtime for f in markdown_files)
        date_str = datetime.datetime.fromtimestamp(latest_mtime).strftime("%Y-%m-%d %H:%M")
        
        # Calculate total file count as message count
        file_count = len(markdown_files)
        
        # Generate preview
        preview = f"Kiro records contain {file_count} markdown files"
        if markdown_files:
            first_file = markdown_files[0]
            try:
                with open(first_file, 'r', encoding='utf-8') as f:
                    first_lines = f.read(100).replace('\n', ' ').strip()
                    if first_lines:
                        preview += f": {first_lines}..."
            except Exception:
                pass
        
        return [{
            'session_id': 'kiro-docs',
            'project': get_project_name(),
            'date': date_str,
            'message_count': file_count,
            'preview': preview,
            'file_count': file_count
        }]
    
    def _get_markdown_files(self, kiro_path: Path) -> List[Path]:
        """Get all markdown files, sorted by modification time"""
        markdown_files = []
        
        # Support common markdown extensions
        markdown_extensions = ['.md', '.markdown', '.mkd', '.mdown']
        
        for file_path in kiro_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in markdown_extensions:
                markdown_files.append(file_path)
        
        # Sort by modification time, newest first
        markdown_files.sort(key=lambda f: f.stat().st_mtime, reverse=False)
        
        self.logger.debug(f"Found {len(markdown_files)} markdown files in .kiro directory")
        return markdown_files
    
    def _combine_markdown_files(self, markdown_files: List[Path]) -> str:
        """Combine all markdown file contents"""
        combined_content = []
        
        for file_path in markdown_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        # Add file information as separator
                        relative_path = file_path.relative_to(Path.cwd())
                        file_header = f"\n\n---\n**文件: {relative_path}**\n"
                        
                        # Get file modification time
                        mtime = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                        file_header += f"**修改时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')}**\n---\n\n"
                        
                        combined_content.append(file_header + content)
                        
            except Exception as e:
                self.logger.warning(f"Error reading file {file_path}: {e}")
                continue
        
        return '\n\n'.join(combined_content)
    
    def _create_chat_session(self, content: str, kiro_path: Path) -> Dict[str, Any]:
        """Create chat session object"""
        # Get latest modification time
        try:
            markdown_files = self._get_markdown_files(kiro_path)
            if markdown_files:
                latest_mtime = max(f.stat().st_mtime for f in markdown_files)
                created_at = latest_mtime * 1000
            else:
                created_at = datetime.datetime.now().timestamp() * 1000
        except Exception:
            created_at = datetime.datetime.now().timestamp() * 1000
        
        # Create single message, containing all content
        messages = [{
            'role': 'user',
            'content': content,
            'timestamp': datetime.datetime.now().isoformat()
        }]
        
        # Create chat session object
        chat_data = {
            'project': {
                'name': get_project_name(),
                'rootPath': str(Path.cwd())
            },
            'session': {
                'sessionId': 'kiro-combined-docs',
                'title': f"Kiro - {get_project_name()}",
                'createdAt': created_at,
                'lastUpdatedAt': created_at
            },
            'messages': messages,
            'metadata': {
                'source_path': str(kiro_path),
                'file_count': len(self._get_markdown_files(kiro_path)),
                'extraction_time': datetime.datetime.now().isoformat()
            }
        }
        
        return chat_data 