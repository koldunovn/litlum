"""Database module for managing SQLite operations."""

import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


class Database:
    """SQLite database handler for publications."""
    
    def __init__(self, db_path: str):
        """Initialize database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = os.path.expanduser(db_path)
        self._ensure_db_dir_exists()
        self.conn = self._connect()
        self._create_tables()
    
    def _ensure_db_dir_exists(self) -> None:
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)
    
    def _connect(self) -> sqlite3.Connection:
        """Connect to the SQLite database.
        
        Returns:
            SQLite connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _create_tables(self) -> None:
        """Create required tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Publications table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS publications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            journal TEXT NOT NULL,
            title TEXT NOT NULL,
            abstract TEXT,
            url TEXT,
            pub_date TEXT,
            guid TEXT UNIQUE,
            processed_date TEXT,
            relevance_score INTEGER,
            llm_summary TEXT,
            UNIQUE(journal, title)
        )
        ''')
        
        # Daily summaries table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            summary TEXT,
            created_at TEXT
        )
        ''')
        
        self.conn.commit()
    
    def add_publication(self, publication: Dict[str, Any]) -> int:
        """Add a publication to the database.
        
        Args:
            publication: Dictionary containing publication details
            
        Returns:
            ID of the inserted publication or -1 if already exists
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO publications 
            (journal, title, abstract, url, pub_date, guid, processed_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                publication.get('journal', ''),
                publication.get('title', ''),
                publication.get('abstract', ''),
                publication.get('url', ''),
                publication.get('pub_date', ''),
                publication.get('guid', ''),
                datetime.now().isoformat()
            ))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Publication already exists
            return -1
    
    def update_publication_analysis(self, pub_id: int, relevance_score: int, summary: str) -> None:
        """Update a publication with LLM analysis results.
        
        Args:
            pub_id: Publication ID
            relevance_score: Relevance score (0-10)
            summary: LLM-generated summary
        """
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE publications
        SET relevance_score = ?, llm_summary = ?
        WHERE id = ?
        ''', (relevance_score, summary, pub_id))
        self.conn.commit()
    
    def get_unprocessed_publications(self) -> List[Dict[str, Any]]:
        """Get publications that haven't been processed by the LLM.
        
        Returns:
            List of publication dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, journal, title, abstract, url, pub_date, guid
        FROM publications
        WHERE relevance_score IS NULL
        ''')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_publications_by_date(self, date: str, min_relevance: int = 0) -> List[Dict[str, Any]]:
        """Get publications processed on a specific date with minimum relevance score.
        
        Args:
            date: Date string in ISO format (YYYY-MM-DD)
            min_relevance: Minimum relevance score (0-10)
            
        Returns:
            List of publication dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, journal, title, abstract, url, pub_date, guid, relevance_score, llm_summary
        FROM publications
        WHERE date(processed_date) = ?
        AND (relevance_score IS NULL OR relevance_score >= ?)
        ORDER BY relevance_score DESC
        ''', (date, min_relevance))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_publications(self, days: int = 1, min_relevance: int = 0) -> List[Dict[str, Any]]:
        """Get recent publications from the last N days with minimum relevance score.
        
        Args:
            days: Number of days to look back
            min_relevance: Minimum relevance score (0-10)
            
        Returns:
            List of publication dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, journal, title, abstract, url, pub_date, guid, relevance_score, llm_summary
        FROM publications
        WHERE date(processed_date) >= date('now', ? || ' days')
        AND (relevance_score IS NULL OR relevance_score >= ?)
        ORDER BY 
            CASE WHEN relevance_score IS NULL THEN 1 ELSE 0 END,
            relevance_score DESC,
            pub_date DESC
        ''', (f'-{days}', min_relevance))
        return [dict(row) for row in cursor.fetchall()]
    
    def save_daily_summary(self, date: str, summary: str) -> int:
        """Save a daily summary to the database.
        
        Args:
            date: Date string in ISO format (YYYY-MM-DD)
            summary: Summary text
            
        Returns:
            ID of the inserted summary
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO daily_summaries 
            (date, summary, created_at)
            VALUES (?, ?, ?)
            ''', (date, summary, datetime.now().isoformat()))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Update existing summary
            cursor.execute('''
            UPDATE daily_summaries
            SET summary = ?, created_at = ?
            WHERE date = ?
            ''', (summary, datetime.now().isoformat(), date))
            self.conn.commit()
            return cursor.lastrowid
    
    def get_daily_summary(self, date: str) -> Optional[Dict[str, Any]]:
        """Get a daily summary for a specific date.
        
        Args:
            date: Date string in ISO format (YYYY-MM-DD)
            
        Returns:
            Summary dictionary or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, date, summary, created_at
        FROM daily_summaries
        WHERE date = ?
        ''', (date,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_publication_by_guid(self, guid: str) -> Optional[Dict[str, Any]]:
        """Get a publication by its GUID.
        
        Args:
            guid: Publication GUID
            
        Returns:
            Publication dictionary or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, journal, title, abstract, url, pub_date, guid, relevance_score, llm_summary
        FROM publications
        WHERE guid = ?
        ''', (guid,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
