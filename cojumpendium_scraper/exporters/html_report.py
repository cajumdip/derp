"""HTML report generator."""

from pathlib import Path
from typing import Optional
from datetime import datetime
from ..database import Database


class HTMLReporter:
    """Generate HTML reports from database content."""
    
    def __init__(self, database: Database, output_dir: str = './exports'):
        """Initialize HTML reporter.
        
        Args:
            database: Database instance
            output_dir: Output directory for reports
        """
        self.db = database
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, filename: Optional[str] = None) -> str:
        """Generate HTML report.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to generated report
        """
        if not filename:
            filename = f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        
        output_path = self.output_dir / filename
        
        # Get statistics
        stats = self.db.get_statistics()
        
        # Generate HTML
        html = self._generate_html(stats)
        
        with open(output_path, 'w') as f:
            f.write(html)
        
        return str(output_path)
    
    def _generate_html(self, stats: dict) -> str:
        """Generate HTML content.
        
        Args:
            stats: Statistics dictionary
            
        Returns:
            HTML string
        """
        urls_by_status = stats.get('urls_by_status', {})
        media_by_type = stats.get('media_by_type', {})
        urls_by_platform = stats.get('urls_by_platform', {})
        total_storage = stats.get('total_storage_bytes', 0)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Cojumpendium Scraper Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .stat-box {{
            display: inline-block;
            margin: 15px;
            padding: 20px;
            background-color: #f9f9f9;
            border-left: 4px solid #4CAF50;
            min-width: 200px;
        }}
        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            color: #4CAF50;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Cojumpendium Lost Media Scraper Report</h1>
        <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <h2>Summary Statistics</h2>
        <div>
            <div class="stat-box">
                <div class="stat-number">{sum(urls_by_status.values())}</div>
                <div class="stat-label">Total URLs</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{sum(media_by_type.values())}</div>
                <div class="stat-label">Media Files</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{total_storage / (1024*1024):.2f} MB</div>
                <div class="stat-label">Storage Used</div>
            </div>
        </div>
        
        <h2>URLs by Status</h2>
        <table>
            <tr>
                <th>Status</th>
                <th>Count</th>
            </tr>
            {''.join(f'<tr><td>{status}</td><td>{count}</td></tr>' for status, count in urls_by_status.items())}
        </table>
        
        <h2>Media by Type</h2>
        <table>
            <tr>
                <th>Type</th>
                <th>Count</th>
            </tr>
            {''.join(f'<tr><td>{media_type}</td><td>{count}</td></tr>' for media_type, count in media_by_type.items())}
        </table>
        
        <h2>URLs by Platform</h2>
        <table>
            <tr>
                <th>Platform</th>
                <th>Count</th>
            </tr>
            {''.join(f'<tr><td>{platform}</td><td>{count}</td></tr>' for platform, count in urls_by_platform.items())}
        </table>
    </div>
</body>
</html>
"""
        return html
