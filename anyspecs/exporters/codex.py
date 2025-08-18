"""
Codex chat history extractor.
"""

import json
import pathlib
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..core.extractors import BaseExtractor
from ..utils.paths import get_project_name


class CodexExtractor(BaseExtractor):
    """Extractor for Codex chat history."""
    
    def __init__(self):
        super().__init__('codex')
        self.history_dir = pathlib.Path.home() / ".codex"
    
    def extract_chats(self) -> List[Dict[str, Any]]:
        """Extract all chat data from Codex."""
        if not self.history_dir.exists():
            self.logger.debug(f"No Codex history found at: {self.history_dir}")
            return []
        
        # Get current project path for filtering
        current_project_path = str(pathlib.Path.cwd())
        self.logger.debug(f"Current project path: {current_project_path}")
        
        # Extract from multiple sources
        all_sessions = {}
        
        # 1. Extract from history.jsonl (global history)
        history_sessions = self._extract_from_history_jsonl(current_project_path)
        all_sessions.update(history_sessions)
        
        # 2. Extract from session files (detailed conversations)
        session_sessions = self._extract_from_session_files(current_project_path)
        all_sessions.update(session_sessions)
        
        # 3. Extract from log files (activity logs)
        log_sessions = self._extract_from_log_files(current_project_path)
        all_sessions.update(log_sessions)
        
        # 4. Extract from config (project settings)
        config_sessions = self._extract_from_config(current_project_path)
        all_sessions.update(config_sessions)
        
        # Convert sessions to list and filter out empty ones
        chats = []
        for session in all_sessions.values():
            if session['messages']:
                chats.append(session)
        
        self.logger.info(f"Extracted {len(chats)} Codex chat sessions")
        return chats
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List available Codex chat sessions with metadata."""
        chats = self.extract_chats()
        sessions = []
        
        for chat in chats:
            session = {
                'session_id': chat['session_id'],
                'project': chat['project']['name'],
                'date': chat['metadata']['created_at'] or int(datetime.now().timestamp()),
                'message_count': len(chat['messages']),
                'source': 'codex',
                'preview': self._generate_preview(chat)
            }
            sessions.append(session)
        
        return sessions
    
    def _extract_from_history_jsonl(self, project_path: str) -> Dict[str, Dict[str, Any]]:
        """Extract sessions from history.jsonl file."""
        sessions = {}
        history_file = self.history_dir / "history.jsonl"
        
        if not history_file.exists():
            return sessions
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        entry = json.loads(line)
                        session_id = entry.get('session_id', f'history_{line_num}')
                        
                        # Check if this entry is related to current project
                        if not self._is_project_related(entry, project_path):
                            continue
                        
                        if session_id not in sessions:
                            sessions[session_id] = self._create_session_template(session_id, project_path)
                        
                        # Add user message
                        text = entry.get('text', '')
                        if text:
                            sessions[session_id]['messages'].append({
                                'role': 'user',
                                'content': text,
                                'timestamp': entry.get('ts'),
                                'source': 'history.jsonl'
                            })
                            
                            # Update timestamps
                            if entry.get('ts'):
                                ts = entry['ts']
                                if sessions[session_id]['metadata']['created_at'] is None:
                                    sessions[session_id]['metadata']['created_at'] = ts
                                sessions[session_id]['metadata']['last_updated'] = ts
                                
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Invalid JSON in history.jsonl line {line_num}: {e}")
                        continue
                        
        except Exception as e:
            self.logger.warning(f"Error reading history.jsonl: {e}")
        
        return sessions
    
    def _extract_from_session_files(self, project_path: str) -> Dict[str, Dict[str, Any]]:
        """Extract sessions from session files."""
        sessions = {}
        sessions_dir = self.history_dir / "sessions"
        
        if not sessions_dir.exists():
            return sessions
        
        # Walk through all session files
        for session_file in sessions_dir.rglob("*.jsonl"):
            try:
                session_id = self._extract_session_id_from_filename(session_file.name)
                if not session_id:
                    continue
                
                if session_id not in sessions:
                    sessions[session_id] = self._create_session_template(session_id, project_path)
                
                # Read session file
                with open(session_file, 'r', encoding='utf-8') as f:
                    for line in sessions[session_id]['messages']:
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            record = json.loads(line)
                            self._process_session_record(record, sessions[session_id], session_file)
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                self.logger.warning(f"Error processing session file {session_file}: {e}")
                continue
        
        return sessions
    
    def _extract_from_log_files(self, project_path: str) -> Dict[str, Dict[str, Any]]:
        """Extract sessions from log files."""
        sessions = {}
        log_dir = self.history_dir / "log"
        
        if not log_dir.exists():
            return sessions
        
        # Process log files
        for log_file in log_dir.glob("*.log"):
            try:
                session_id = f"log_{log_file.stem}"
                
                if session_id not in sessions:
                    sessions[session_id] = self._create_session_template(session_id, project_path)
                
                # Read log file
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                    
                    # Extract relevant log entries
                    if project_path in log_content:
                        # Add log summary as a message
                        sessions[session_id]['messages'].append({
                            'role': 'system',
                            'content': f"Log entries related to project: {log_content}",
                            'timestamp': int(datetime.now().timestamp()),
                            'source': str(log_file)
                        })
                        
            except Exception as e:
                self.logger.warning(f"Error processing log file {log_file}: {e}")
                continue
        
        return sessions
    
    def _extract_from_config(self, project_path: str) -> Dict[str, Dict[str, Any]]:
        """Extract project configuration information."""
        sessions = {}
        config_file = self.history_dir / "config.toml"
        
        if not config_file.exists():
            return sessions
        
        try:
            # Read config file content
            with open(config_file, 'r', encoding='utf-8') as f:
                config_content = f.read()
                
                # Check if current project is in trusted projects
                if project_path in config_content:
                    session_id = "config_project"
                    sessions[session_id] = self._create_session_template(session_id, project_path)
                    
                    # Add config information as a message
                    sessions[session_id]['messages'].append({
                        'role': 'system',
                        'content': f"Project configuration: {config_content}",
                        'timestamp': int(datetime.now().timestamp()),
                        'source': 'config.toml'
                    })
                    
        except Exception as e:
            self.logger.warning(f"Error reading config file: {e}")
        
        return sessions
    
    def _create_session_template(self, session_id: str, project_path: str) -> Dict[str, Any]:
        """Create a template for a new session."""
        return {
            'session_id': session_id,
            'messages': [],
            'project': {
                'name': get_project_name(),
                'rootPath': project_path
            },
            'metadata': {
                'source_files': [],
                'created_at': None,
                'last_updated': None,
                'codex_path': project_path,
                'extractor_version': '1.0'
            }
        }
    
    def _is_project_related(self, entry: Dict[str, Any], project_path: str) -> bool:
        """Check if an entry is related to the current project."""
        # Check various fields that might contain project information
        text = entry.get('text', '')
        path = entry.get('path', '')
        
        return project_path in text or project_path in path
    
    def _extract_session_id_from_filename(self, filename: str) -> Optional[str]:
        """Extract session ID from filename."""
        # Example: rollout-2025-08-17T13-42-18-fa0195a0-3f1d-4f2c-b6c2-4ef50e47ba23.jsonl
        match = re.search(r'rollout-.*?-([a-f0-9-]+)\.jsonl', filename)
        if match:
            return match.group(1)
        return None
    
    def _process_session_record(self, record: Dict[str, Any], session: Dict[str, Any], file_path: str):
        """Process a single record from a session file."""
        record_type = record.get('type')
        
        if record_type == 'message':
            role = record.get('role')
            content = record.get('content', [])
            
            if role and content:
                # Extract text content
                text_content = ""
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'input_text':
                        text_content += item.get('text', '')
                    elif isinstance(item, dict) and item.get('type') == 'output_text':
                        text_content += item.get('text', '')
                
                if text_content:
                    session['messages'].append({
                        'role': role,
                        'content': text_content,
                        'timestamp': record.get('timestamp'),
                        'source': str(file_path)
                    })
                    
                    # Update timestamps
                    if record.get('timestamp'):
                        ts = self._parse_timestamp(record['timestamp'])
                        if ts and session['metadata']['created_at'] is None:
                            session['metadata']['created_at'] = ts
                        if ts:
                            session['metadata']['last_updated'] = ts
        
        elif record_type == 'function_call':
            # Handle function calls
            func_name = record.get('name', 'unknown')
            arguments = record.get('arguments', '{}')
            
            session['messages'].append({
                'role': 'assistant',
                'content': f"**Function Call: {func_name}**\n```json\n{arguments}\n```",
                'timestamp': record.get('timestamp'),
                'source': str(file_path)
            })
        
        elif record_type == 'function_call_output':
            # Handle function call outputs
            call_id = record.get('call_id', 'unknown')
            output = record.get('output', '{}')
            
            session['messages'].append({
                'role': 'system',
                'content': f"**Function Output: {call_id}**\n```json\n{output}\n```",
                'timestamp': record.get('timestamp'),
                'source': str(file_path)
            })
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[int]:
        """Parse timestamp string to Unix timestamp."""
        try:
            # Handle ISO format timestamps
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return int(dt.timestamp())
        except:
            try:
                # Handle Unix timestamp
                return int(timestamp_str)
            except:
                return None
    
    def _generate_preview(self, chat: Dict[str, Any]) -> str:
        """Generate a preview of the chat session."""
        if not chat['messages']:
            return "No messages"
        
        # Get first user message as preview
        for message in chat['messages']:
            if message['role'] == 'user':
                content = message['content']
                if len(content) > 100:
                    content = content[:100] + "..."
                return content
        
        return "Codex session"
