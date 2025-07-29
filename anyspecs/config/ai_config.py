"""
AI configuration manager for AnySpecs CLI.
Handles saving and loading AI provider settings.
"""

import os
import json
import sys
import getpass
from pathlib import Path
from typing import Dict, Any, Optional

from ..utils.logging import get_logger

logger = get_logger('ai_config')


def masked_input(prompt: str) -> str:
    """Input function that shows asterisks for each character typed."""
    try:
        import termios
        import tty
        
        print(prompt, end='', flush=True)
        password = ""
        
        while True:
            # Read one character at a time
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                char = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
            # Handle different key presses
            if char == '\r' or char == '\n':  # Enter key
                print()  # New line
                break
            elif char == '\x7f' or char == '\x08':  # Backspace
                if password:
                    password = password[:-1]
                    # Clear the line and reprint
                    print('\r' + ' ' * (len(prompt) + len(password) + 1), end='')
                    print('\r' + prompt + '*' * len(password), end='', flush=True)
            elif char == '\x03':  # Ctrl+C
                print()
                raise KeyboardInterrupt
            elif ord(char) >= 32:  # Printable characters
                password += char
                print('*', end='', flush=True)
        
        return password
        
    except (ImportError, AttributeError):
        # Fallback to getpass on systems without termios (like Windows)
        return getpass.getpass(prompt)


