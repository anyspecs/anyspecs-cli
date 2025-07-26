"""
MiniMax AI client implementation.
"""

import json
from typing import Optional, Dict, Any
import requests
from requests.exceptions import RequestException, Timeout

from .base_client import BaseAIClient
from ..utils.logging import get_logger

logger = get_logger('minimax_client')


class MinimaxClient(BaseAIClient):
    """MiniMax AI client implementation."""
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "MiniMax-Text-01",
        base_url: str = "https://api.minimaxi.com/v1",
        group_id: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 8192,
        timeout: int = 120,
        **kwargs
    ):
        """Initialize MiniMax client."""
        super().__init__(api_key, model, **kwargs)
        
        self.base_url = base_url.rstrip('/')
        self.group_id = group_id  # Required for chatcompletion_pro endpoint
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        self.logger = logger
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "minimax"
    
    def process_text(
        self, 
        system_prompt: str, 
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Optional[str]:
        """Process text using MiniMax API."""
        
        try:
            # Check if group_id is provided
            if not self.group_id:
                raise MinimaxAPIError("group_id is required for MiniMax API. Please set it in your configuration.")
            
            # Use provided values or defaults
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens
            
            # Log request details
            self.logger.debug(f"Processing text with model: {self.model}")
            self.logger.debug(f"System prompt length: {len(system_prompt)}")
            self.logger.debug(f"User prompt length: {len(user_prompt)}")
            
            # Prepare request payload (MiniMax chatcompletion_pro format)
            payload = {
                "model": self.model,
                "tokens_to_generate": tokens,
                "reply_constraints": {
                    "sender_type": "BOT", 
                    "sender_name": "MM智能助理"
                },
                "messages": [
                    {
                        "sender_type": "USER",
                        "sender_name": "用户",
                        "text": f"系统指令：{system_prompt}\n\n用户输入：{user_prompt}"
                    }
                ],
                "bot_setting": [
                    {
                        "bot_name": "MM智能助理",
                        "content": "MM智能助理是一款由MiniMax自研的，没有调用其他产品的接口的大型语言模型。MiniMax是一家中国科技公司，一直致力于进行大模型相关的研究。",
                    }
                ]
            }
            
            # Add optional parameters
            if temp != 0.3:  # Only add if different from default
                payload['temperature'] = temp
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Make API request - using chatcompletion_pro endpoint with GroupId
            url = f"{self.base_url}/text/chatcompletion_pro?GroupId={self.group_id}"
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            # Log response status
            self.logger.debug(f"MiniMax API response status: {response.status_code}")
            
            # Check for HTTP errors
            if not response.ok:
                error_text = response.text
                self.logger.error(f"MiniMax API request failed: {response.status_code} {response.reason}")
                self.logger.error(f"Error response: {error_text}")
                raise MinimaxAPIError(f"API request failed: {response.status_code} {response.reason}")
            
            # Parse response
            response_data = response.json()
            
            # Log response for debugging
            self.logger.debug(f"MiniMax API response data keys: {response_data.keys()}")
            
            # Extract content from response (MiniMax chatcompletion_pro format)
            # Primary response field: reply
            if 'reply' in response_data and response_data['reply']:
                content = response_data['reply']
                self.logger.debug(f"Received response via 'reply' field (length: {len(content)})")
                return content
            
            # Fallback: check choices format (for compatibility)
            if 'choices' in response_data and response_data['choices']:
                choice = response_data['choices'][0]
                
                # Extract from messages if available
                if 'messages' in choice and choice['messages']:
                    for msg in choice['messages']:
                        if msg.get('sender_type') == 'BOT' and 'text' in msg:
                            content = msg['text']
                            self.logger.debug(f"Received response from BOT message (length: {len(content)})")
                            return content
                
                # Standard choice format fallback
                if 'message' in choice and 'content' in choice['message']:
                    content = choice['message']['content']
                    self.logger.debug(f"Received response from choice.message.content (length: {len(content)})")
                    return content
                elif 'text' in choice:
                    content = choice['text']
                    self.logger.debug(f"Received response from choice.text (length: {len(content)})")
                    return content
            
            # Try other possible response fields
            for field in ['output', 'result', 'text']:
                if field in response_data and response_data[field]:
                    content = response_data[field]
                    self.logger.debug(f"Received response via '{field}' field (length: {len(content)})")
                    return content
            
            self.logger.error(f"No valid content found in MiniMax API response. Available fields: {list(response_data.keys())}")
            return None
                
        except requests.exceptions.Timeout:
            self.logger.error(f"MiniMax API request timed out after {self.timeout} seconds")
            raise MinimaxAPIError("API request timed out")
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Failed to connect to MiniMax API: {self.base_url}")
            raise MinimaxAPIError("Failed to connect to MiniMax API")
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response from MiniMax API: {e}")
            raise MinimaxAPIError("Invalid JSON response from API")
        except Exception as e:
            self.logger.error(f"Unexpected error during MiniMax API call: {e}")
            raise MinimaxAPIError(f"Unexpected error: {e}")
    
    def test_connection(self) -> bool:
        """Test connection to MiniMax API."""
        
        try:
            self.logger.info("Testing MiniMax API connection...")
            
            if not self.group_id:
                self.logger.error("Cannot test connection: group_id is required for MiniMax API")
                return False
            
            # Simple test request using chatcompletion_pro format
            response = self.process_text(
                system_prompt="你是一个有用的AI助手。",
                user_prompt="你好，请简单回复一下。",
                max_tokens=50
            )
            
            success = response is not None and len(response.strip()) > 0
            
            if success:
                self.logger.info("MiniMax API connection test successful")
            else:
                self.logger.warning("MiniMax API connection test failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"MiniMax connection test failed: {e}")
            return False
    
    def get_available_models(self) -> Optional[list]:
        """Get list of available models."""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=30
            )
            
            if response.ok:
                data = response.json()
                if 'data' in data:
                    return [model['id'] for model in data['data']]
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Could not fetch MiniMax models list: {e}")
            return None
    
    def get_balance(self) -> Optional[Dict[str, Any]]:
        """Get account balance information (if supported)."""
        
        # MiniMax may provide balance endpoints - placeholder for future implementation
        return None


class MinimaxAPIError(Exception):
    """Exception for MiniMax API errors."""
    pass