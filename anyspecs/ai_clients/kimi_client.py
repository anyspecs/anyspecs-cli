"""
Kimi (月之暗面) AI client implementation using OpenAI-compatible API.
"""

from typing import Optional, Dict, Any

from .base_client import BaseAIClient
from ..utils.logging import get_logger

logger = get_logger('kimi_client')

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. Install with: pip install openai")


class KimiClient(BaseAIClient):
    """Kimi (月之暗面) AI client implementation using OpenAI client."""
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "kimi-k2-0711-preview",
        base_url: str = "https://api.moonshot.cn/v1",
        temperature: float = 0.6,
        max_tokens: int = 10000,
        timeout: int = 120,
        **kwargs
    ):
        """Initialize Kimi client."""
        super().__init__(api_key, model, **kwargs)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package is required for Kimi client. Install with: pip install openai")
        
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        # Initialize OpenAI client with Kimi configuration
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )
        
        self.logger = logger
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "kimi"
    
    def process_text(
        self, 
        system_prompt: str, 
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Optional[str]:
        """Process text using Kimi API with OpenAI client."""
        
        try:
            # Use provided values or defaults
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens
            
            # Log request details
            self.logger.debug(f"Processing text with model: {self.model}")
            self.logger.debug(f"System prompt length: {len(system_prompt)}")
            self.logger.debug(f"User prompt length: {len(user_prompt)}")
            
            # Prepare messages - using official Kimi system prompt format
            messages = [
                {
                    "role": "system", 
                    "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。\n\n" + system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
            
            # Make API call using OpenAI client
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
                **kwargs
            )
            
            # Extract response content
            if completion.choices and len(completion.choices) > 0:
                content = completion.choices[0].message.content
                
                if content:
                    self.logger.debug(f"Received response (length: {len(content)})")
                    return content
                else:
                    self.logger.warning("Empty content in Kimi API response")
                    return None
            else:
                self.logger.error("No choices in Kimi API response")
                return None
                
        except Exception as e:
            self.logger.error(f"Error calling Kimi API: {e}")
            raise KimiAPIError(f"API call failed: {e}")
    
    def test_connection(self) -> bool:
        """Test connection to Kimi API."""
        
        try:
            self.logger.info("Testing Kimi API connection...")
            
            # Simple test request
            response = self.process_text(
                system_prompt="",
                user_prompt="你好，我叫李雷，1+1等于多少？",
                max_tokens=50
            )
            
            success = response is not None and len(response.strip()) > 0
            
            if success:
                self.logger.info("Kimi API connection test successful")
            else:
                self.logger.warning("Kimi API connection test failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Kimi connection test failed: {e}")
            return False
    
    def get_available_models(self) -> Optional[list]:
        """Get list of available models."""
        
        try:
            # Try to get models list via OpenAI client
            models = self.client.models.list()
            
            if hasattr(models, 'data'):
                return [model.id for model in models.data]
            else:
                return None
                
        except Exception as e:
            self.logger.debug(f"Could not fetch Kimi models list: {e}")
            return None
    
    def get_usage_info(self) -> Optional[Dict[str, Any]]:
        """Get API usage information (if supported)."""
        
        # Kimi may provide usage endpoints - placeholder for future implementation
        return None


class KimiAPIError(Exception):
    """Exception for Kimi API errors."""
    pass