"""
Base AI client interface for all AI service providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseAIClient(ABC):
    """Abstract base class for AI service clients."""
    
    def __init__(self, api_key: str, model: str, **kwargs):
        """Initialize AI client."""
        self.api_key = api_key
        self.model = model
        self.config = kwargs
    
    @abstractmethod
    def process_text(
        self, 
        system_prompt: str, 
        user_prompt: str,
        **kwargs
    ) -> Optional[str]:
        """Process text using AI service and return response."""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test connection to AI service."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the AI service provider."""
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)