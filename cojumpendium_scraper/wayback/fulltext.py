"""Full-text search scraper for Wayback Machine search results."""

import logging
import urllib.parse
from typing import List, Dict, Any, Optional
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re


logger = logging.getLogger(__name__)


class FullTextScraper:
    """Scraper that parses Wayback Machine's full-text search results pages."""
    
    def __init__(self, config, database, http_client, rate_limiter):
        """Initialize full-text scraper.
        
        Args:
            config: Configuration object
            database: Database instance
            http_client: Async HTTP client
            rate_limiter: Rate limiter instance
        """
        self.config = config
        self.db = database
        self.http = http_client
        self.rate_limiter = rate_limiter
        self.base_url = config.get('wayback', 'fulltext', 'base_url',
                                   default='https://web.archive.org/web/*/')
        self.max_pages = config.get('wayback', 'fulltext', 'max_pages', default=50)
    
    async def search(self, phrase: str, resume: bool = False) -> int:
        """Search Wayback full-text search for phrase.
        
        Args:
            phrase: Search phrase
            resume: Whether to resume from previous progress
            
        Returns:
            Number of URLs discovered
        """
        logger.info(f"Full-text search for phrase: {phrase}")
        
        # Check for existing progress
        progress = self.db.get_search_progress(phrase, 'fulltext')
        if progress and progress['completed'] and not resume:
            logger.info(f"Full-text search for '{phrase}' already completed")
            return 0
        
        start_page = 0
        if progress and resume:
            start_page = progress.get('last_offset', 0)
            logger.info(f"Resuming full-text search from page {start_page}")
        
        total_discovered = 0
        
        # Search with phrase
        search_url = f"{self.base_url}{urllib.parse.quote(phrase)}"
        
        for page in range(start_page, self.max_pages):
            logger.info(f"Fetching full-text search results page {page + 1}/{self.max_pages}")
            
            discovered = await self._search_page(phrase, search_url, page)
            total_discovered += discovered
            
            # Update progress
            self.db.update_search_progress(phrase, 'fulltext', last_offset=page + 1)
            
            # If no results on this page, we're done
            if discovered == 0:
                logger.info(f"No more results found on page {page + 1}, search complete")
                break
        
        # Mark as completed
        self.db.update_search_progress(phrase, 'fulltext', completed=True)
        
        logger.info(f"Full-text search for '{phrase}' complete: {total_discovered} URLs discovered")
        return total_discovered
    
    async def _search_page(self, phrase: str, search_url: str, page: int) -> int:
        """Scrape a single page of search results.
        
        Args:
            phrase: Search phrase
            search_url: Base search URL
            page: Page number (0-indexed)
            
        Returns:
            Number of URLs discovered on this page
        """
        # Wayback search uses page parameter
        url = search_url if page == 0 else f"{search_url}&page={page}"
        
        try:
            # Apply rate limiting
            await self.rate_limiter.wait()
            
            # Fetch search results page
            logger.debug(f"Full-text request: {url}")
            html = await self.http.get_text(url)
            
            # Log success
            self.rate_limiter.on_success()
            self.db.log_request(url, 200, True)
            
            if not html:
                logger.warning(f"No HTML content from {url}")
                return 0
            
            # Parse HTML
            soup = BeautifulSoup(html, 'lxml')
            
            # Find search result links
            # Wayback search results are typically in <div class="result">
            # with <a> tags pointing to archived pages
            discovered = 0
            
            # Look for links to archived pages (format: /web/TIMESTAMP/URL)
            archive_pattern = re.compile(r'/web/(\d{14})/(.+)')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                match = archive_pattern.search(href)
                if match:
                    timestamp = match.group(1)
                    original_url = match.group(2)
                    
                    # Build full archive URL
                    if href.startswith('http'):
                        archive_url = href
                    else:
                        archive_url = f"https://web.archive.org{href}"
                    
                    # Save to database
                    url_id = self.db.add_discovered_url(
                        original_url=original_url,
                        archive_url=archive_url,
                        archive_timestamp=timestamp,
                        search_phrase=phrase,
                        metadata={
                            'search_method': 'fulltext',
                            'page': page,
                            'link_text': link.get_text(strip=True)[:200]
                        }
                    )
                    
                    if url_id > 0:
                        discovered += 1
            
            logger.info(f"Page {page + 1}: {discovered} new URLs")
            return discovered
            
        except aiohttp.ClientError as e:
            logger.error(f"Full-text request failed for page {page}: {e}")
            status_code = getattr(e, 'status', 500)
            self.rate_limiter.on_error(status_code)
            self.db.log_request(url, status_code, False)
            return 0
        except Exception as e:
            logger.error(f"Unexpected error in full-text search page {page}: {e}")
            self.db.log_request(url, 500, False)
            return 0
