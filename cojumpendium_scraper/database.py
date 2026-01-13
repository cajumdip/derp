"""Database management for Cojumpendium scraper."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import json


class Database:
    """SQLite database manager for tracking discovered content."""
    
    def __init__(self, db_path: str = './cojumpendium.db'):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Discovered URLs from Wayback search
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discovered_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT,
                archive_url TEXT UNIQUE NOT NULL,
                archive_timestamp TEXT,
                search_phrase TEXT,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                content_hash TEXT,
                metadata TEXT
            )
        ''')
        
        # Media found on pages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_id INTEGER,
                media_url TEXT NOT NULL,
                media_type TEXT,
                local_path TEXT,
                file_hash TEXT,
                downloaded_at TIMESTAMP,
                FOREIGN KEY (url_id) REFERENCES discovered_urls(id)
            )
        ''')
        
        # Search progress tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_phrase TEXT NOT NULL,
                search_method TEXT NOT NULL,
                last_offset INTEGER DEFAULT 0,
                last_timestamp TEXT,
                completed BOOLEAN DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Request log for rate limiting
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS request_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status_code INTEGER,
                success BOOLEAN
            )
        ''')
        
        # Legacy tables for compatibility
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                source_platform TEXT NOT NULL,
                archive_date TEXT,
                content_type TEXT,
                status TEXT DEFAULT 'pending',
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_checked TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_id INTEGER,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_hash TEXT UNIQUE,
                file_size INTEGER,
                original_url TEXT,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed BOOLEAN DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (url_id) REFERENCES urls(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_term TEXT NOT NULL,
                platform TEXT NOT NULL,
                results_count INTEGER,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_urls_platform ON urls(source_platform)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_urls_status ON urls(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_hash ON media_files(file_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_type ON media_files(file_type)')
        
        # New indexes for discovered_urls
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_discovered_urls_status ON discovered_urls(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_discovered_urls_phrase ON discovered_urls(search_phrase)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_discovered_urls_timestamp ON discovered_urls(archive_timestamp)')
        
        # Indexes for media
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_url_id ON media(url_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_type ON media(media_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_hash ON media(file_hash)')
        
        # Indexes for search_progress
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_search_progress_phrase_method ON search_progress(search_phrase, search_method)')
        
        # Indexes for request_log
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_request_log_timestamp ON request_log(timestamp)')
        
        self.conn.commit()
    
    def add_url(self, url: str, source_platform: str, archive_date: Optional[str] = None,
                content_type: Optional[str] = None, metadata: Optional[Dict] = None) -> int:
        """Add a discovered URL to the database.
        
        Args:
            url: The URL
            source_platform: Platform where URL was found
            archive_date: Archive date if applicable
            content_type: Type of content
            metadata: Additional metadata as dict
            
        Returns:
            URL ID
        """
        cursor = self.conn.cursor()
        metadata_json = json.dumps(metadata) if metadata else None
        
        try:
            cursor.execute('''
                INSERT INTO urls (url, source_platform, archive_date, content_type, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (url, source_platform, archive_date, content_type, metadata_json))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # URL already exists, get its ID
            cursor.execute('SELECT id FROM urls WHERE url = ?', (url,))
            row = cursor.fetchone()
            return row['id'] if row else -1
    
    def add_media_file(self, file_path: str, file_type: str, file_hash: str,
                      file_size: int, original_url: str, url_id: Optional[int] = None) -> int:
        """Add a downloaded media file to the database.
        
        Args:
            file_path: Local path to file
            file_type: Type of media (image/video/audio)
            file_hash: Hash of file for deduplication
            file_size: Size in bytes
            original_url: Original URL of media
            url_id: Associated URL ID if any
            
        Returns:
            Media file ID, or -1 if duplicate
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO media_files 
                (url_id, file_path, file_type, file_hash, file_size, original_url)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (url_id, file_path, file_type, file_hash, file_size, original_url))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # File already exists (duplicate hash)
            return -1
    
    def update_url_status(self, url_id: int, status: str) -> None:
        """Update the status of a URL.
        
        Args:
            url_id: URL ID
            status: New status (pending/processing/completed/error)
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE urls 
            SET status = ?, last_checked = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, url_id))
        self.conn.commit()
    
    def get_pending_urls(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get pending URLs to process.
        
        Args:
            limit: Maximum number of URLs to return
            
        Returns:
            List of URL records
        """
        cursor = self.conn.cursor()
        query = 'SELECT * FROM urls WHERE status = "pending"'
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dictionary with various statistics
        """
        cursor = self.conn.cursor()
        
        stats = {}
        
        # URL counts by status
        cursor.execute('SELECT status, COUNT(*) as count FROM urls GROUP BY status')
        stats['urls_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Media counts by type
        cursor.execute('SELECT file_type, COUNT(*) as count FROM media_files GROUP BY file_type')
        stats['media_by_type'] = {row['file_type']: row['count'] for row in cursor.fetchall()}
        
        # Total storage size
        cursor.execute('SELECT SUM(file_size) as total_size FROM media_files')
        row = cursor.fetchone()
        stats['total_storage_bytes'] = row['total_size'] or 0
        
        # Platform counts
        cursor.execute('SELECT source_platform, COUNT(*) as count FROM urls GROUP BY source_platform')
        stats['urls_by_platform'] = {row['source_platform']: row['count'] for row in cursor.fetchall()}
        
        return stats
    
    def mark_reviewed(self, media_id: int, notes: Optional[str] = None) -> None:
        """Mark a media file as reviewed.
        
        Args:
            media_id: Media file ID
            notes: Optional notes about the review
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE media_files
            SET reviewed = 1, notes = ?
            WHERE id = ?
        ''', (notes, media_id))
        self.conn.commit()
    
    # New methods for Wayback-focused scraper
    
    def add_discovered_url(self, original_url: str, archive_url: str, 
                          archive_timestamp: str, search_phrase: str,
                          content_hash: Optional[str] = None,
                          metadata: Optional[Dict] = None) -> int:
        """Add a discovered URL from Wayback search.
        
        Args:
            original_url: Original URL before archiving
            archive_url: Wayback Machine URL
            archive_timestamp: Archive timestamp
            search_phrase: Search phrase that found this URL
            content_hash: Hash of content
            metadata: Additional metadata
            
        Returns:
            URL ID, or -1 if duplicate
        """
        cursor = self.conn.cursor()
        metadata_json = json.dumps(metadata) if metadata else None
        
        try:
            cursor.execute('''
                INSERT INTO discovered_urls 
                (original_url, archive_url, archive_timestamp, search_phrase, content_hash, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (original_url, archive_url, archive_timestamp, search_phrase, content_hash, metadata_json))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # URL already exists
            cursor.execute('SELECT id FROM discovered_urls WHERE archive_url = ?', (archive_url,))
            row = cursor.fetchone()
            return row['id'] if row else -1
    
    def add_media(self, url_id: int, media_url: str, media_type: str,
                  local_path: Optional[str] = None, file_hash: Optional[str] = None) -> int:
        """Add media found on a page.
        
        Args:
            url_id: Reference to discovered_urls
            media_url: URL of media
            media_type: Type (image/video/audio)
            local_path: Local download path
            file_hash: Hash of downloaded file
            
        Returns:
            Media ID
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO media (url_id, media_url, media_type, local_path, file_hash, downloaded_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (url_id, media_url, media_type, local_path, file_hash, 
              datetime.now().isoformat() if local_path else None))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_discovered_url_status(self, url_id: int, status: str, 
                                     content_hash: Optional[str] = None) -> None:
        """Update status of discovered URL.
        
        Args:
            url_id: URL ID
            status: New status (pending/fetched/analyzed/error)
            content_hash: Optional content hash
        """
        cursor = self.conn.cursor()
        if content_hash:
            cursor.execute('''
                UPDATE discovered_urls 
                SET status = ?, content_hash = ?
                WHERE id = ?
            ''', (status, content_hash, url_id))
        else:
            cursor.execute('''
                UPDATE discovered_urls 
                SET status = ?
                WHERE id = ?
            ''', (status, url_id))
        self.conn.commit()
    
    def get_search_progress(self, search_phrase: str, search_method: str) -> Optional[Dict[str, Any]]:
        """Get progress for a search.
        
        Args:
            search_phrase: Search phrase
            search_method: Search method
            
        Returns:
            Progress record or None
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM search_progress 
            WHERE search_phrase = ? AND search_method = ?
        ''', (search_phrase, search_method))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_search_progress(self, search_phrase: str, search_method: str,
                              last_offset: int = 0, last_timestamp: Optional[str] = None,
                              completed: bool = False) -> None:
        """Update or create search progress.
        
        Args:
            search_phrase: Search phrase
            search_method: Search method
            last_offset: Last processed offset
            last_timestamp: Last processed timestamp
            completed: Whether search is completed
        """
        cursor = self.conn.cursor()
        
        # Try to update existing record
        cursor.execute('''
            UPDATE search_progress 
            SET last_offset = ?, last_timestamp = ?, completed = ?, updated_at = CURRENT_TIMESTAMP
            WHERE search_phrase = ? AND search_method = ?
        ''', (last_offset, last_timestamp, 1 if completed else 0, search_phrase, search_method))
        
        # If no rows updated, insert new record
        if cursor.rowcount == 0:
            cursor.execute('''
                INSERT INTO search_progress 
                (search_phrase, search_method, last_offset, last_timestamp, completed)
                VALUES (?, ?, ?, ?, ?)
            ''', (search_phrase, search_method, last_offset, last_timestamp, 1 if completed else 0))
        
        self.conn.commit()
    
    def log_request(self, url: str, status_code: int, success: bool) -> None:
        """Log an HTTP request for rate limiting analysis.
        
        Args:
            url: Request URL
            status_code: HTTP status code
            success: Whether request succeeded
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO request_log (url, status_code, success)
            VALUES (?, ?, ?)
        ''', (url, status_code, 1 if success else 0))
        self.conn.commit()
    
    def get_recent_requests(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get recent requests for rate limiting.
        
        Args:
            minutes: Time window in minutes
            
        Returns:
            List of recent requests
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM request_log 
            WHERE timestamp >= datetime('now', '-' || ? || ' minutes')
            ORDER BY timestamp DESC
        ''', (minutes,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_pending_discovered_urls(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get pending discovered URLs to fetch.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of pending URLs
        """
        cursor = self.conn.cursor()
        query = 'SELECT * FROM discovered_urls WHERE status = "pending"'
        if limit:
            query += f' LIMIT {limit}'
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_discovered_urls_for_analysis(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get fetched URLs that need content analysis.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of URLs to analyze
        """
        cursor = self.conn.cursor()
        query = 'SELECT * FROM discovered_urls WHERE status = "fetched"'
        if limit:
            query += f' LIMIT {limit}'
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_wayback_statistics(self) -> Dict[str, Any]:
        """Get Wayback scraper statistics.
        
        Returns:
            Dictionary with statistics
        """
        cursor = self.conn.cursor()
        stats = {}
        
        # Discovered URLs by status
        cursor.execute('SELECT status, COUNT(*) as count FROM discovered_urls GROUP BY status')
        stats['discovered_urls_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Discovered URLs by phrase
        cursor.execute('SELECT search_phrase, COUNT(*) as count FROM discovered_urls GROUP BY search_phrase')
        stats['discovered_urls_by_phrase'] = {row['search_phrase']: row['count'] for row in cursor.fetchall()}
        
        # Media by type
        cursor.execute('SELECT media_type, COUNT(*) as count FROM media GROUP BY media_type')
        stats['media_by_type'] = {row['media_type']: row['count'] for row in cursor.fetchall()}
        
        # Search progress
        cursor.execute('SELECT * FROM search_progress ORDER BY updated_at DESC')
        stats['search_progress'] = [dict(row) for row in cursor.fetchall()]
        
        # Request statistics (last hour)
        cursor.execute('''
            SELECT 
                COUNT(*) as total_requests,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_requests
            FROM request_log 
            WHERE timestamp >= datetime('now', '-1 hour')
        ''')
        row = cursor.fetchone()
        if row:
            stats['requests_last_hour'] = dict(row)
        
        return stats
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
