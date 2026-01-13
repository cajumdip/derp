"""Archive.org general search API scraper."""

import logging
import urllib.parse
from typing import List, Dict, Any, Optional
import asyncio
import aiohttp


logger = logging.getLogger(__name__)


class ArchiveSearchScraper:
    """Scraper for Archive.org's general search API (uploaded content)."""
    
    def __init__(self, config, database, http_client, rate_limiter):
        """Initialize Archive.org search scraper.
        
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
        self.search_url = config.get('wayback', 'archive_search', 'url',
                                     default='https://archive.org/advancedsearch.php')
        self.rows = config.get('wayback', 'archive_search', 'rows', default=100)
        self.fields = config.get('wayback', 'archive_search', 'fields',
                                 default=['identifier', 'title', 'description', 'creator', 'date'])
    
    async def search(self, phrase: str, resume: bool = False) -> int:
        """Search Archive.org for uploaded content matching phrase.
        
        Args:
            phrase: Search phrase
            resume: Whether to resume from previous progress
            
        Returns:
            Number of items discovered
        """
        logger.info(f"Archive.org search for phrase: {phrase}")
        
        # Check for existing progress
        progress = self.db.get_search_progress(phrase, 'archive_search')
        if progress and progress['completed'] and not resume:
            logger.info(f"Archive.org search for '{phrase}' already completed")
            return 0
        
        start_page = 0
        if progress and resume:
            start_page = progress.get('last_offset', 0)
            logger.info(f"Resuming Archive.org search from page {start_page}")
        
        total_discovered = 0
        page = start_page
        
        while True:
            logger.info(f"Fetching Archive.org search results page {page + 1}")
            
            discovered, has_more = await self._search_page(phrase, page)
            total_discovered += discovered
            
            # Update progress
            self.db.update_search_progress(phrase, 'archive_search', last_offset=page + 1)
            
            # Check if we should continue
            if not has_more or discovered == 0:
                logger.info(f"No more results on page {page + 1}, search complete")
                break
            
            page += 1
        
        # Mark as completed
        self.db.update_search_progress(phrase, 'archive_search', completed=True)
        
        logger.info(f"Archive.org search for '{phrase}' complete: {total_discovered} items discovered")
        return total_discovered
    
    async def _search_page(self, phrase: str, page: int) -> tuple:
        """Search a single page of Archive.org results.
        
        Args:
            phrase: Search phrase
            page: Page number (0-indexed)
            
        Returns:
            Tuple of (discovered count, has_more_pages)
        """
        # Build query
        # Search in title, description, and creator fields
        query = f'({phrase}) OR title:({phrase}) OR creator:({phrase})'
        
        params = {
            'q': query,
            'fl[]': self.fields,
            'rows': self.rows,
            'page': page + 1,  # Archive.org uses 1-indexed pages
            'output': 'json'
        }
        
        url = f"{self.search_url}?{urllib.parse.urlencode(params, doseq=True)}"
        
        try:
            # Apply rate limiting
            await self.rate_limiter.wait()
            
            # Make request
            logger.debug(f"Archive.org request: {url}")
            data = await self.http.get_json(url)
            
            # Log success
            self.rate_limiter.on_success()
            self.db.log_request(url, 200, True)
            
            if not data or 'response' not in data:
                logger.warning(f"Invalid response from Archive.org search")
                return 0, False
            
            response = data['response']
            docs = response.get('docs', [])
            num_found = response.get('numFound', 0)
            
            logger.info(f"Page {page + 1}: {len(docs)} results (total available: {num_found})")
            
            discovered = 0
            
            # Process each result
            for doc in docs:
                identifier = doc.get('identifier', '')
                if not identifier:
                    continue
                
                # Build Archive.org item URL
                item_url = f"https://archive.org/details/{identifier}"
                
                # Save to database
                url_id = self.db.add_discovered_url(
                    original_url=item_url,
                    archive_url=item_url,
                    archive_timestamp=doc.get('date', ''),
                    search_phrase=phrase,
                    metadata={
                        'search_method': 'archive_search',
                        'title': doc.get('title', ''),
                        'description': doc.get('description', ''),
                        'creator': doc.get('creator', ''),
                        'mediatype': doc.get('mediatype', ''),
                        'page': page
                    }
                )
                
                if url_id > 0:
                    discovered += 1
            
            # Check if there are more pages
            has_more = (page + 1) * self.rows < num_found
            
            return discovered, has_more
            
        except aiohttp.ClientError as e:
            logger.error(f"Archive.org request failed for page {page}: {e}")
            status_code = getattr(e, 'status', 500)
            self.rate_limiter.on_error(status_code)
            self.db.log_request(url, status_code, False)
            return 0, False
        except Exception as e:
            logger.error(f"Unexpected error in Archive.org search page {page}: {e}")
            self.db.log_request(url, 500, False)
            return 0, False
