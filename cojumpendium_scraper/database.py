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
        
        # URLs table - tracks all discovered URLs
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
        
        # Media files table - tracks downloaded media
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
        
        # Search results table - tracks search queries
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
