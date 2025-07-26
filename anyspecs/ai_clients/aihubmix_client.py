"""
Aihubmix AI client using OpenAI-compatible API.
"""

import random
from typing import Optional, Dict, Any

from .base_client import BaseAIClient
from ..utils.logging import get_logger

logger = get_logger('aihubmix_client')

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. Install with: pip install openai")


class AihubmixClient(BaseAIClient):
    """Aihubmix AI client implementation."""
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "gpt-4o-mini",
        base_url: str = "https://aihubmix.com/v1",
        temperature: float = 0.3,
        max_tokens: int = 10000,
        timeout: int = 120,
        **kwargs
    ):
        """Initialize Aihubmix client."""
        super().__init__(api_key, model, **kwargs)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package is required for Aihubmix client. Install with: pip install openai")
        
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        # Initialize OpenAI client with Aihubmix configuration
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout
        )
        
        self.logger = logger
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "aihubmix"
    
    def process_text(
        self, 
        system_prompt: str, 
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Optional[str]:
        """Process text using Aihubmix API."""
        
        try:
            # Use provided values or defaults
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens
            
            # Log request details
            self.logger.debug(f"Processing text with model: {self.model}")
            self.logger.debug(f"System prompt length: {len(system_prompt)}")
            self.logger.debug(f"User prompt length: {len(user_prompt)}")
            
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": user_prompt
                }
            ]
            
            # Make API call
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
                top_p=kwargs.get('top_p', 1),
                frequency_penalty=kwargs.get('frequency_penalty', 0),
                presence_penalty=kwargs.get('presence_penalty', 0),
                seed=kwargs.get('seed', random.randint(1, 1000000000))
            )
            
            # Extract response content
            if completion.choices and len(completion.choices) > 0:
                content = completion.choices[0].message.content
                
                if content:
                    self.logger.debug(f"Received response (length: {len(content)})")
                    return content
                else:
                    self.logger.warning("Empty content in API response")
                    return None
            else:
                self.logger.error("No choices in API response")
                return None
                
        except Exception as e:
            self.logger.error(f"Error calling Aihubmix API: {e}")
            raise AihubmixAPIError(f"API call failed: {e}")
    
    def test_connection(self) -> bool:
        """Test connection to Aihubmix API."""
        
        try:
            self.logger.info("Testing Aihubmix API connection...")
            
            # Simple test request
            response = self.process_text(
                system_prompt="You are a helpful assistant.",
                user_prompt="Say 'test' if you can read this message.",
                max_tokens=50
            )
            
            success = response is not None and 'test' in response.lower()
            
            if success:
                self.logger.info("Aihubmix API connection test successful")
            else:
                self.logger.warning("Aihubmix API connection test failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Aihubmix connection test failed: {e}")
            return False
    
    def get_available_models(self) -> Optional[list]:
        """Get list of available models (if supported)."""
        
        try:
            # Try to get models list
            models = self.client.models.list()
            
            if hasattr(models, 'data'):
                return [model.id for model in models.data]
            else:
                return None
                
        except Exception as e:
            self.logger.debug(f"Could not fetch models list: {e}")
            return None
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> Optional[float]:
        """Estimate cost for token usage (if pricing info available)."""
        
        # Placeholder for cost estimation
        # Would need actual pricing information from Aihubmix
        
        return None


class AihubmixAPIError(Exception):
    """Exception for Aihubmix API errors."""
    pass