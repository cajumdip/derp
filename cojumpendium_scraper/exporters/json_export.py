"""JSON exporter for database content."""

import json
from pathlib import Path
from typing import Optional
from ..database import Database


class JSONExporter:
    """Export database content to JSON format."""
    
    def __init__(self, database: Database, output_dir: str = './exports'):
        """Initialize JSON exporter.
        
        Args:
            database: Database instance
            output_dir: Output directory for exports
        """
        self.db = database
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(self, filename: Optional[str] = None) -> str:
        """Export all data to JSON.
        
        Args:
            filename: Output filename (default: cojumpendium_export.json)
            
        Returns:
            Path to exported file
        """
        if not filename:
            filename = 'cojumpendium_export.json'
        
        output_path = self.output_dir / filename
        
        # Get all data from database
        cursor = self.db.conn.cursor()
        
        data = {
            'urls': [],
            'media_files': [],
            'statistics': self.db.get_statistics()
        }
        
        # Export URLs
        cursor.execute('SELECT * FROM urls')
        for row in cursor.fetchall():
            data['urls'].append(dict(row))
        
        # Export media files
        cursor.execute('SELECT * FROM media_files')
        for row in cursor.fetchall():
            data['media_files'].append(dict(row))
        
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return str(output_path)
