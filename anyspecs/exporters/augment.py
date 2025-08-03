"""
Augment AI chat history extractor.
"""

import json
import sqlite3
import pathlib
from typing import Dict, Any, List, Iterable, Tuple
from datetime import datetime

from ..core.extractors import BaseExtractor
from ..utils.paths import get_project_name


class AugmentExtractor(BaseExtractor):
    """Extractor for Augment AI chat history from VSCode state.vscdb."""
    
    def __init__(self):
        super().__init__('augment')
    
    def extract_chats(self) -> List[Dict[str, Any]]:
        """Extract all chat data from Augment."""
        # Look for state.vscdb in current directory and common VSCode locations
        db_paths = self._find_state_vscdb()
        
        if not db_paths:
            self.logger.warning("No state.vscdb files found")
            return []
        
        all_chats = []
        
        for db_path in db_paths:
            self.logger.debug(f"Processing database: {db_path}")
            chats = self._extract_from_database(db_path)
            all_chats.extend(chats)
        
        # Sort by last updated time if available
        all_chats.sort(key=lambda s: s.get('date', 0), reverse=True)
        self.logger.debug(f"Total Augment chat sessions extracted: {len(all_chats)}")
        return all_chats
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List Augment chat sessions."""
        chats = self.extract_chats()
        sessions = []
        
        # Get current project name to filter sessions
        current_project = get_project_name().lower()
        
        for chat in chats:
            session_id = chat.get('session_id', 'unknown')[:8]
            project_name = chat.get('project', {}).get('name', 'Unknown Project')
            msg_count = len(chat.get('messages', []))
            
            # Only include sessions from current workspace/project
            if current_project in project_name.lower() or project_name.lower() in current_project:
                # Format date
                date_str = "Unknown date"
                date_timestamp = chat.get('date')
                if date_timestamp:
                    try:
                        if date_timestamp > 1e10:  # milliseconds
                            date_timestamp = date_timestamp / 1000
                        date_obj = datetime.fromtimestamp(date_timestamp)
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
                    'db_path': chat.get('db_path', 'unknown')
                })
        
        return sessions
    
    def _find_state_vscdb(self) -> List[pathlib.Path]:
        """Find state.vscdb files in common locations."""
        db_paths = []
        
        # Check current directory
        current_db = pathlib.Path.cwd() / "state.vscdb"
        if current_db.exists():
            db_paths.append(current_db)
        
        # Check common VSCode locations
        home = pathlib.Path.home()
        
        # macOS
        mac_paths = [
            home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "state.vscdb",
            home / "Library" / "Application Support" / "Code" / "User" / "workspaceStorage" / "*" / "state.vscdb",
        ]
        
        # Linux
        linux_paths = [
            home / ".config" / "Code" / "User" / "globalStorage" / "state.vscdb",
            home / ".config" / "Code" / "User" / "workspaceStorage" / "*" / "state.vscdb",
        ]
        
        # Windows
        windows_paths = [
            home / "AppData" / "Roaming" / "Code" / "User" / "globalStorage" / "state.vscdb",
            home / "AppData" / "Roaming" / "Code" / "User" / "workspaceStorage" / "*" / "state.vscdb",
        ]
        
        # Check all possible paths
        all_paths = mac_paths + linux_paths + windows_paths
        
        for path_pattern in all_paths:
            if "*" in str(path_pattern):
                # Handle glob patterns
                parent = path_pattern.parent
                if parent.exists():
                    for db_file in parent.glob("state.vscdb"):
                        if db_file.exists():
                            db_paths.append(db_file)
            else:
                # Direct path
                if path_pattern.exists():
                    db_paths.append(path_pattern)
        
        return db_paths
    
    def _extract_from_database(self, db_path: pathlib.Path) -> List[Dict[str, Any]]:
        """Extract chat data from a specific database file."""
        try:
            # Connect to database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get chat session index
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'chat.ChatSessionStore.index';")
            index_result = cursor.fetchone()
            
            if not index_result:
                self.logger.debug(f"No chat session index found in {db_path}")
                conn.close()
                return []
            
            # Parse session index
            session_index = json.loads(index_result[0])
            self.logger.debug(f"Found {len(session_index.get('entries', {}))} chat sessions in {db_path}")
            
            # Get Augment chat records
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'memento/webviewView.augment-chat';")
            chat_result = cursor.fetchone()
            
            if not chat_result:
                self.logger.debug(f"No Augment chat records found in {db_path}")
                conn.close()
                return []
            
            # Parse chat records
            chat_data = json.loads(chat_result[0])
            webview_state = json.loads(chat_data.get('webviewState', '{}'))
            
            # Extract conversations
            conversations = webview_state.get('conversations', {})
            
            if not conversations:
                self.logger.debug(f"No conversations found in {db_path}")
                conn.close()
                return []
            
            # Process each conversation
            chats = []
            for conv_id, conversation in conversations.items():
                chat = self._process_conversation(conv_id, conversation, db_path)
                if chat:
                    chats.append(chat)
            
            conn.close()
            return chats
            
        except Exception as e:
            self.logger.error(f"Error extracting from {db_path}: {e}")
            return []
    
    def _process_conversation(self, conv_id: str, conversation: Dict[str, Any], db_path: pathlib.Path) -> Dict[str, Any]:
        """Process a single conversation into a chat object."""
        try:
            # Extract chat history
            chat_history = conversation.get('chatHistory', [])
            
            if not chat_history:
                return None
            
            # Convert to standardized message format
            messages = []
            for message in chat_history:
                # User message
                request_message = message.get('request_message', '')
                if request_message:
                    messages.append({
                        'role': 'user',
                        'content': request_message
                    })
                
                # Assistant reply
                response_text = message.get('response_text', '')
                if response_text:
                    messages.append({
                        'role': 'assistant',
                        'content': response_text
                    })
            
            if not messages:
                return None
            
            # Get timestamps
            created_at = conversation.get('createdAtIso')
            last_interacted = conversation.get('lastInteractedAtIso')
            
            # Convert ISO timestamps to Unix timestamps
            date_timestamp = 0
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    date_timestamp = dt.timestamp()
                except:
                    date_timestamp = datetime.now().timestamp()
            else:
                date_timestamp = datetime.now().timestamp()
            
            # Create chat object
            chat = {
                'project': {
                    'name': get_project_name(),
                    'rootPath': str(pathlib.Path.cwd())
                },
                'session': {
                    'composerId': conv_id,
                    'title': f'Augment Chat {conv_id[:8]}',
                    'createdAt': created_at,
                    'lastUpdatedAt': last_interacted
                },
                'messages': messages,
                'date': date_timestamp,
                'session_id': conv_id,
                'db_path': str(db_path)
            }
            
            return chat
            
        except Exception as e:
            self.logger.error(f"Error processing conversation {conv_id}: {e}")
            return None 