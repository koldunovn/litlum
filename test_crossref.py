#!/usr/bin/env python3
"""
Test script for the CrossRef API implementation.
This script tests the FeedParser with CrossRef journal configurations.
"""

import sys
from pprint import pprint
from publication_reader.feeds.parser import FeedParser
from publication_reader.config import Config

def test_crossref_parser():
    """Test the CrossRef API parser with the configured journals."""
    # Initialize the parser
    parser = FeedParser()
    
    # Get the configuration
    config = Config()
    feeds = config.get_feeds()
    
    # Test each CrossRef feed
    for feed in feeds:
        if feed.get('type') == 'crossref':
            print(f"\nTesting CrossRef API for journal: {feed.get('name')} (ISSN: {feed.get('issn')})")
            
            # Parse the feed
            publications = parser.parse_feed(feed)
            
            # Print summary
            print(f"Found {len(publications)} publications")
            
            # Print first publication details (if any)
            if publications:
                print("\nFirst publication details:")
                first_pub = publications[0]
                pprint({
                    'title': first_pub.get('title'),
                    'journal': first_pub.get('journal'),
                    'doi': first_pub.get('doi'),
                    'url': first_pub.get('url'),
                    'pub_date': first_pub.get('pub_date'),
                    'abstract_preview': first_pub.get('abstract', '')[:150] + '...' if first_pub.get('abstract') else 'No abstract'
                })
            else:
                print("No publications found")

if __name__ == "__main__":
    test_crossref_parser()
