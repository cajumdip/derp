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
        
        # Build wildcard URLs to search
        search_patterns = [
            f"*{phrase.replace(' ', '')}*",  # No spaces
            f"*{phrase.replace(' ', '-')}*",  # Dashes
            f"*{phrase.replace(' ', '_')}*",  # Underscores
        ]
        
        total_discovered = 0
        
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
        
        # Add date range if configured
        start_year = self.config.get('search', 'date_range', 'start', default='2004')
        end_year = self.config.get('search', 'date_range', 'end', default='2012')
        
        if start_year:
            params['from'] = f"{start_year}0101"
        if end_year:
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
