"""Tests for the CrossRef API parser."""

import unittest
import inspect
from unittest.mock import patch, MagicMock
from urllib.parse import quote
import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from litlum.feeds.parser import FeedParser


class TestFeedParser(unittest.TestCase):
    """Test cases for the FeedParser class with CrossRef API."""

    def setUp(self):
        """Set up test environment."""
        self.parser = FeedParser()
        
        # Sample CrossRef API response item
        self.crossref_item = {
            'DOI': '10.1029/2024jc021997',
            'title': ['Asymmetric Response of the North Atlantic Gyres to the North Atlantic Oscillation'],
            'abstract': '<jats:title>Abstract</jats:title><jats:p>The North Atlantic Oscillation (NAO) is a leading mode of atmospheric variability, affecting the North Atlantic Ocean circulation through changes in wind stress and buoyancy forcing.</jats:p>',
            'published': {
                'date-parts': [[2025, 5, 30]]
            }
        }
        
        # Sample feed configuration
        self.feed_config = {
            'name': 'JGR Oceans',
            'type': 'crossref',
            'issn': '2169-9291'
            # No days_range specified - should use global default
        }

    def test_extract_pub_date_full(self):
        """Test extracting publication date with year, month, and day."""
        item = {
            'published': {
                'date-parts': [[2025, 5, 30]]
            }
        }
        expected = "2025-05-30T00:00:00"
        self.assertEqual(self.parser._extract_pub_date(item), expected)

    def test_extract_pub_date_year_month(self):
        """Test extracting publication date with only year and month."""
        item = {
            'published': {
                'date-parts': [[2025, 5]]
            }
        }
        expected = "2025-05-01T00:00:00"
        self.assertEqual(self.parser._extract_pub_date(item), expected)

    def test_extract_pub_date_year_only(self):
        """Test extracting publication date with only year."""
        item = {
            'published': {
                'date-parts': [[2025]]
            }
        }
        expected = "2025-01-01T00:00:00"
        self.assertEqual(self.parser._extract_pub_date(item), expected)

    def test_extract_pub_date_missing(self):
        """Test extracting publication date when missing or invalid."""
        # Should return current time if date is missing
        item = {}
        result = self.parser._extract_pub_date(item)
        # Just check that it returns an ISO formatted string
        self.assertIsInstance(result, str)
        self.assertTrue('T' in result)  # ISO format has T between date and time

    def test_extract_publication_data(self):
        """Test extracting publication data from CrossRef item."""
        result = self.parser._extract_publication_data(self.crossref_item, 'JGR Oceans')
        
        self.assertEqual(result['title'], 'Asymmetric Response of the North Atlantic Gyres to the North Atlantic Oscillation')
        self.assertEqual(result['journal'], 'JGR Oceans')
        self.assertEqual(result['doi'], '10.1029/2024jc021997')
        self.assertEqual(result['url'], 'https://doi.org/10.1029/2024jc021997')
        self.assertTrue('abstract' in result)
        self.assertTrue('pub_date' in result)
        self.assertEqual(result['guid'], 'crossref-10.1029/2024jc021997')

    @patch('requests.get')
    @patch('litlum.feeds.parser.Config')
    def test_parse_feed(self, mock_config, mock_get):
        """Test parsing CrossRef feed."""
        # Mock config to return a global days_range of 10
        mock_config_instance = MagicMock()
        mock_config_instance.get.return_value = 10  # For days_range
        mock_config_instance._config = {
            'crossref': {
                'days_range': 10
            }
        }
        mock_config.return_value = mock_config_instance
        
        # Create a mock response for the requests.get call
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'message': {
                'items': [self.crossref_item]
            }
        }
        mock_get.return_value = mock_response
        
        # Reset and re-initialize the parser to use our mocked config
        self.parser = FeedParser()
        
        # Call the parse_feed method
        result = self.parser.parse_feed(self.feed_config)
        
        # Verify the results
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], 'Asymmetric Response of the North Atlantic Gyres to the North Atlantic Oscillation')
        self.assertEqual(result[0]['journal'], 'JGR Oceans')
        self.assertEqual(result[0]['url'], 'https://doi.org/10.1029/2024jc021997')

    @patch('requests.get')
    def test_parse_feed_error(self, mock_get):
        """Test error handling in parse_feed method."""
        # Create a mock response that raises an exception
        mock_get.side_effect = Exception("API error")
        
        # Call the parse_feed method
        result = self.parser.parse_feed(self.feed_config)
        
        # Verify the results
        self.assertEqual(result, [])

    def test_missing_issn(self):
        """Test handling of missing ISSN in feed configuration."""
        # Create a feed config with missing ISSN
        feed_config = {
            'name': 'JGR Oceans',
            'type': 'crossref'
            # No ISSN provided
        }
        
        # Call the parse_feed method
        result = self.parser.parse_feed(feed_config)
        
        # Verify the results
        self.assertEqual(result, [])

    def test_non_research_title_filtering(self):
        """Test filtering of non-research content based on title."""
        # Create a CrossRef item with a non-research title
        item = {
            'DOI': '10.1029/2024jc021998',
            'title': ['Issue Information: Table of Contents'],
            'abstract': 'Some abstract content',
            'published': {
                'date-parts': [[2025, 5, 30]]
            }
        }
        
        # Extract publication data
        result = self.parser._extract_publication_data(item, 'JGR Oceans')
        
        # Should be filtered out
        self.assertIsNone(result)
        
    @patch('requests.get')
    @patch('datetime.datetime')
    @patch('litlum.feeds.parser.Config')
    def test_custom_days_range(self, mock_config, mock_datetime, mock_get):
        """Test that days_range parameter is used correctly."""
        # Mock config to return a global days_range of 10
        mock_config_instance = MagicMock()
        mock_config_instance._load_config.return_value = {
            'crossref': {
                'days_range': 10
            }
        }
        mock_config.return_value = mock_config_instance
        
        # Mock the current date to a fixed value
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2025-05-31"
        mock_datetime.now.return_value = mock_now
        
        # Create a mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'message': {
                'items': [self.crossref_item]
            }
        }
        mock_get.return_value = mock_response
        
        # Create a feed config with custom days_range that overrides global setting
        custom_feed_config = {
            'name': 'JGR Oceans',
            'type': 'crossref',
            'issn': '2169-9291',
            'days_range': 7  # 7 days instead of global default 10
        }
        
        # Reset and re-initialize the parser to use our mocked config
        self.parser = FeedParser()
        
        # Call the parse_feed method
        self.parser.parse_feed(custom_feed_config)
        
        # Verify the URL used in the request contains the correct date range
        called_url = mock_get.call_args[0][0]
        # The from-pub-date should be 7 days back from 2025-05-31
        # Since the URL parameters are encoded, we need to check the encoded value
        # Note: The implementation uses timedelta(days=days_range), which makes it exclusive of the start date
        # So for 7 days range from 2025-05-31, it should be 2025-05-25
        encoded_param = quote('from-pub-date:2025-05-25')
        self.assertIn(encoded_param, called_url)


if __name__ == "__main__":
    unittest.main()
