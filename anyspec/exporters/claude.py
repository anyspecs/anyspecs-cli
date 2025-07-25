"""
Claude Code chat history extractor.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from ..core.extractors import BaseExtractor
from ..utils.paths import get_claude_history_path, get_project_name


class ClaudeExtractor(BaseExtractor):
    """Extractor for Claude Code chat history."""
    
    def __init__(self):
        super().__init__('claude')
    
    def extract_chats(self) -> List[Dict[str, Any]]:
        """Extract all chat data from Claude Code."""
        history_path = get_claude_history_path()
        
        if not history_path.exists():
            self.logger.debug(f"No Claude Code history found at: {history_path}")
            return []
        
        history_files = self._list_history_files(history_path)
        if not history_files:
            self.logger.debug("No history files found.")
            return []
        
        # Group entries by session
        sessions = {}
        
        for file_info in history_files:
            entries = self._read_history_file(file_info['path'])
            for entry in entries:
                session_id = entry.get('sessionId', 'unknown')
                
                if session_id not in sessions:
                    sessions[session_id] = {
                        'session_id': session_id,
                        'messages': [],
                        'project': {
                            'name': get_project_name(),
                            'rootPath': str(Path.cwd())
                        },
                        'metadata': {
                            'source_files': [],
                            'created_at': None,
                            'last_updated': None
                        }
                    }
                
                # Track source files
                source_file = str(file_info['path'])
                if source_file not in sessions[session_id]['metadata']['source_files']:
                    sessions[session_id]['metadata']['source_files'].append(source_file)
                
                # Update timestamps
                timestamp = entry.get('timestamp')
                if timestamp:
                    if sessions[session_id]['metadata']['created_at'] is None:
                        sessions[session_id]['metadata']['created_at'] = timestamp
                    sessions[session_id]['metadata']['last_updated'] = timestamp
                
                # Convert entries to messages
                entry_type = entry.get('type')
                
                if entry_type == 'user':
                    content = entry.get('message', {}).get('content', 'No content')
                    sessions[session_id]['messages'].append({
                        'role': 'user',
                        'content': content,
                        'timestamp': timestamp
                    })
                
                elif entry_type == 'assistant':
                    content = entry.get('message', {}).get('content', 'No content')
                    sessions[session_id]['messages'].append({
                        'role': 'assistant',
                        'content': content,
                        'timestamp': timestamp
                    })
                
                elif entry_type == 'tool':
                    tool_name = entry.get('tool', 'Unknown')
                    input_data = entry.get('input', {})
                    content = f"**Tool Call: {tool_name}**\n\n"
                    if input_data:
                        content += f"```json\n{json.dumps(input_data, indent=2, default=str)}\n```"
                    
                    sessions[session_id]['messages'].append({
                        'role': 'assistant',
                        'content': content,
                        'timestamp': timestamp
                    })
                
                elif entry_type == 'tool_result':
                    result = entry.get('result', {})
                    content = "**Tool Result**\n\n"
                    
                    if isinstance(result, dict):
                        if 'output' in result:
                            content += f"```\n{result['output']}\n```"
                        else:
                            content += f"```json\n{json.dumps(result, indent=2, default=str)}\n```"
                    else:
                        content += f"```\n{result}\n```"
                    
                    sessions[session_id]['messages'].append({
                        'role': 'assistant',
                        'content': content,
                        'timestamp': timestamp
                    })
        
        # Convert to output format
        chats = []
        for session_data in sessions.values():
            # Calculate date from timestamps
            date_timestamp = None
            if session_data['metadata']['created_at']:
                try:
                    date_timestamp = datetime.fromisoformat(session_data['metadata']['created_at'].replace('Z', '+00:00'))
                    date_timestamp = date_timestamp.timestamp()
                except:
                    # Try parsing as timestamp
                    try:
                        date_timestamp = float(session_data['metadata']['created_at'])
                    except:
                        date_timestamp = datetime.now().timestamp()
            else:
                date_timestamp = datetime.now().timestamp()
            
            chat_data = {
                'project': session_data['project'],
                'session': {
                    'sessionId': session_data['session_id'],
                    'title': f"Claude Session {session_data['session_id'][:8]}",
                    'createdAt': date_timestamp * 1000 if date_timestamp else None,  # Convert to milliseconds
                    'lastUpdatedAt': date_timestamp * 1000 if date_timestamp else None
                },
                'messages': session_data['messages'],
                'metadata': session_data['metadata']
            }
            
            chats.append(chat_data)
        
        # Sort by creation time
        chats.sort(key=lambda x: x['session'].get('createdAt', 0), reverse=True)
        
        self.logger.debug(f"Extracted {len(chats)} Claude chat sessions")
        return chats
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List available chat sessions with metadata."""
        chats = self.extract_chats()
        sessions = []
        
        for chat in chats:
            session_id = chat.get('session', {}).get('sessionId', 'unknown')[:8]
            project_name = chat.get('project', {}).get('name', 'Unknown Project')
            msg_count = len(chat.get('messages', []))
            
            # Format date
            date_str = "Unknown date"
            created_at = chat.get('session', {}).get('createdAt')
            if created_at:
                try:
                    if created_at > 1e10:  # milliseconds
                        created_at = created_at / 1000
                    date_obj = datetime.fromtimestamp(created_at)
                    date_str = date_obj.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            # Get preview of first message
            preview = "No messages"
            messages = chat.get('messages', [])
            if messages:
                first_msg = messages[0].get('content', '')
                preview = first_msg[:60] + "..." if len(first_msg) > 60 else first_msg
                preview = preview.replace('\n', ' ')
            
            sessions.append({
                'session_id': session_id,
                'project': project_name,
                'date': date_str,
                'message_count': msg_count,
                'preview': preview,
                'source_files': len(chat.get('metadata', {}).get('source_files', []))
            })
        
        return sessions
    
    def _list_history_files(self, project_path: Path) -> List[Dict[str, Any]]:
        """List all history files for the project."""
        if not project_path.exists():
            return []
        
        history_files = []
        for file_path in project_path.glob('*.jsonl'):
            try:
                stat = file_path.stat()
                history_files.append({
                    'path': file_path,
                    'name': file_path.name,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })
            except Exception as e:
                self.logger.warning(f"Error reading file info for {file_path}: {e}")
        
        return sorted(history_files, key=lambda x: x['modified'], reverse=True)
    
    def _read_history_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read and parse a JSONL history file."""
        entries = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            entries.append(entry)
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Invalid JSON on line {line_num} in {file_path}: {e}")
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
        
        return entries 