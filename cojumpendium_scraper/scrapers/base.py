"""Base scraper class for all platform scrapers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
from ..database import Database
from ..config import Config
from ..utils.http import HTTPClient


logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for platform scrapers."""
    
    def __init__(self, config: Config, database: Database, http_client: HTTPClient):
        """Initialize scraper.
        
        Args:
            config: Configuration object
            database: Database instance
            http_client: HTTP client for requests
        """
        self.config = config
        self.db = database
        self.http = http_client
        self.platform_name = self.__class__.__name__.replace('Scraper', '').lower()
        self.logger = logging.getLogger(f"{__name__}.{self.platform_name}")
    
    @abstractmethod
    async def search(self, search_terms: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Search for content on the platform.
        
        Args:
            search_terms: List of search terms
            **kwargs: Additional platform-specific parameters
            
        Returns:
            List of discovered URLs with metadata
        """
        pass
    
    @abstractmethod
    async def scrape_url(self, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Scrape a specific URL.
        
        Args:
            url: URL to scrape
            **kwargs: Additional parameters
            
        Returns:
            Scraped data or None
        """
        pass
    
    def save_url(self, url: str, content_type: Optional[str] = None, 
                 archive_date: Optional[str] = None, metadata: Optional[Dict] = None) -> int:
        """Save discovered URL to database.
        
        Args:
            url: URL to save
            content_type: Type of content
            archive_date: Archive date if applicable
            metadata: Additional metadata
            
        Returns:
            URL ID
        """
        return self.db.add_url(
            url=url,
            source_platform=self.platform_name,
            archive_date=archive_date,
            content_type=content_type,
            metadata=metadata
        )
    
    async def run(self, search_terms: Optional[List[str]] = None, 
                  urls: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run the scraper.
        
        Args:
            search_terms: Terms to search for
            urls: Specific URLs to scrape
            
        Returns:
            Summary of scraping results
        """
        results = {
            'platform': self.platform_name,
            'urls_found': 0,
            'urls_scraped': 0,
            'errors': 0
        }
        
        # Search phase
        if search_terms:
            self.logger.info(f"Searching {self.platform_name} for {len(search_terms)} terms")
            try:
                found_urls = await self.search(search_terms)
                results['urls_found'] = len(found_urls)
                
                # Save discovered URLs
                for url_data in found_urls:
                    self.save_url(
                        url=url_data['url'],
                        content_type=url_data.get('content_type'),
                        archive_date=url_data.get('archive_date'),
                        metadata=url_data.get('metadata')
                    )
            except Exception as e:
                self.logger.error(f"Search failed: {e}")
                results['errors'] += 1
        
        # Scrape phase
        if urls:
            self.logger.info(f"Scraping {len(urls)} URLs from {self.platform_name}")
            for url in urls:
                try:
                    data = await self.scrape_url(url)
                    if data:
                        results['urls_scraped'] += 1
                except Exception as e:
                    self.logger.error(f"Failed to scrape {url}: {e}")
                    results['errors'] += 1
        
        return results
