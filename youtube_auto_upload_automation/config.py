"""Configuration management for YouTube automation."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List


class Config:
    """Configuration manager for the YouTube automation system."""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration from JSON file.
        
        Args:
            config_file: Path to the configuration JSON file
        """
        self.config_file = config_file
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file.
        
        Returns:
            Dictionary containing configuration settings
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(
                f"Configuration file '{self.config_file}' not found. "
                f"Please copy 'config.json.example' to 'config.json' and configure it."
            )
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # YouTube API settings
    @property
    def client_secrets_file(self) -> str:
        """Get path to YouTube API client secrets file."""
        return self.config['youtube_api']['client_secrets_file']
    
    @property
    def token_file(self) -> str:
        """Get path to YouTube API token file."""
        return self.config['youtube_api']['token_file']
    
    @property
    def youtube_scopes(self) -> List[str]:
        """Get YouTube API scopes."""
        return self.config['youtube_api']['scopes']
    
    # Monitoring settings
    @property
    def watch_directories(self) -> List[str]:
        """Get list of directories to monitor for new videos."""
        return self.config['monitoring']['watch_directories']
    
    @property
    def supported_extensions(self) -> List[str]:
        """Get list of supported video file extensions."""
        return self.config['monitoring']['supported_extensions']
    
    @property
    def check_interval_seconds(self) -> int:
        """Get interval for checking file modifications."""
        return self.config['monitoring']['check_interval_seconds']
    
    @property
    def min_file_size_mb(self) -> float:
        """Get minimum file size in MB to process."""
        return self.config['monitoring']['min_file_size_mb']
    
    # Upload settings
    @property
    def default_privacy(self) -> str:
        """Get default privacy status for uploads."""
        return self.config['upload_settings']['default_privacy']
    
    @property
    def default_category(self) -> str:
        """Get default YouTube category ID."""
        return self.config['upload_settings']['default_category']
    
    @property
    def auto_publish(self) -> bool:
        """Check if videos should be automatically published."""
        return self.config['upload_settings']['auto_publish']
    
    @property
    def made_for_kids(self) -> bool:
        """Check if videos are made for kids."""
        return self.config['upload_settings']['made_for_kids']
    
    @property
    def notify_subscribers(self) -> bool:
        """Check if subscribers should be notified."""
        return self.config['upload_settings']['notify_subscribers']
    
    # Metadata settings
    @property
    def metadata_file_suffix(self) -> str:
        """Get suffix for metadata files."""
        return self.config['metadata']['metadata_file_suffix']
    
    @property
    def default_title_template(self) -> str:
        """Get default title template."""
        return self.config['metadata']['default_title_template']
    
    @property
    def default_description(self) -> str:
        """Get default description."""
        return self.config['metadata']['default_description']
    
    @property
    def default_tags(self) -> List[str]:
        """Get default tags."""
        return self.config['metadata']['default_tags']
    
    # Processing settings
    @property
    def move_after_upload(self) -> bool:
        """Check if files should be moved after upload."""
        return self.config['processing']['move_after_upload']
    
    @property
    def processed_directory(self) -> str:
        """Get directory for successfully processed videos."""
        return self.config['processing']['processed_directory']
    
    @property
    def failed_directory(self) -> str:
        """Get directory for failed uploads."""
        return self.config['processing']['failed_directory']
    
    @property
    def track_processed_videos(self) -> bool:
        """Check if processed videos should be tracked."""
        return self.config['processing']['track_processed_videos']
    
    @property
    def processed_videos_file(self) -> str:
        """Get path to processed videos tracking file."""
        return self.config['processing']['processed_videos_file']
    
    # Logging settings
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self.config['logging']['log_level']
    
    @property
    def log_file(self) -> str:
        """Get log file path."""
        return self.config['logging']['log_file']
    
    @property
    def max_log_size_mb(self) -> int:
        """Get maximum log file size in MB."""
        return self.config['logging']['max_log_size_mb']
    
    @property
    def backup_count(self) -> int:
        """Get number of log file backups to keep."""
        return self.config['logging']['backup_count']
