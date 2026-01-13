"""CDX Server API scraper for Wayback Machine."""

import logging
import urllib.parse
from typing import List, Dict, Any, Optional
import asyncio
import aiohttp


logger = logging.getLogger(__name__)


class CDXScraper:
    """Scraper using Wayback Machine's CDX Server API with wildcard matching."""
    
    def __init__(self, config, database, http_client, rate_limiter):
        """Initialize CDX scraper.
        
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
        self.cdx_url = config.get('wayback', 'cdx', 'url', 
                                  default='https://web.archive.org/cdx/search/cdx')
        self.match_type = config.get('wayback', 'cdx', 'match_type', default='domain')
    
    async def search(self, phrase: str, resume: bool = False) -> int:
        """Search CDX API for archived URLs containing phrase.
        
        Args:
            phrase: Search phrase
            resume: Whether to resume from previous progress
            
        Returns:
            Number of URLs discovered
        """
        logger.info(f"CDX search for phrase: {phrase}")
        
        # Check for existing progress
        progress = self.db.get_search_progress(phrase, 'cdx')
        if progress and progress['completed'] and not resume:
            logger.info(f"CDX search for '{phrase}' already completed")
            return 0
        
        total_discovered = 0
        
        # First, search URL patterns if configured
        url_patterns = self.config.get('search', 'url_patterns', default=[])
        if url_patterns:
            logger.info(f"Searching {len(url_patterns)} URL patterns")
            for url_pattern in url_patterns:
                discovered = await self._search_url_pattern(phrase, url_pattern)
                total_discovered += discovered
        
        # Then, search wildcard patterns based on phrase
        search_patterns = [
            f"*{phrase.replace(' ', '')}*",  # No spaces
            f"*{phrase.replace(' ', '-')}*",  # Dashes
            f"*{phrase.replace(' ', '_')}*",  # Underscores
        ]
        
        for pattern in search_patterns:
            logger.info(f"Searching CDX with pattern: {pattern}")
            discovered = await self._search_pattern(phrase, pattern)
            total_discovered += discovered
        
        # Mark as completed
        self.db.update_search_progress(phrase, 'cdx', completed=True)
        
        logger.info(f"CDX search for '{phrase}' complete: {total_discovered} URLs discovered")
        return total_discovered
    
    async def _search_pattern(self, phrase: str, url_pattern: str) -> int:
        """Search a specific URL pattern.
        
        Args:
            phrase: Original search phrase
            url_pattern: URL pattern with wildcards
            
        Returns:
            Number of URLs discovered
        """
        params = {
            'url': url_pattern,
            'output': 'json',
            'collapse': 'digest',  # Collapse duplicate content
            'filter': 'statuscode:200',  # Only successful captures
            'matchType': self.match_type
        }
        
        # Add date range - FILTER TO 2004-2011 ONLY
        start_year = self.config.get('search', 'date_range', 'start', default=2004)
        end_year = self.config.get('search', 'date_range', 'end', default=2011)
        
        # Convert to int if string
        if isinstance(start_year, str):
            start_year = int(start_year.split('-')[0])
        if isinstance(end_year, str):
            end_year = int(end_year.split('-')[0])
        
        params['from'] = f"{start_year}0101"
        params['to'] = f"{end_year}1231"
        
        query_url = f"{self.cdx_url}?{urllib.parse.urlencode(params)}"
        
        try:
            # Apply rate limiting
            await self.rate_limiter.wait()
            
            # Make request
            logger.debug(f"CDX request: {query_url}")
            json_data = await self.http.get_json(query_url)
            
            # Log success
            self.rate_limiter.on_success()
            self.db.log_request(query_url, 200, True)
            
            if not json_data or len(json_data) < 2:
                logger.debug(f"No results for pattern: {url_pattern}")
                return 0
            
            # First row is headers
            headers = json_data[0]
            discovered = 0
            
            # Process results
            for row in json_data[1:]:
                record = dict(zip(headers, row))
                
                original_url = record.get('original', '')
                timestamp = record.get('timestamp', '')
                
                # Filter out any results after 2011-12-31
                if timestamp and int(timestamp[:8]) > 20111231:
                    logger.debug(f"Skipping URL with timestamp {timestamp} (after 2011)")
                    continue
                
                archive_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
                
                # Save to database
                url_id = self.db.add_discovered_url(
                    original_url=original_url,
                    archive_url=archive_url,
                    archive_timestamp=timestamp,
                    search_phrase=phrase,
                    metadata={
                        'mimetype': record.get('mimetype', ''),
                        'statuscode': record.get('statuscode', ''),
                        'digest': record.get('digest', ''),
                        'search_method': 'cdx',
                        'url_pattern': url_pattern
                    }
                )
                
                if url_id > 0:
                    discovered += 1
            
            logger.info(f"Pattern '{url_pattern}': {discovered} new URLs")
            return discovered
            
        except aiohttp.ClientError as e:
            logger.error(f"CDX request failed: {e}")
            # Determine status code
            status_code = getattr(e, 'status', 500)
            self.rate_limiter.on_error(status_code)
            self.db.log_request(query_url, status_code, False)
            return 0
        except Exception as e:
            logger.error(f"Unexpected error in CDX search: {e}")
            self.db.log_request(query_url, 500, False)
            return 0
    
    async def _search_url_pattern(self, phrase: str, url_pattern: str) -> int:
        """Search for archived snapshots of a specific URL pattern.
        
        This is used for searching platform-specific URLs like myspace.com/cojumdip.
        
        Args:
            phrase: Original search phrase (for tracking)
            url_pattern: URL pattern to search (e.g., "myspace.com/cojumdip")
            
        Returns:
            Number of URLs discovered
        """
        # Use the same logic as _search_pattern but log differently
        logger.info(f"Searching URL pattern: {url_pattern}")
        return await self._search_pattern(phrase, url_pattern)
