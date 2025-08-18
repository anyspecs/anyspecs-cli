"""
AI clients package for different AI service providers.
"""

from .base_client import BaseAIClient
from .aihubmix_client import AihubmixClient
from .kimi_client import KimiClient
from .minimax_client import MinimaxClient
from .ppio_client import PPIOClient
from .dify_client import DifyClient

__all__ = [
    'BaseAIClient',
    'AihubmixClient', 
    'KimiClient',
    'MinimaxClient',
    'PPIOClient',
    'DifyClient'
]

# Available AI providers
AVAILABLE_PROVIDERS = {
    'aihubmix': AihubmixClient,
    'kimi': KimiClient,
    'minimax': MinimaxClient,
    'ppio': PPIOClient,
    'dify': DifyClient
}

def create_ai_client(provider: str, api_key: str, model: str, **kwargs) -> BaseAIClient:
    """Create AI client for specified provider."""
    
    if provider not in AVAILABLE_PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}. Available providers: {list(AVAILABLE_PROVIDERS.keys())}")
    
    client_class = AVAILABLE_PROVIDERS[provider]
    return client_class(api_key=api_key, model=model, **kwargs)