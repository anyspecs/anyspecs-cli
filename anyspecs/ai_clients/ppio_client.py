"""
PPIO AI client for AnySpecs CLI.
Uses OpenAI-compatible API interface.
"""

import logging
from typing import Dict, Any, Optional

from .base_client import BaseAIClient

logger = logging.getLogger(__name__)


class PPIOClient(BaseAIClient):
    """PPIO AI client implementation."""
    
    def __init__(self, api_key: str, model: str = "deepseek/deepseek-r1", **kwargs):
        """
        Initialize PPIO client.
        
        Args:
            api_key: PPIO API key
            model: Model name (default: deepseek/deepseek-r1)
            **kwargs: Additional configuration
        """
        self.api_key = api_key
        self.model = model
        self.base_url = kwargs.get('base_url', 'https://api.ppinfra.com/v3/openai')
        self.temperature = kwargs.get('temperature', 0.3)
        self.max_tokens = kwargs.get('max_tokens', 512)
        self.timeout = kwargs.get('timeout', 30)
        
        # Import OpenAI client
        try:
            from openai import OpenAI
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.timeout
            )
            logger.info(f"PPIO client initialized with model: {self.model}")
        except ImportError:
            logger.warning("OpenAI package not installed. Install with: pip install openai")
            raise ImportError("OpenAI package is required for PPIO client. Install with: pip install openai")
    
    @property
    def provider_name(self) -> str:
        """Return the name of the AI service provider."""
        return "ppio"
    
    def process_text(self, system_prompt: str, user_prompt: str, **kwargs) -> Optional[str]:
        """
        Process text using PPIO AI.
        
        Args:
            system_prompt: System prompt for context
            user_prompt: User input text
            **kwargs: Additional arguments
            
        Returns:
            AI response text or None if failed
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            logger.debug(f"Sending request to PPIO API with model: {self.model}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=False
            )
            
            if response.choices and len(response.choices) > 0:
                result = response.choices[0].message.content
                logger.debug("PPIO processing successful")
                return result
            else:
                logger.error("No response choices from PPIO API")
                return None
                
        except Exception as e:
            logger.error(f"PPIO processing failed: {e}")
            return None
    
    def compress_content(self, content: str, prompt: str) -> Optional[str]:
        """
        Compress content using PPIO AI.
        
        Args:
            content: Content to compress
            prompt: Compression prompt
            
        Returns:
            Compressed content as JSON string or None if failed
        """
        try:
            messages = [
                {
                    "role": "system", 
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": content
                }
            ]
            
            logger.debug(f"Sending request to PPIO API with model: {self.model}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=False
            )
            
            if response.choices and len(response.choices) > 0:
                compressed_content = response.choices[0].message.content
                logger.debug("PPIO compression successful")
                return compressed_content
            else:
                logger.error("No response choices from PPIO API")
                return None
                
        except Exception as e:
            logger.error(f"PPIO compression failed: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test connection to PPIO API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                temperature=0
            )
            
            return bool(response.choices and len(response.choices) > 0)
            
        except Exception as e:
            logger.error(f"PPIO connection test failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information.
        
        Returns:
            Dictionary containing model details
        """
        return {
            "provider": "ppio",
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }