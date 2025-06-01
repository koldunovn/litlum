"""Tests for the configuration module."""

import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import sys
import yaml
from pathlib import Path

# Add the project root directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from litlum.config import Config


class TestConfig(unittest.TestCase):
    """Test cases for the Config class."""

    def setUp(self):
        """Set up test cases."""
        # Create a mock configuration for testing
        self.test_config = {
            "feeds": [
                {
                    "name": "Test Journal",
                    "url": "https://example.com/feed.rss",
                    "type": "rss"
                }
            ],
            "interests": [
                "Arctic ocean",
                "climate modelling",
                "sea ice",
                "climate change"
            ],
            "database": {
                "path": "~/test/publications.db"
            },
            "ollama": {
                "model": "llama3.2",
                "host": "http://localhost:11434",
                "relevance_prompt": "Analyze this scientific publication and determine if it's relevant based on the following interests: {interests}. Rate relevance from 0-10 and explain why. Keep your explanation brief (1-2 sentences).",
                "summary_prompt": "Create a very concise summary (1-2 sentences) of this scientific publication highlighting key findings and briefly explain its relevance to the following interests: {interests}."
            },
            "reports": {
                "path": "~/test/reports",
                "min_relevance": 6
            }
        }

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('os.path.expanduser')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.parent')
    def test_load_existing_config(self, mock_parent, mock_exists, mock_expanduser, mock_yaml_load, mock_file):
        """Test loading an existing configuration file."""
        # Set up mocks
        mock_exists.return_value = True
        mock_yaml_load.return_value = self.test_config
        mock_expanduser.return_value = "/home/user/test/path"
        
        # Create a config instance with our mocks
        config = Config()
        
        # Verify the config was loaded
        mock_file.assert_called_once()
        mock_yaml_load.assert_called_once()
        
        # Verify the loaded config matches our test config
        self.assertEqual(config.config, self.test_config)

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_dump')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.parent')
    def test_create_default_config(self, mock_parent, mock_exists, mock_yaml_dump, mock_file):
        """Test creating a default configuration file."""
        # Set up mocks
        mock_exists.return_value = False
        mock_parent.return_value = MagicMock()
        
        # Create a config instance with our mocks
        config = Config()
        
        # Verify a default config was created
        mock_file.assert_called_once()
        mock_yaml_dump.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('pathlib.Path.exists')
    def test_get_interests(self, mock_exists, mock_yaml_load, mock_file):
        """Test getting interests from the configuration."""
        # Set up mocks
        mock_exists.return_value = True
        mock_yaml_load.return_value = self.test_config
        
        # Create a config instance with our mocks
        config = Config()
        
        # Get interests
        interests = config.get_interests()
        
        # Verify the interests match our test config
        self.assertEqual(interests, self.test_config["interests"])
        self.assertEqual(len(interests), 4)
        self.assertIn("Arctic ocean", interests)
        self.assertIn("climate modelling", interests)
        self.assertIn("sea ice", interests)
        self.assertIn("climate change", interests)

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('pathlib.Path.exists')
    def test_format_prompts_with_interests(self, mock_exists, mock_yaml_load, mock_file):
        """Test that prompts are formatted with interests."""
        # Set up mocks
        mock_exists.return_value = True
        mock_yaml_load.return_value = self.test_config
        
        # Create a config instance with our mocks
        config = Config()
        
        # Get Ollama config with formatted prompts
        ollama_config = config.get_ollama_config()
        
        # Verify the prompts are formatted with interests
        interests_str = ", ".join(self.test_config["interests"])
        self.assertIn(interests_str, ollama_config["relevance_prompt"])
        self.assertIn(interests_str, ollama_config["summary_prompt"])
        
        # Make sure the placeholders are replaced
        self.assertNotIn("{interests}", ollama_config["relevance_prompt"])
        self.assertNotIn("{interests}", ollama_config["summary_prompt"])

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('pathlib.Path.exists')
    def test_get_min_relevance(self, mock_exists, mock_yaml_load, mock_file):
        """Test getting minimum relevance threshold from config."""
        # Set up mocks
        mock_exists.return_value = True
        mock_yaml_load.return_value = self.test_config
        
        # Create a config instance with our mocks
        config = Config()
        
        # Get minimum relevance
        min_relevance = config.get_min_relevance()
        
        # Verify the minimum relevance matches our test config
        self.assertEqual(min_relevance, 6)


if __name__ == "__main__":
    unittest.main()
