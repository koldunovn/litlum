"""RSS feed parser for scientific publications."""

import feedparser
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse


class FeedParser:
    """Parser for scientific publication RSS feeds."""
    
    def __init__(self):
        """Initialize the feed parser."""
        self.cleaned_feeds = []
    
    def parse_feed(self, feed_config: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse an RSS feed and extract publication information.
        
        Args:
            feed_config: Dictionary containing feed configuration
            
        Returns:
            List of dictionaries with publication data
        """
        feed_url = feed_config.get('url', '')
        journal_name = feed_config.get('name', '')
        
        if not feed_url:
            return []
        
        try:
            feed = feedparser.parse(feed_url)
            publications = []
            
            for entry in feed.entries:
                publication = self._extract_publication_data(entry, journal_name)
                if publication:
                    publications.append(publication)
            
            return publications
        except Exception as e:
            print(f"Error parsing feed {feed_url}: {str(e)}")
            return []
    
    def _extract_publication_data(self, entry: Dict[str, Any], journal_name: str) -> Optional[Dict[str, Any]]:
        """Extract publication data from an RSS feed entry.
        
        Args:
            entry: RSS feed entry
            journal_name: Name of the journal
            
        Returns:
            Dictionary with publication data or None if invalid
        """
        # Get title and clean it
        title = entry.get('title', '')
        if not title:
            return None
        
        # Extract URL
        url = entry.get('link', '')
        
        # Extract publication date
        pub_date = self._parse_date(entry)
        
        # Extract GUID or create one
        guid = entry.get('id', url)
        
        # Extract abstract
        abstract = self._extract_abstract(entry)
        
        return {
            'journal': journal_name,
            'title': title,
            'abstract': abstract,
            'url': url,
            'pub_date': pub_date,
            'guid': guid
        }
    
    def _parse_date(self, entry: Dict[str, Any]) -> str:
        """Parse publication date from feed entry.
        
        Args:
            entry: Feed entry
            
        Returns:
            ISO format date string
        """
        for date_field in ['published', 'updated', 'pubDate']:
            if date_field in entry:
                try:
                    parsed_date = datetime(*entry.get(f"{date_field}_parsed")[:6])
                    return parsed_date.isoformat()
                except (AttributeError, TypeError):
                    pass
        
        # Default to current time if no date found
        return datetime.now().isoformat()
    
    def _extract_abstract(self, entry: Dict[str, Any]) -> str:
        """Extract abstract from a feed entry.
        
        Args:
            entry: Feed entry
            
        Returns:
            Abstract text
        """
        # Try to get from summary
        if 'summary' in entry:
            return self._clean_html(entry.summary)
        
        # Try to get from content
        if 'content' in entry and entry.content:
            for content in entry.content:
                if 'value' in content:
                    return self._clean_html(content.value)
        
        # Try to get from description
        if 'description' in entry:
            return self._clean_html(entry.description)
        
        return ""
    
    @staticmethod
    def _clean_html(html_text: str) -> str:
        """Clean HTML from text.
        
        Args:
            html_text: Text containing HTML
            
        Returns:
            Cleaned text
        """
        # Simple HTML tag removal (for more complex cases, consider using a library like BeautifulSoup)
        clean_text = re.sub(r'<[^>]+>', ' ', html_text)
        
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text
