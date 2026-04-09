"""Configuration manager for persisting GUI settings."""

import json
import os
from pathlib import Path


class ConfigManager:
    """
    Manages application configuration persistence.
    
    Saves settings to JSON file in user's home directory.
    Does NOT save API keys for security reasons.
    """
    
    DEFAULT_CONFIG_FILE = Path.home() / '.video_downloader_config.json'
    
    DEFAULT_CONFIG = {
        'download': {
            'output_dir': 'dump',
            'last_url': '',
        },
        'transcribe': {
            'output_dir': 'dump',
            'last_file': '',
            'device': 'cpu',
            'model_size': 'base',
        },
        'analyze': {
            'output_dir': 'dump',
            'last_file': '',
            'auth_method': 'direct',
            'endpoint': 'https://api.anthropic.com/v1/messages',
            'model_name': 'claude-opus-4-5-20251101',
            'aws_secret_name': 'anthropic/default',
            'aws_region': 'eu-west-2',
        },
        'pipeline': {
            'output_dir': 'dump',
            'last_url': '',
            'auth_method': 'direct',
            'endpoint': 'https://api.anthropic.com/v1/messages',
            'model_name': 'claude-opus-4-5-20251101',
            'aws_secret_name': 'anthropic/default',
            'aws_region': 'eu-west-2',
            'transcribe_device': 'cpu',
            'transcribe_model': 'base',
        }
    }
    
    def __init__(self, config_file=None):
        """
        Initialize config manager.
        
        Args:
            config_file (str, optional): Path to config file. If None, uses default.
        """
        self.config_file = Path(config_file) if config_file else self.DEFAULT_CONFIG_FILE
        self.config = self._load_config()
    
    def _load_config(self):
        """
        Load configuration from file.
        
        Returns:
            dict: Configuration dictionary
        """
        if not self.config_file.exists():
            return self.DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Merge with defaults to handle new settings in updates
            config = self.DEFAULT_CONFIG.copy()
            for section, values in loaded_config.items():
                if section in config:
                    config[section].update(values)
                else:
                    config[section] = values
            
            return config
        
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """
        Save configuration to file.
        
        Returns:
            bool: True if saved successfully
        """
        try:
            # Create parent directory if it doesn't exist
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            
            return True
        
        except Exception as e:
            print(f"Error: Could not save config file: {e}")
            return False
    
    def get(self, section, key, default=None):
        """
        Get configuration value.
        
        Args:
            section (str): Section name ('download', 'transcribe', 'analyze', 'pipeline')
            key (str): Setting key
            default: Default value if not found
        
        Returns:
            Value from config or default
        """
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section, key, value):
        """
        Set configuration value.
        
        Args:
            section (str): Section name
            key (str): Setting key
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
    
    def update_section(self, section, values):
        """
        Update multiple values in a section.
        
        Args:
            section (str): Section name
            values (dict): Dictionary of key-value pairs to update
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section].update(values)
    
    def get_section(self, section):
        """
        Get entire section.
        
        Args:
            section (str): Section name
        
        Returns:
            dict: Section configuration
        """
        return self.config.get(section, {}).copy()
    
    def reset(self):
        """Reset configuration to defaults."""
        self.config = self.DEFAULT_CONFIG.copy()
        return self.save_config()
    
    def delete_config_file(self):
        """
        Delete the configuration file.
        
        Returns:
            bool: True if deleted successfully
        """
        try:
            if self.config_file.exists():
                self.config_file.unlink()
            self.config = self.DEFAULT_CONFIG.copy()
            return True
        except Exception as e:
            print(f"Error: Could not delete config file: {e}")
            return False
