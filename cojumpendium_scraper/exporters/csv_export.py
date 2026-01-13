"""CSV exporter for database content."""

import csv
from pathlib import Path
from typing import Optional
from ..database import Database


class CSVExporter:
    """Export database content to CSV format."""
    
    def __init__(self, database: Database, output_dir: str = './exports'):
        """Initialize CSV exporter.
        
        Args:
            database: Database instance
            output_dir: Output directory for exports
        """
        self.db = database
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_urls(self, filename: Optional[str] = None) -> str:
        """Export URLs to CSV.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        if not filename:
            filename = 'urls.csv'
        
        output_path = self.output_dir / filename
        
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM urls')
        
        rows = cursor.fetchall()
        if rows:
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(rows[0].keys())
                # Write data
                for row in rows:
                    writer.writerow(row)
        
        return str(output_path)
    
    def export_media(self, filename: Optional[str] = None) -> str:
        """Export media files to CSV.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        if not filename:
            filename = 'media_files.csv'
        
        output_path = self.output_dir / filename
        
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM media_files')
        
        rows = cursor.fetchall()
        if rows:
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(rows[0].keys())
                for row in rows:
                    writer.writerow(row)
        
        return str(output_path)
    
    def export_all(self) -> dict:
        """Export all tables to CSV.
        
        Returns:
            Dictionary of exported file paths
        """
        return {
            'urls': self.export_urls(),
            'media': self.export_media()
        }
