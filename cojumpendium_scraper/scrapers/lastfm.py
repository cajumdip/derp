"""Last.fm scraper."""

from typing import List, Dict, Any, Optional
from .base import BaseScraper


class LastfmScraper(BaseScraper):
    """Scraper for Last.fm content."""
    
    async def search(self, search_terms: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Search Last.fm.
        
        Args:
            search_terms: List of search terms
            **kwargs: Additional parameters
            
        Returns:
            List of discovered URLs
        """
        return [{
            'url': 'https://www.last.fm/music/Cojum+Dip',
            'content_type': 'lastfm_artist',
            'metadata': {'artist': 'Cojum Dip'}
        }]
    
    async def scrape_url(self, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Scrape Last.fm URL.
        
        Args:
            url: URL to scrape
            **kwargs: Additional parameters
            
        Returns:
            Scraped data
        """
        return {'url': url}
