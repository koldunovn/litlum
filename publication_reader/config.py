"""Configuration module for the publication reader application."""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any

CONFIG_PATH = Path.home() / ".config" / "publication_reader" / "config.yaml"
DEFAULT_CONFIG = {
    "crossref": {
        "days_range": 10  # Default number of days to look back for all journals
    },
    "feeds": [
        {
        "name": "JGR Oceans",
        "type": "crossref",
        "issn": "2169-9291"
        # Removed specific days_range to use global default
        },
        {
        "name": "Ocean Science",
        "type": "crossref",
        "issn": "1812-0792"
        # Removed specific days_range to use global default
        },
        {
        "name": "BAMS",
        "type": "crossref",
        "issn": "1520-0477"
        },
        {
        "name": "GMD",
        "type": "crossref",
        "issn": "1991-9603"
        },
        {
        "name": "GRL",
        "type": "crossref",
        "issn": "1944-8007"
        },
        {
        "name": "JAMES",
        "type": "crossref",
        "issn": "1942-2466"
        },
        {
        "name": "JGR Atmospheres",
        "type": "crossref",
        "issn": "2169-8996"
        },
        {
        "name": "Journal of Climate",
        "type": "crossref",
        "issn": "1520-0442"
        },
        {
        "name": "JPO",
        "type": "crossref",
        "issn": "1520-0485"
        },
        {
        "name": "Monthly Weather Review",
        "type": "crossref",
        "issn": "1520-0493"
        },
        {
        "name": "Nature Climate Change",
        "type": "crossref",
        "issn": "1758-6798"
        },
        {
        "name": "Nature Geoscience",
        "type": "crossref",
        "issn": "1752-0908"
        }
        # Add more CrossRef journals as needed
        # {
        #   "name": "Journal Name",
        #   "type": "crossref",
        #   "issn": "XXXX-XXXX",
        #   "days_range": 7  # Optional: override global days_range for this journal
        # }
        
    ],
    "database": {
        "path": "~/.local/share/publication_reader/publications.db"
    },
    "interests": [
        "Arctic ocean", 
        "climate modelling", 
        "high resolution modelling", 
        # "artificial intelligence", 
        # "machine learning", 
        "sea ice", 
        "Southern Ocean", 
        "climate change"
    ],
    "ollama": {
        "model": "llama3.2",
        "host": "http://localhost:11434",
        "relevance_prompt": "Analyze this scientific publication and determine if it's relevant based on the following interests: {interests}. Rate relevance from 0-10 and explain why. Keep your explanation brief (1-2 sentences).",
        "summary_prompt": "Create a very concise summary (1-2 sentences) of this scientific publication highlighting key findings and briefly explain its relevance to the following interests: {interests}."
    },
    "reports": {
        "path": "~/.local/share/publication_reader/reports",
        "min_relevance": 5
    },
    "web": {
        "path": "~/.local/share/publication_reader/web",
        "title": "Publication Reader"
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
    
    def get_interests(self) -> List[str]:
        """Get the list of interests for determining publication relevance.
        
        Returns:
            List of interest topics as strings
        """
        return self.config.get('interests', [])
    
    def get_ollama_config(self) -> Dict[str, Any]:
        """Get Ollama LLM configuration with interests formatted into prompts.
        
        Returns:
            Ollama configuration dictionary with formatted prompts
        """
        ollama_config = self.config.get('ollama', DEFAULT_CONFIG['ollama'])
        
        # Format the interests into the prompts
        interests = self.get_interests()
        interests_str = ", ".join(interests)
        
        # Replace the placeholder in the prompts
        if 'relevance_prompt' in ollama_config:
            ollama_config['relevance_prompt'] = ollama_config['relevance_prompt'].format(interests=interests_str)
        
        if 'summary_prompt' in ollama_config:
            ollama_config['summary_prompt'] = ollama_config['summary_prompt'].format(interests=interests_str)
        
        return ollama_config
    
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
    
    def get_web_path(self) -> str:
        """Get the path for the static website.
        
        Returns:
            Web path
        """
        path = self.config.get('web', {}).get('path', DEFAULT_CONFIG['web']['path'])
        web_path = os.path.expanduser(path)
        os.makedirs(web_path, exist_ok=True)
        return web_path
    
    def save(self) -> None:
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.safe_dump(self.config, f)