class AIConfigManager:
    """Manages AI provider configurations."""
    
    def __init__(self):
        self.config_dir = Path.home() / '.anyspecs'
        self.config_file = self.config_dir / 'ai_config.json'
        self.env_file = Path.cwd() / '.env'
        self.logger = logger
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Default configuration structure
        self.default_config = {
            'default_provider': None,
            'providers': {
                'aihubmix': {
                    'api_key': None,
                    'model': 'gpt-4o-mini',
                    'base_url': 'https://aihubmix.com/v1',
                    'temperature': 0.3,
                    'max_tokens': 10000
                },
                'kimi': {
                    'api_key': None,
                    'model': 'kimi-k2-0711-preview',
                    'base_url': 'https://api.moonshot.cn/v1',
                    'temperature': 0.6,
                    'max_tokens': 10000
                },
                'minimax': {
                    'api_key': None,
                    'group_id': None,
                    'model': 'MiniMax-Text-01',
                    'base_url': 'https://api.minimaxi.com/v1',
                    'temperature': 0.3,
                    'max_tokens': 8192
                },
                'ppio': {
                    'api_key': None,
                    'model': 'deepseek/deepseek-r1',
                    'base_url': 'https://api.ppinfra.com/v3/openai',
                    'temperature': 0.3,
                    'max_tokens': 512
                }
            },
            'compress_settings': {
                'default_input_dir': '.anyspecs',
                'default_output_dir': None,  # None means same as input
                'default_pattern': None,
                'batch_size': 1
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """Load AI configuration from file."""
        
        if not self.config_file.exists():
            self.logger.debug("AI config file not found, returning default config")
            return self.default_config.copy()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Merge with defaults to ensure all keys exist
            merged_config = self._merge_with_defaults(config)
            self.logger.debug("AI config loaded successfully")
            return merged_config
            
        except Exception as e:
            self.logger.error(f"Error loading AI config: {e}")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save AI configuration to file."""
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"AI config saved to: {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving AI config: {e}")
            return False
    
    def is_configured(self, provider: Optional[str] = None) -> bool:
        """Check if AI configuration is complete."""
        
        config = self.load_config()
        
        # If no provider specified, check if any provider is configured
        if provider is None:
            if config.get('default_provider'):
                provider = config['default_provider']
            else:
                # Check if any provider has an API key
                for p, settings in config.get('providers', {}).items():
                    if settings.get('api_key'):
                        return True
                return False
        
        # Check specific provider
        provider_config = config.get('providers', {}).get(provider, {})
        has_api_key = bool(provider_config.get('api_key'))
        
        # MiniMax requires both api_key and group_id
        if provider == 'minimax':
            has_group_id = bool(provider_config.get('group_id'))
            return has_api_key and has_group_id
        
        return has_api_key
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific provider."""
        
        config = self.load_config()
        provider_config = config.get('providers', {}).get(provider, {})
        
        # Merge with environment variables (priority: command line > .env file > config file)
        merged_config = provider_config.copy()
        
        # Load from .env file first
        env_config = self._load_from_env()
        
        # Apply .env values if config doesn't have them
        if env_config.get('api_key') and not merged_config.get('api_key'):
            merged_config['api_key'] = env_config['api_key']
        if env_config.get('model') and not merged_config.get('model'):
            merged_config['model'] = env_config['model']
        if env_config.get('provider') and env_config['provider'] == provider:
            # If .env specifies this provider, use its settings
            merged_config.update({k: v for k, v in env_config.items() if v and k != 'provider'})
        
        # Check for environment variable API key (highest priority)
        env_key = os.getenv('ANYSPECS_AI_API_KEY')
        if env_key:
            merged_config['api_key'] = env_key
        
        return merged_config
    
    def set_provider_config(self, provider: str, **settings) -> bool:
        """Set configuration for a specific provider."""
        
        config = self.load_config()
        
        if 'providers' not in config:
            config['providers'] = {}
        
        if provider not in config['providers']:
            config['providers'][provider] = {}
        
        # Update provider settings
        config['providers'][provider].update(settings)
        
        # If this is the first configured provider, make it default
        if not config.get('default_provider') and settings.get('api_key'):
            config['default_provider'] = provider
        
        # Save to both config file and .env file
        config_success = self.save_config(config)
        env_success = self._save_to_env(provider, settings)
        
        return config_success and env_success
    
    def get_default_provider(self) -> Optional[str]:
        """Get the default AI provider."""
        
        # Priority: .env file > config file
        env_config = self._load_from_env()
        if env_config.get('provider'):
            return env_config['provider']
        
        config = self.load_config()
        return config.get('default_provider')
    
    def set_default_provider(self, provider: str) -> bool:
        """Set the default AI provider."""
        
        config = self.load_config()
        config['default_provider'] = provider
        return self.save_config(config)
    
    def setup_interactive(self, provider: str) -> bool:
        """Interactive setup for AI provider configuration."""
        
        print(f"\n🤖 Setting up {provider.upper()} AI provider")
        print("=" * 50)
        
        try:
            # Get API key (masked input for security)
            api_key = masked_input(f"Enter your {provider.upper()} API key: ").strip()
            if not api_key:
                print("❌ API key is required")
                return False
            
            # Get model (optional, will use default if not provided)
            current_config = self.get_provider_config(provider)
            default_model = current_config.get('model', self.default_config['providers'][provider]['model'])
            
            model = input(f"Enter model name (default: {default_model}): ").strip()
            if not model:
                model = default_model
            
            # MiniMax specific configuration
            extra_config = {}
            if provider == 'minimax':
                print("\n📝 MiniMax requires a Group ID for API access")
                group_id = masked_input("Enter your MiniMax Group ID: ").strip()
                if not group_id:
                    print("❌ Group ID is required for MiniMax API")
                    return False
                extra_config['group_id'] = group_id
            
            # Save configuration
            success = self.set_provider_config(
                provider,
                api_key=api_key,
                model=model,
                **extra_config
            )
            
            if success:
                print(f"✅ {provider.upper()} configuration saved successfully!")
                print(f"   Model: {model}")
                if provider == 'minimax' and extra_config.get('group_id'):
                    print(f"   Group ID: {extra_config['group_id']}")
                print(f"   Config saved to: {self.config_file}")
                print(f"   Environment saved to: {self.env_file}")
                return True
            else:
                print(f"❌ Failed to save {provider.upper()} configuration")
                return False
                
        except KeyboardInterrupt:
            print("\n❌ Setup cancelled by user")
            return False
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration with defaults."""
        
        def merge_dict(target: dict, source: dict):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    merge_dict(target[key], value)
                elif key not in target:
                    target[key] = value
                else:
                    # If value exists in source, use it (don't override with defaults)
                    target[key] = value
        
        merged = self.default_config.copy()
        merge_dict(merged, config)
        return merged
    
    def list_configured_providers(self) -> list:
        """List all configured providers."""
        
        config = self.load_config()
        configured = []
        
        for provider, settings in config.get('providers', {}).items():
            if settings.get('api_key'):
                configured.append({
                    'provider': provider,
                    'model': settings.get('model'),
                    'is_default': provider == config.get('default_provider')
                })
        
        return configured
    
    def reset_config(self) -> bool:
        """Reset configuration to defaults."""
        
        try:
            if self.config_file.exists():
                self.config_file.unlink()
            self.logger.info("AI configuration reset to defaults")
            return True
        except Exception as e:
            self.logger.error(f"Error resetting config: {e}")
            return False
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from .env file."""
        
        env_config = {}
        
        if not self.env_file.exists():
            return env_config
        
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        
                        # Map environment variable names to config keys
                        if key == 'ANYSPECS_AI_PROVIDER':
                            env_config['provider'] = value
                        elif key == 'ANYSPECS_AI_API_KEY':
                            env_config['api_key'] = value
                        elif key == 'ANYSPECS_AI_MODEL':
                            env_config['model'] = value
                        elif key == 'ANYSPECS_AI_GROUP_ID':
                            env_config['group_id'] = value
                        elif key == 'ANYSPECS_AI_TEMPERATURE':
                            try:
                                env_config['temperature'] = float(value)
                            except ValueError:
                                pass
                        elif key == 'ANYSPECS_AI_MAX_TOKENS':
                            try:
                                env_config['max_tokens'] = int(value)
                            except ValueError:
                                pass
            
            self.logger.debug(f"Loaded configuration from .env: {list(env_config.keys())}")
            return env_config
            
        except Exception as e:
            self.logger.error(f"Error loading .env file: {e}")
            return {}
    
    def _save_to_env(self, provider: str, settings: Dict[str, Any]) -> bool:
        """Save configuration to .env file."""
        
        try:
            # Load existing .env content
            existing_lines = []
            env_vars = set()
            
            if self.env_file.exists():
                with open(self.env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key = line.split('=', 1)[0].strip()
                            env_vars.add(key)
                        # Keep non-AnySpecs related lines
                        if not line.startswith('ANYSPECS_AI_'):
                            existing_lines.append(line)
            
            # Add/update AnySpecs AI configuration
            new_lines = existing_lines
            if not any('# AnySpecs AI Configuration' in line for line in existing_lines):
                new_lines.extend(['', '# AnySpecs AI Configuration'])
            new_lines.append(f'ANYSPECS_AI_PROVIDER="{provider}"')
            
            if settings.get('api_key'):
                new_lines.append(f'ANYSPECS_AI_API_KEY="{settings["api_key"]}"')
            
            if settings.get('model'):
                new_lines.append(f'ANYSPECS_AI_MODEL="{settings["model"]}"')
            
            if settings.get('group_id'):
                new_lines.append(f'ANYSPECS_AI_GROUP_ID="{settings["group_id"]}"')
            
            if settings.get('temperature') is not None:
                new_lines.append(f'ANYSPECS_AI_TEMPERATURE={settings["temperature"]}')
            
            if settings.get('max_tokens') is not None:
                new_lines.append(f'ANYSPECS_AI_MAX_TOKENS={settings["max_tokens"]}')
            
            # Write updated .env file
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
                if new_lines:  # Add final newline if file has content
                    f.write('\n')
            
            self.logger.info(f"AI configuration saved to .env: {self.env_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving to .env file: {e}")
            return False


# Global AI config manager instance
ai_config = AIConfigManager()