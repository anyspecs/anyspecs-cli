"""
Configuration management for AnySpecs CLI.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration class for AnySpecs."""
    
    def __init__(self):
        self.config_dir = Path.home() / '.anyspecs'
        self.config_file = self.config_dir / 'config.json'
        self._config = {}
        
        # Default configuration
        self.defaults = {
            'export': {
                'default_format': 'markdown',
                'default_output_dir': str(Path.cwd())
            },
            'sources': {
                'cursor': {
                    'enabled': True
                },
                'claude': {
                    'enabled': True
                }
            },
            'server': {
                'default_url': 'http://localhost:4999'
            }
        }
        
        self.load()
    
    def load(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                import json
                with open(self.config_file, 'r') as f:
                    self._config = json.load(f)
            except Exception:
                self._config = {}
        
        # Merge with defaults
        self._merge_defaults()
    
    def save(self):
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            import json
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception:
            pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set a configuration value using dot notation."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save()
    
    def _merge_defaults(self):
        """Merge default configuration with loaded config."""
        def merge_dict(target: dict, source: dict):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    merge_dict(target[key], value)
                elif key not in target:
                    target[key] = value
        
        merge_dict(self._config, self.defaults)


# Global configuration instance
config = Config() 