"""
Base classes and common functionality for data extraction.
"""

import uuid
import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..utils.logging import get_logger

logger = get_logger('extractors')


class BaseExtractor(ABC):
    """Base class for all extractors."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f'extractors.{name}')
    
    @abstractmethod
    def extract_chats(self) -> List[Dict[str, Any]]:
        """Extract chat data and return a list of chat sessions."""
        pass
    
    @abstractmethod
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List available chat sessions with metadata."""
        pass
    
    def format_chat_for_export(self, chat: Dict[str, Any]) -> Dict[str, Any]:
        """Format chat data for export with standardized fields."""
        try:
            # Generate a unique ID for this chat if it doesn't have one
            session_id = str(uuid.uuid4())
            if 'session' in chat and isinstance(chat['session'], dict):
                session_id = chat['session'].get('composerId') or chat['session'].get('sessionId', session_id)
            elif 'session_id' in chat:
                session_id = chat['session_id']
            
            # Format date from various timestamp sources
            date = int(datetime.datetime.now().timestamp())
            if 'session' in chat and isinstance(chat['session'], dict):
                created_at = chat['session'].get('createdAt') or chat['session'].get('timestamp')
                if created_at and isinstance(created_at, (int, float)):
                    # Handle both seconds and milliseconds timestamps
                    date = created_at / 1000 if created_at > 1e10 else created_at
            elif 'date' in chat:
                date = chat['date']
            
            # Ensure project has expected fields
            project = chat.get('project', {})
            if not isinstance(project, dict):
                project = {'name': 'Unknown Project', 'rootPath': '/'}
            
            # Ensure messages exist and are properly formatted
            messages = chat.get('messages', [])
            if not isinstance(messages, list):
                messages = []
            
            # Create standardized chat object
            return {
                'project': project,
                'messages': messages,
                'date': date,
                'session_id': session_id,
                'source': self.name,
                'metadata': chat.get('metadata', {})
            }
        except Exception as e:
            self.logger.error(f"Error formatting chat: {e}")
            # Return a minimal valid object if there's an error
            return {
                'project': {'name': 'Error', 'rootPath': '/'},
                'messages': [],
                'date': int(datetime.datetime.now().timestamp()),
                'session_id': str(uuid.uuid4()),
                'source': self.name,
                'metadata': {'error': str(e)}
            } 