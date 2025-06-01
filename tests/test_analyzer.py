"""Tests for the LLM analyzer."""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import re
from pathlib import Path

# Add the project root directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from litlum.llm.analyzer import OllamaAnalyzer


class TestOllamaAnalyzer(unittest.TestCase):
    """Test cases for the OllamaAnalyzer class."""

    def setUp(self):
        """Set up test cases."""
        # Create a mock config dictionary for testing
        self.mock_config = {
            "model": "llama3.2",
            "host": "http://localhost:11434",
            "relevance_prompt": "Analyze this scientific publication and determine if it's relevant based on the following interests: test interest. Rate relevance from 0-10 and explain why.",
            "summary_prompt": "Create a concise summary of this scientific publication highlighting key findings and methodology."
        }
        self.analyzer = OllamaAnalyzer(self.mock_config)

    @patch('ollama.chat')
    def test_extract_relevance_standard_format(self, mock_ollama_chat):
        """Test extracting relevance score from standard 'N/10' format."""
        # Mock the ollama.chat response
        mock_ollama_chat.return_value = {
            'message': {'content': 'I would rate the relevance of this publication as 7/10.'}
        }
        
        relevance, explanation = self.analyzer._determine_relevance("Test Title", "Test Abstract")
        self.assertEqual(relevance, 7)

    @patch('ollama.chat')
    def test_extract_relevance_with_colon(self, mock_ollama_chat):
        """Test extracting relevance score from 'Relevance: N' format."""
        # Mock the ollama.chat response
        mock_ollama_chat.return_value = {
            'message': {'content': 'Relevance: 8\nThe publication discusses topics related to the interests.'}
        }
        
        relevance, explanation = self.analyzer._determine_relevance("Test Title", "Test Abstract")
        self.assertEqual(relevance, 8)

    @patch('ollama.chat')
    def test_extract_relevance_with_is(self, mock_ollama_chat):
        """Test extracting relevance score from 'relevance is N' format."""
        # Mock the ollama.chat response
        mock_ollama_chat.return_value = {
            'message': {'content': 'The relevance is 5 because the publication partially addresses the interests.'}
        }
        
        relevance, explanation = self.analyzer._determine_relevance("Test Title", "Test Abstract")
        self.assertEqual(relevance, 5)

    @patch('ollama.chat')
    def test_extract_relevance_from_score_word(self, mock_ollama_chat):
        """Test extracting relevance score from 'score N' format."""
        # Mock the ollama.chat response
        mock_ollama_chat.return_value = {
            'message': {'content': 'I give this a score of 9 due to its direct relevance to the interests.'}
        }
        
        relevance, explanation = self.analyzer._determine_relevance("Test Title", "Test Abstract")
        self.assertEqual(relevance, 9)

    @patch('ollama.chat')
    def test_extract_relevance_fallback(self, mock_ollama_chat):
        """Test extracting relevance score using fallback method (any number)."""
        # Mock the ollama.chat response
        mock_ollama_chat.return_value = {
            'message': {'content': 'This publication gets 6 for addressing some of the interests.'}
        }
        
        relevance, explanation = self.analyzer._determine_relevance("Test Title", "Test Abstract")
        self.assertEqual(relevance, 6)

    @patch('ollama.chat')
    def test_no_relevance_found(self, mock_ollama_chat):
        """Test handling case where no relevance score is found."""
        # Mock the ollama.chat response with no clear score
        mock_ollama_chat.return_value = {
            'message': {'content': 'This publication discusses machine learning approaches.'}
        }
        
        relevance, explanation = self.analyzer._determine_relevance("Test Title", "Test Abstract")
        self.assertEqual(relevance, 0)  # Should default to 0 if no score found

    @patch('ollama.chat')
    def test_extract_explanation(self, mock_ollama_chat):
        """Test extracting the explanation from the LLM response."""
        # Mock the ollama.chat response with an explanation
        mock_ollama_chat.return_value = {
            'message': {'content': 'I would rate this 8/10.\n\nExplanation: This is highly relevant because it covers multiple interests directly.'}
        }
        
        relevance, explanation = self.analyzer._determine_relevance("Test Title", "Test Abstract")
        self.assertEqual(relevance, 8)
        self.assertIn("highly relevant", explanation)

    def test_create_relevance_prompt(self):
        """Test creating a relevance prompt with interests."""
        # Test the actual _create_relevance_prompt method
        title = "Test Title"
        abstract = "Test Abstract"
        prompt = self.analyzer._create_relevance_prompt(title, abstract)
        
        # Verify the prompt contains the title and abstract
        self.assertIn(title, prompt)
        self.assertIn(abstract, prompt)
        
        # Verify it contains the base prompt from config
        self.assertIn("Analyze this scientific publication", prompt)


if __name__ == "__main__":
    unittest.main()
