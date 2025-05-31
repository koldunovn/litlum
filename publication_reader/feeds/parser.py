"""RSS feed parser for scientific publications."""

import feedparser
import html
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
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
            
        # Filter out non-research content like issue information, tables of contents, etc.
        non_research_keywords = [
            'issue information', 'table of contents', 'cover image', 
            'editorial board', 'masthead', 'editor', 'front matter',
            'back matter', 'volume information', 'errata', 'correction'
        ]
        
        # Check if the title contains any of the non-research keywords
        if any(keyword.lower() in title.lower() for keyword in non_research_keywords):
            return None
        
        # Extract URL
        url = entry.get('link', '')
        
        # Extract publication date
        pub_date = self._parse_date(entry)
        
        # Extract GUID or create one
        guid = entry.get('id', url)
        
        # Extract abstract
        abstract = self._extract_abstract(entry)
        
        # If there's no abstract, this might not be a research article
        if not abstract.strip() and 'issue' in title.lower():
            return None
        
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
        # Check if it's a Wiley journal entry based on URL
        is_wiley = False
        if 'link' in entry and 'wiley.com' in entry.get('link', ''):  
            is_wiley = True
        
        # For Wiley journals, check the content field which may contain the abstract
        if is_wiley:
            # The content field in Wiley journals often contains the abstract
            if 'content' in entry and entry.content:
                for content_item in entry.content:
                    if isinstance(content_item, dict):
                        if content_item.get('type') == 'text/html' and 'value' in content_item:
                            html_content = content_item.get('value', '')
                            # Try to extract abstract from HTML
                            # First try to find an abstract section
                            abstract_match = re.search(r'<section[^>]*class="abstract[^>]*>(.*?)</section>', html_content, re.DOTALL)
                            if abstract_match:
                                cleaned = self._clean_html(abstract_match.group(1))
                                if cleaned:
                                    return cleaned
                                
                            # Try to find content with <h2>Abstract</h2> or similar
                            abstract_match = re.search(r'<h2[^>]*>\s*Abstract\s*</h2>(.*?)(?:<h2|<div class="section)', html_content, re.DOTALL)
                            if abstract_match:
                                cleaned = self._clean_html(abstract_match.group(1))
                                if cleaned:
                                    return cleaned
                                    
                            # Try to find any paragraph content that isn't metadata
                            paragraphs = re.findall(r'<p>(.*?)</p>', html_content, re.DOTALL)
                            if paragraphs:
                                # Skip first paragraph if it looks like metadata
                                for para in paragraphs:
                                    cleaned = self._clean_html(para)
                                    # Skip metadata paragraphs (journal info, dates, etc.)
                                    if len(cleaned) > 100 and not ('Volume' in cleaned and 'Issue' in cleaned):
                                        return cleaned
        
        # Try to get from summary
        if 'summary' in entry:
            content = self._clean_html(entry.summary)
            if len(content) > 50 and not (
                content.startswith("Journal of") and 
                ("Volume" in content) and 
                ("Issue" in content)):
                return content
        
        # Try to get from content
        if 'content' in entry and entry.content:
            for content in entry.content:
                if 'value' in content:
                    cleaned = self._clean_html(content.value)
                    if len(cleaned) > 50 and not (
                        cleaned.startswith("Journal of") and 
                        ("Volume" in cleaned) and 
                        ("Issue" in cleaned)):
                        return cleaned
        
        # Try to get from description, but skip if it's just journal metadata
        if 'description' in entry:
            description = self._clean_html(entry.description)
            # Skip if it's just journal metadata (common in Wiley feeds)
            if not (description.startswith("Journal of") and 
                    ("Volume" in description) and 
                    ("Issue" in description)):
                return description
        
        # Special case for Wiley journals - try to extract from HTML content
        if is_wiley:
            # Check for raw HTML content that might contain the abstract
            if hasattr(entry, 'summary_detail') and entry.summary_detail.get('type') == 'text/html':
                html_content = entry.summary_detail.get('value', '')
                if '<div class="abstract-group">' in html_content:
                    abstract_match = re.search(r'<div class="abstract-group">.*?<p>(.*?)</p>', html_content, re.DOTALL)
                    if abstract_match:
                        return self._clean_html(abstract_match.group(1))
            
            # Try parsing the full HTML content if available
            if hasattr(entry, 'content') and entry.content:
                for content_item in entry.content:
                    if hasattr(content_item, 'type') and content_item.type == 'text/html':
                        html = content_item.value
                        # Look for abstract div or class
                        abstract_match = re.search(r'<section class="abstract[^>]*>(.*?)</section>', html, re.DOTALL)
                        if abstract_match:
                            return self._clean_html(abstract_match.group(1))
        
        # Last resort: if we can't find a proper abstract, return a placeholder
        # This will prevent the entry from being filtered out
        if is_wiley:
            return "[Abstract not available in RSS feed. Please visit the article URL for full abstract.]"            
        
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
