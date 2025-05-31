"""Configuration module for the publication reader application."""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any

CONFIG_PATH = Path.home() / ".config" / "publication_reader" / "config.yaml"
DEFAULT_CONFIG = {
    "feeds": [
        {
            "name": "Nature",
            "url": "https://www.nature.com/nature.rss",
            "type": "rss"
        },
        {
            "name": "Science",
            "url": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",
            "type": "rss"
        },
        {
            "name": "PNAS",
            "url": "https://www.pnas.org/action/showFeed?type=etoc&feed=rss",
            "type": "rss"
        }
    ],
    "database": {
        "path": "~/.local/share/publication_reader/publications.db"
    },
    "ollama": {
        "model": "llama3.2",
        "host": "http://localhost:11434",
        "relevance_prompt": "Analyze this scientific publication and determine if it's relevant based on the following interests: Arctic ocean, climate modelling, high resolution modelling, artificial intelligence, machine learning, AI, ML, sea ice, Southern Ocean, climate change. Rate relevance from 0-10 and explain why.",
        "summary_prompt": "Create a concise summary of this scientific publication highlighting key findings and methodology and explain its relevance to Arctic ocean, climate modelling, high resolution modelling, artificial intelligence, machine learning, sea ice, Southern Ocean, climate change research."
    },
    "reports": {
        "path": "~/.local/share/publication_reader/reports",
        "min_relevance": 7
    }
}


class Config:
    """Configuration manager for the application."""
    
    def __init__(self):
        """Initialize the configuration."""
        self.config_path = CONFIG_PATH
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        config = DEFAULT_CONFIG
        with open(self.config_path, 'w') as f:
            yaml.safe_dump(config, f)
        return config
    
    def get_feeds(self) -> List[Dict[str, str]]:
        """Get configured RSS feeds."""
        return self.config.get('feeds', [])
    
    def get_database_path(self) -> str:
        """Get database path, expanding the user home directory."""
        path = self.config.get('database', {}).get('path', DEFAULT_CONFIG['database']['path'])
        return os.path.expanduser(path)
    
    def get_ollama_config(self) -> Dict[str, Any]:
        """Get Ollama configuration."""
        return self.config.get('ollama', DEFAULT_CONFIG['ollama'])
    
    def get_reports_path(self) -> str:
        """Get the path for storing reports.
        
        Returns:
            Reports path
        """
        path = self.config.get('reports', {}).get('path', DEFAULT_CONFIG['reports']['path'])
        reports_path = os.path.expanduser(path)
        os.makedirs(reports_path, exist_ok=True)
        return reports_path
    
    def get_min_relevance(self) -> int:
        """Get the minimum relevance threshold for reports.
        
        Returns:
            Minimum relevance score (0-10)
        """
        return self.config.get('reports', {}).get('min_relevance', 7)
    
    def save(self) -> None:
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.safe_dump(self.config, f)
