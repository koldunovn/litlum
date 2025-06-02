"""Configuration module for the LitLum application."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

# Paths
CONFIG_DIR = Path.home() / ".config" / "litlum"
CONFIG_PATH = CONFIG_DIR / "config.yaml"
DEFAULT_CONFIG_PATH = Path(__file__).parent / "default-config.yaml"


def load_yaml_config(file_path: Path) -> Dict[str, Any]:
    """Load a YAML configuration file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def ensure_config_dir() -> None:
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def expand_path(path: Union[str, Path]) -> Path:
    """Expand user and environment variables in a path."""
    return Path(os.path.expandvars(os.path.expanduser(str(path))))


class Config:
    """Configuration manager for the application."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the configuration.
        
        Args:
            config_path: Optional path to a custom config file
        """
        self.config_path = config_path or CONFIG_PATH
        self._config: Dict[str, Any] = {}
        self._load_config()

    # Class-level flag to track if we've already printed config info
    _config_loaded = False

    def _load_config(self) -> None:
        """Load configuration from file or create default."""
        # Load default config
        if not Config._config_loaded:
            print(f"[INFO] Loading default configuration from: {DEFAULT_CONFIG_PATH}")
            
        try:
            self._config = load_yaml_config(DEFAULT_CONFIG_PATH)
            if not Config._config_loaded:
                print("[INFO] Successfully loaded default configuration")
        except Exception as e:
            print(f"[ERROR] Failed to load default config: {e}")
            raise RuntimeError(f"Failed to load default config: {e}")
        
        # Load user config if it exists
        if self.config_path.exists():
            if not Config._config_loaded:
                print(f"[INFO] Loading user configuration from: {self.config_path}")
            try:
                user_config = load_yaml_config(self.config_path)
                self._update_config(user_config)
                if not Config._config_loaded:
                    print("[INFO] Successfully loaded user configuration")
            except Exception as e:
                if not Config._config_loaded:
                    print(f"[WARNING] Failed to load user config: {e}. Using default configuration.")
        elif not Config._config_loaded:
            print(f"[INFO] No user configuration found at {self.config_path}. Using default configuration.")
        
        # Mark config as loaded after first successful load
        Config._config_loaded = True

    def _update_config(self, new_config: Dict[str, Any], target: Optional[Dict[str, Any]] = None) -> None:
        """Recursively update the configuration.
        
        Args:
            new_config: New configuration values to apply
            target: The target dictionary to update (defaults to self._config)
        """
        if target is None:
            target = self._config
            
        for key, value in new_config.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_config(value, target[key])
            else:
                target[key] = value

    def get(self, *keys: str, default: Any = None) -> Any:
        """Get a nested config value by dot notation."""
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def get_database_path(self) -> Path:
        """Get database path, expanding the user home directory."""
        db_path = self.get("database", "path") or "~/.local/share/litlum/litlum.db"
        return expand_path(db_path)

    def get_reports_path(self) -> Path:
        """Get the path for storing reports."""
        # First check if environment variable is set
        if os.environ.get('LITLUM_REPORTS_DIR'):
            return Path(os.environ['LITLUM_REPORTS_DIR'])
        # Then check config file
        reports_path = self.get("storage", "reports") or "~/.local/share/litlum/reports"
        return expand_path(reports_path)

    def get_web_path(self) -> Path:
        """Get the path for the static website."""
        # First check if environment variable is set
        if os.environ.get('LITLUM_WEB_DIR'):
            return Path(os.environ['LITLUM_WEB_DIR'])
        # Then check config file
        web_path = self.get("storage", "web") or "~/.local/share/litlum/web"
        return expand_path(web_path)

    def get_ollama_config(self) -> Dict[str, Any]:
        """Get Ollama LLM configuration with interests formatted into prompts."""
        ollama_config = self.get("ollama") or {}
        interests = self.get("interests") or []
        
        # Format prompts with interests if they contain {interests} placeholder
        if "system_prompt" in ollama_config and "{interests}" in ollama_config["system_prompt"]:
            ollama_config["system_prompt"] = ollama_config["system_prompt"].format(
                interests=", ".join(interests)
            )
            
        if "relevance_prompt" in ollama_config and "{interests}" in ollama_config["relevance_prompt"]:
            ollama_config["relevance_prompt"] = ollama_config["relevance_prompt"].format(
                interests=", ".join(interests)
            )
            
        return ollama_config

    def get_feeds(self) -> List[Dict[str, Any]]:
        """Get configured RSS feeds."""
        return self.get("feeds") or []

    def get_interests(self) -> List[str]:
        """Get the list of interests for determining publication relevance."""
        return self.get("interests") or []

    def get_min_relevance(self) -> float:
        """Get the minimum relevance threshold for reports."""
        return float(self.get("reports", "min_relevance") or 5.0)

    def save(self) -> None:
        """Save current configuration to file."""
        ensure_config_dir()
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)
