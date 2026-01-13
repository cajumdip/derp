"""Wayback Machine scraper for archived content."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import urllib.parse
from .base import BaseScraper


logger = logging.getLogger(__name__)


class WaybackScraper(BaseScraper):
    """Scraper for Wayback Machine archives."""
    
    def __init__(self, *args, **kwargs):
        """Initialize Wayback scraper."""
        super().__init__(*args, **kwargs)
        self.cdx_url = self.config.get('wayback', 'cdx_url', 
                                       default='https://web.archive.org/cdx/search/cdx')
        self.rate_limit = self.config.get('wayback', 'rate_limit', default=30)
    
    async def search_cdx(self, url: str, from_date: Optional[str] = None, 
                        to_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search CDX API for archived snapshots.
        
        Args:
            url: URL or URL pattern to search
            from_date: Start date (YYYYMMDD format)
            to_date: End date (YYYYMMDD format)
            
        Returns:
            List of archived snapshots
        """
        params = {
            'url': url,
            'output': 'json',
            'collapse': 'digest',  # Collapse duplicates
            'filter': 'statuscode:200'  # Only successful captures
        }
        
        if from_date:
            params['from'] = from_date.replace('-', '')
        if to_date:
            params['to'] = to_date.replace('-', '')
        
        # Build query URL
        query_url = f"{self.cdx_url}?{urllib.parse.urlencode(params)}"
        
        self.logger.debug(f"Querying CDX: {query_url}")
        
        try:
            json_data = await self.http.get_json(query_url)
            
            if not json_data or len(json_data) < 2:
                return []
            
            # First row is headers
            headers = json_data[0]
            results = []
            
            for row in json_data[1:]:
                record = dict(zip(headers, row))
                results.append({
                    'url': record.get('original', ''),
                    'timestamp': record.get('timestamp', ''),
                    'archive_url': f"https://web.archive.org/web/{record.get('timestamp')}/{record.get('original')}",
                    'mimetype': record.get('mimetype', ''),
                    'statuscode': record.get('statuscode', ''),
                    'digest': record.get('digest', '')
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"CDX search failed for {url}: {e}")
            return []
    
    async def search(self, search_terms: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Search Wayback Machine for archived pages matching search terms.
        
        Args:
            search_terms: List of search terms
            **kwargs: Additional parameters
            
        Returns:
            List of discovered URLs
        """
        from_date = self.config.get('search', 'date_range', 'start', default='2004-01-01')
        to_date = self.config.get('search', 'date_range', 'end', default='2011-12-31')
        
        # Known platform URLs to check
        platform_urls = [
            'myspace.com/cojumdip',
            'soundcloud.com/cojumdip',
            'facebook.com/cojumdip',
            'purevolume.com/cojumdip',
            'last.fm/music/Cojum+Dip',
            'youtube.com/cojumdip'
        ]
        
        all_results = []
        
        # Search archived versions of known URLs
        for base_url in platform_urls:
            self.logger.info(f"Searching archived snapshots of {base_url}")
            
            snapshots = await self.search_cdx(
                url=base_url,
                from_date=from_date,
                to_date=to_date
            )
            
            for snapshot in snapshots:
                all_results.append({
                    'url': snapshot['archive_url'],
                    'content_type': 'archived_page',
                    'archive_date': self._parse_timestamp(snapshot['timestamp']),
                    'metadata': {
                        'original_url': snapshot['url'],
                        'mimetype': snapshot['mimetype'],
                        'digest': snapshot['digest']
                    }
                })
        
        self.logger.info(f"Found {len(all_results)} archived snapshots")
        return all_results
    
    async def scrape_url(self, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Scrape an archived URL.
        
        Args:
            url: Archive URL to scrape
            **kwargs: Additional parameters
            
        Returns:
            Scraped content
        """
        try:
            html_content = await self.http.get_text(url)
            
            if not html_content:
                return None
            
            return {
                'url': url,
                'content': html_content,
                'content_length': len(html_content)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to scrape {url}: {e}")
            return None
    
    def _parse_timestamp(self, timestamp: str) -> str:
        """Parse Wayback timestamp to ISO format.
        
        Args:
            timestamp: Timestamp in YYYYMMDDHHMMSS format
            
        Returns:
            ISO formatted date string
        """
        try:
            dt = datetime.strptime(timestamp, '%Y%m%d%H%M%S')
            return dt.isoformat()
        except:
            return timestamp
