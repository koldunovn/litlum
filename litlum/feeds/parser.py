"""CrossRef API parser for scientific publications."""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from urllib.parse import quote
from ..config import Config


class FeedParser:
    """Parser for scientific publications using CrossRef API."""
    
    def __init__(self, current_date=None):
        """Initialize the feed parser.
        
        Args:
            current_date: Optional datetime to use as current date (for testing)
        """
        self.base_url = "https://api.crossref.org/works"
        self.user_agent = "PublicationReader/1.0 (mailto:you@awi.de)"  # Replace with your email
        self.config_manager = Config()
        # Don't call _load_config() here as it's already called in Config.__init__
        # and stores the config in self._config
        self.config = self.config_manager._config
        self._current_date = current_date or datetime.now()
    
    def parse_feed(self, feed_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse publications from CrossRef API based on ISSN.
        
        Args:
            feed_config: Dictionary containing feed configuration with ISSN
            
        Returns:
            List of dictionaries with publication data
        """
        journal_name = feed_config.get('name', '')
        issn = feed_config.get('issn', '')
        
        if not issn:
            print(f"Error: ISSN not provided for journal {journal_name}")
            return []
        
        try:
            # Get publications using journal-specific days_range if specified, otherwise use global default
            global_days_range = self.config.get('crossref', {}).get('days_range', 10)
            days_range = feed_config.get('days_range', global_days_range)
            from_date = (self._current_date - timedelta(days=days_range)).strftime("%Y-%m-%d")
            
            # Construct the API URL
            filter_params = f"issn:{issn},from-pub-date:{from_date},has-abstract:true"
            url = f"{self.base_url}?filter={quote(filter_params)}&select=DOI,title,abstract&sort=published&order=desc&rows=100"
            
            # Make the request
            headers = {"User-Agent": self.user_agent}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract and format publications
            publications = []
            if 'message' in data and 'items' in data['message']:
                for item in data['message']['items']:
                    publication = self._extract_publication_data(item, journal_name)
                    if publication:
                        publications.append(publication)
            
            return publications
        except Exception as e:
            print(f"Error fetching CrossRef data for {journal_name} (ISSN: {issn}): {str(e)}")
            return []
    
    def _extract_publication_data(self, item: Dict[str, Any], journal_name: str) -> Optional[Dict[str, Any]]:
        """Extract publication data from a CrossRef API item.
        
        Args:
            item: CrossRef API item
            journal_name: Name of the journal
            
        Returns:
            Dictionary with publication data or None if invalid
        """
        # Extract DOI
        doi = item.get('DOI', '')
        if not doi:
            return None
        
        # Extract title
        title = ""
        if 'title' in item and item['title']:
            title = item['title'][0]  # CrossRef returns titles as an array
        
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
        
        # Extract abstract
        abstract = ""
        if 'abstract' in item and item['abstract']:
            abstract = item['abstract'].strip()
        
        # Create URL from DOI
        url = f"https://doi.org/{doi}"
        
        # Extract publication date
        pub_date = self._extract_pub_date(item)
        
        # Create a unique GUID using the DOI
        guid = f"crossref-{doi}"
        
        return {
            'journal': journal_name,
            'title': title,
            'abstract': abstract,
            'url': url,
            'pub_date': pub_date,
            'guid': guid,
            'doi': doi
        }
    
    def _extract_pub_date(self, item: Dict[str, Any]) -> str:
        """Extract publication date from CrossRef item.
        
        Args:
            item: CrossRef API item
            
        Returns:
            ISO format date string
        """
        try:
            if 'published' in item:
                published = item['published']
                if 'date-parts' in published and published['date-parts']:
                    date_parts = published['date-parts'][0]
                    if len(date_parts) >= 3:
                        year, month, day = date_parts[:3]
                        return datetime(year, month, day).isoformat()
                    elif len(date_parts) == 2:
                        year, month = date_parts
                        return datetime(year, month, 1).isoformat()
                    elif len(date_parts) == 1:
                        year = date_parts[0]
                        return datetime(year, 1, 1).isoformat()
        except Exception as e:
            print(f"Error parsing date from CrossRef item: {str(e)}")
        
        # Default to current time if no date found
        return datetime.now().isoformat()
