"""Feed parser for scientific publications.

Supports:
- Crossref (journals by ISSN)
- DataCite-backed arXiv (preprints by subject category)
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from urllib.parse import quote
from ..config import Config


class FeedParser:
    """Parser for scientific publications using CrossRef and DataCite APIs."""
    
    def __init__(self, current_date=None):
        """Initialize the feed parser.
        
        Args:
            current_date: Optional datetime to use as current date (for testing)
        """
        self.crossref_base_url = "https://api.crossref.org/works"
        self.datacite_base_url = "https://api.datacite.org/dois"
        self.user_agent = "PublicationReader/1.0 (mailto:you@awi.de)"  # Replace with your email
        self.config_manager = Config()
        # Don't call _load_config() here as it's already called in Config.__init__
        # and stores the config in self._config
        self.config = self.config_manager._config
        self._current_date = current_date or datetime.now()
    
    def parse_feed(self, feed_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse publications from a configured feed.
        
        Args:
            feed_config: Dictionary containing feed configuration
            
        Returns:
            List of dictionaries with publication data
        """
        feed_type = (feed_config.get('type') or 'crossref').lower()
        if feed_type == 'arxiv':
            # Prefer arXiv native API; fallback to DataCite
            pubs = self._parse_arxiv_native(feed_config)
            if pubs:
                return pubs
            return self._parse_arxiv_datacite(feed_config)
        else:
            return self._parse_crossref(feed_config)

    def _parse_crossref(self, feed_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse publications from Crossref by ISSN."""
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
            url = f"{self.crossref_base_url}?filter={quote(filter_params)}&select=DOI,title,abstract&sort=published&order=desc&rows=100"

            # Make the request
            headers = {"User-Agent": self.user_agent}
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()

            # Extract and format publications
            publications = []
            if 'message' in data and 'items' in data['message']:
                for item in data['message']['items']:
                    publication = self._extract_crossref_publication(item, journal_name)
                    if publication:
                        publications.append(publication)

            return publications
        except Exception as e:
            print(f"Error fetching CrossRef data for {journal_name} (ISSN: {issn}): {str(e)}")
            return []
    
    def _extract_crossref_publication(self, item: Dict[str, Any], journal_name: str) -> Optional[Dict[str, Any]]:
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

    # Backward compatibility for existing tests expecting the old method name
    def _extract_publication_data(self, item: Dict[str, Any], journal_name: str) -> Optional[Dict[str, Any]]:
        """Backward-compatible wrapper for extracting Crossref publication data."""
        return self._extract_crossref_publication(item, journal_name)

    # -----------------------------
    # arXiv support (native API, then DataCite fallback)
    # -----------------------------
    def _parse_arxiv_native(self, feed_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch arXiv items via the native Atom API by category code (e.g., cs.AI)."""
        category = feed_config.get('category') or feed_config.get('arxiv_category')
        journal_name = feed_config.get('name', category or 'arXiv')
        if not category:
            return []

        try:
            global_days_range = self.config.get('datacite', {}).get('days_range', 10)
            days_range = feed_config.get('days_range', global_days_range)
            from_dt = self._current_date - timedelta(days=days_range)

            # arXiv Atom API
            # Docs: https://info.arxiv.org/help/api/user-manual.html
            # Example: http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=100
            base = "http://export.arxiv.org/api/query"
            params = {
                'search_query': f'cat:{category}',
                'sortBy': 'submittedDate',
                'sortOrder': 'descending',
                'max_results': 100,
            }
            headers = {"User-Agent": self.user_agent}
            resp = requests.get(base, params=params, headers=headers, timeout=30)
            resp.raise_for_status()
            text = resp.text

            # Minimal XML parsing to extract entries
            # Avoid adding dependencies; use simple string-based parsing for core fields
            entries: List[Dict[str, Any]] = []
            for chunk in text.split('<entry>')[1:]:
                entry_xml = chunk.split('</entry>')[0]

                def _extract(tag: str) -> Optional[str]:
                    start = entry_xml.find(f'<{tag}>')
                    if start == -1:
                        return None
                    start += len(tag) + 2
                    end = entry_xml.find(f'</{tag}>', start)
                    if end == -1:
                        return None
                    return entry_xml[start:end].strip()

                # Title
                title = _extract('title') or ''
                # Summary
                abstract = _extract('summary') or ''
                # Published
                published = _extract('published') or ''  # e.g., 2025-10-03T10:00:00Z
                # Link (grab first href from <link rel="alternate" href="..."/>)
                link = ''
                link_idx = entry_xml.find('<link')
                while link_idx != -1:
                    end_tag = entry_xml.find('/>', link_idx)
                    if end_tag == -1:
                        break
                    frag = entry_xml[link_idx:end_tag]
                    if 'rel="alternate"' in frag and 'href="' in frag:
                        href_start = frag.find('href="') + 6
                        href_end = frag.find('"', href_start)
                        link = frag[href_start:href_end]
                        break
                    link_idx = entry_xml.find('<link', end_tag)

                # ID (contains arXiv ID)
                arxiv_id = None
                id_text = _extract('id') or ''
                if id_text:
                    # id looks like: http://arxiv.org/abs/YYMM.NNNNNvX
                    arxiv_id = id_text.split('/abs/')[-1]

                # Date filter
                try:
                    pub_iso = published.replace('Z', '')
                    pub_dt = datetime.fromisoformat(pub_iso)
                    if pub_dt < from_dt:
                        continue
                except Exception:
                    pass

                if not title:
                    continue

                guid = f"arxiv-{arxiv_id}" if arxiv_id else (f"arxiv-{link}" if link else None)
                if not guid:
                    continue

                entries.append({
                    'journal': journal_name,
                    'title': title.strip(),
                    'abstract': abstract.strip(),
                    'url': link or id_text,
                    'pub_date': (published or self._current_date.isoformat()),
                    'guid': guid,
                    'doi': ''
                })

            print(f"[INFO] arXiv native ({category}) returned {len(entries)} records after filtering")
            return entries
        except Exception as e:
            print(f"[WARN] arXiv native API failed for {journal_name} (category: {category}): {e}")
            return []

    # DataCite (fallback)
    def _parse_arxiv_datacite(self, feed_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse arXiv preprints by subject using the DataCite API."""
        category = feed_config.get('category') or feed_config.get('arxiv_category')
        journal_name = feed_config.get('name', category or 'arXiv')

        if not category:
            print(f"Error: arXiv category not provided for feed {journal_name}")
            return []

        try:
            # Days range fallback similar to Crossref
            global_days_range = self.config.get('datacite', {}).get('days_range', 10)
            days_range = feed_config.get('days_range', global_days_range)
            from_date = (self._current_date - timedelta(days=days_range)).strftime("%Y-%m-%d")

            headers = {"User-Agent": self.user_agent}

            # Try multiple strategies to improve recall across categories
            strategies = [
                {"label": "provider+unquoted", "params": {
                    'prefix': '10.48550', 'provider-id': 'arxiv', 'query': f'subjects.subject:{category}',
                    'page[size]': 1000, 'sort': '-created'}},
                {"label": "provider+quoted", "params": {
                    'prefix': '10.48550', 'provider-id': 'arxiv', 'query': f'subjects.subject:"{category}"',
                    'page[size]': 1000, 'sort': '-created'}},
                {"label": "no-provider+quoted", "params": {
                    'prefix': '10.48550', 'query': f'subjects.subject:"{category}"',
                    'page[size]': 1000, 'sort': '-created'}},
            ]

            items = []
            used_label = None
            for strat in strategies:
                try:
                    response = requests.get(self.datacite_base_url, params=strat["params"], headers=headers, timeout=30)
                    response.raise_for_status()
                    payload = response.json()
                    items = payload.get('data', [])
                    used_label = strat["label"]
                    print(f"[INFO] DataCite(arXiv:{category}) strategy '{used_label}' returned {len(items)} records")
                    if items:
                        break
                except Exception as e:
                    print(f"[WARN] DataCite strategy '{strat['label']}' failed: {e}")

            # Final fallback: if still no items, try broad provider-id without subject and filter client-side
            if not items:
                try:
                    fallback_params = {
                        'prefix': '10.48550', 'provider-id': 'arxiv', 'page[size]': 1000, 'sort': '-created'
                    }
                    response = requests.get(self.datacite_base_url, params=fallback_params, headers=headers, timeout=30)
                    response.raise_for_status()
                    payload = response.json()
                    items = payload.get('data', [])
                    used_label = 'provider-only-fallback'
                    print(f"[INFO] DataCite(arXiv:{category}) fallback '{used_label}' returned {len(items)} records")
                except Exception as e:
                    print(f"[ERROR] DataCite fallback failed: {e}")

            publications: List[Dict[str, Any]] = []
            for rec in items:
                a = rec.get('attributes', {})

                # Filter by created date client-side to honor days_range
                created = a.get('created') or a.get('registered') or a.get('published')
                if created:
                    try:
                        # created may have a time component; compare dates
                        created_date = created[:10]
                        if created_date < from_date:
                            continue
                    except Exception:
                        pass

                # Client-side subject/category filter only for fallback strategy
                if used_label == 'provider-only-fallback':
                    subjects = [s.get('subject') for s in (a.get('subjects') or []) if isinstance(s, dict)]
                    if subjects:
                        cat = (category or '').lower()
                        if not any((s or '').lower().find(cat) != -1 for s in subjects):
                            # skip if none of the subjects contains the category code text
                            continue

                pub = self._extract_datacite_publication(a, journal_name)
                if pub:
                    publications.append(pub)

            try:
                print(f"[INFO] DataCite(arXiv:{category}) kept {len(publications)} records after filtering (strategy={used_label})")
            except Exception:
                pass

            return publications
        except Exception as e:
            print(f"Error fetching DataCite (arXiv) data for {journal_name} (category: {category}): {str(e)}")
            return []

    def _extract_datacite_publication(self, a: Dict[str, Any], journal_name: str) -> Optional[Dict[str, Any]]:
        """Normalize a DataCite arXiv record to our schema."""
        doi = a.get('doi')

        # Title
        title = None
        titles = a.get('titles') or []
        if titles and isinstance(titles, list):
            t0 = titles[0] or {}
            title = t0.get('title')
        if not title:
            return None

        # Abstract/description
        abstract = None
        descs = a.get('descriptions') or []
        if descs and isinstance(descs, list):
            abstract = (descs[0] or {}).get('description')
        abstract = abstract or ""

        # URL
        url = a.get('url') or (f"https://doi.org/{doi}" if doi else None)

        # Publication date preference: published -> created -> registered -> now
        pub_date = (
            a.get('published') or a.get('created') or a.get('registered') or datetime.now().isoformat()
        )

        # Build GUID: prefer DOI; else parse arXiv ID if DOI missing
        guid = None
        if doi:
            guid = f"datacite-{doi}"
        else:
            # Try to extract arXiv id from alternate identifiers
            # DataCite often provides identifiers like arXiv:YYMM.NNNNN
            for ident in a.get('alternateIdentifiers', []) or []:
                if isinstance(ident, dict) and 'alternateIdentifier' in ident:
                    aid = ident['alternateIdentifier']
                    if isinstance(aid, str) and 'arXiv' in aid:
                        guid = f"arxiv-{aid}"
                        break
        if not guid and doi:
            # As a fallback, derive an arXiv-like guid from DOI suffix
            try:
                suffix = doi.split('/', 1)[1]
                guid = f"arxiv-{suffix}"
            except Exception:
                guid = f"datacite-{doi}"
        if not guid:
            return None

        return {
            'journal': journal_name,
            'title': title,
            'abstract': abstract,
            'url': url or '',
            'pub_date': pub_date,
            'guid': guid,
            'doi': doi or ''
        }
