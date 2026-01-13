"""Configuration management for Cojumpendium scraper."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration manager for the scraper."""
    
    DEFAULT_CONFIG = {
        'general': {
            'download_dir': './downloads',
            'database': './cojumpendium.db',
            'log_level': 'INFO',
            'log_file': './scraper.log'
        },
        'http': {
            'max_concurrent': 10,
            'request_delay': 1.0,
            'timeout': 30,
            'max_retries': 3,
            'user_agent': 'Cojumpendium-Scraper/1.0 (Lost Media Archival Project)'
        },
        'wayback': {
            'rate_limit': 30,
            'use_cdx': True,
            'cdx_url': 'https://web.archive.org/cdx/search/cdx'
        },
        'search': {
            'terms': [
                'Cojum Dip', 'cojumdip', 'cojum-dip',
                'Bora Karaca', 'Turk Off', '2010 Remix'
            ],
            'date_range': {
                'start': 2004,
                'end': 2011
            }
        },
        'media': {
            'images': {
                'enabled': True,
                'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
                'max_size_mb': 50
            },
            'videos': {
                'enabled': True,
                'extensions': ['.mp4', '.avi', '.flv', '.wmv', '.mov'],
                'max_size_mb': 500
            },
            'audio': {
                'enabled': True,
                'extensions': ['.mp3', '.wav', '.ogg', '.flac', '.m4a'],
                'max_size_mb': 100
            }
        },
        'export': {
            'json': True,
            'csv': True,
            'html': True,
            'output_dir': './exports'
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config: Dict[str, Any] = self.DEFAULT_CONFIG.copy()
        
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
        elif os.path.exists('config.yaml'):
            self.load_config('config.yaml')
    
    def load_config(self, config_path: str) -> None:
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to YAML configuration file
        """
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    self._deep_update(self.config, user_config)
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
    
    def _deep_update(self, base: Dict, update: Dict) -> None:
        """Deep update of nested dictionaries.
        
        Args:
            base: Base dictionary to update
            update: Dictionary with updates
        """
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated path.
        
        Args:
            *keys: Path to configuration value
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        dirs = [
            self.get('general', 'download_dir', default='./downloads'),
            self.get('storage', 'downloads', default='./downloads'),
            self.get('storage', 'pages', default='./pages'),
            self.get('export', 'output_dir', default='./exports')
        ]
        for directory in dirs:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
