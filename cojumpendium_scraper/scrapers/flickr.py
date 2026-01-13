"""Flickr scraper."""

from typing import List, Dict, Any, Optional
from .base import BaseScraper


class FlickrScraper(BaseScraper):
    """Scraper for Flickr content."""
    
    async def search(self, search_terms: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Search Flickr.
        
        Args:
            search_terms: List of search terms
            **kwargs: Additional parameters
            
        Returns:
            List of discovered URLs
        """
        results = []
        
        for term in search_terms:
            results.append({
                'url': f'https://www.flickr.com/search/?text={term}',
                'content_type': 'flickr_search',
                'metadata': {'search_term': term}
            })
        
        return results
    
    async def scrape_url(self, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Scrape Flickr URL.
        
        Args:
            url: URL to scrape
            **kwargs: Additional parameters
            
        Returns:
            Scraped data
        """
        return {'url': url}
