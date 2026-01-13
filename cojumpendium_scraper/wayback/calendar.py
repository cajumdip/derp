"""Calendar Captures API scraper for Wayback Machine."""

import logging
import urllib.parse
from typing import List, Dict, Any, Optional
import asyncio
import aiohttp


logger = logging.getLogger(__name__)


class CalendarScraper:
    """Scraper using Wayback Machine's undocumented Calendar Captures API."""
    
    def __init__(self, config, database, http_client, rate_limiter):
        """Initialize calendar scraper.
        
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
        self.calendar_url = config.get('wayback', 'calendar', 'url',
                                       default='https://web.archive.org/__wb/calendarcaptures/2')
    
    async def search(self, phrase: str, resume: bool = False) -> int:
        """Search using Calendar API for known sites.
        
        This searches for archived snapshots of known sites that might
        contain the phrase.
        
        Args:
            phrase: Search phrase (used to determine which sites to check)
            resume: Whether to resume from previous progress
            
        Returns:
            Number of URLs discovered
        """
        logger.info(f"Calendar search for phrase: {phrase}")
        
        # Check for existing progress
        progress = self.db.get_search_progress(phrase, 'calendar')
        if progress and progress['completed'] and not resume:
            logger.info(f"Calendar search for '{phrase}' already completed")
            return 0
        
        # Get configured sites to check
        sites = self.config.get('wayback', 'calendar', 'sites', default=[
            "http://myspace.com/cojumdip",
            "http://purevolume.com/cojumdip",
            "http://soundcloud.com/cojumdip",
            "http://facebook.com/cojumdip",
            "http://youtube.com/cojumdip",
            "http://last.fm/music/Cojum+Dip"
        ])
        
        # Add phrase-specific sites
        phrase_lower = phrase.lower().replace(' ', '')
        if 'bkaraca' in phrase_lower or 'bora' in phrase_lower:
            sites.extend([
                f"http://myspace.com/{phrase_lower}",
                f"http://facebook.com/{phrase_lower}"
            ])
        
        total_discovered = 0
        
        # Get date range
        start_year = int(self.config.get('search', 'date_range', 'start', default='2004'))
        end_year = int(self.config.get('search', 'date_range', 'end', default='2012'))
        
        # Search each site
        for site in sites:
            logger.info(f"Calendar search for site: {site}")
            
            for year in range(start_year, end_year + 1):
                discovered = await self._search_site_year(phrase, site, year)
                total_discovered += discovered
        
        # Mark as completed
        self.db.update_search_progress(phrase, 'calendar', completed=True)
        
        logger.info(f"Calendar search for '{phrase}' complete: {total_discovered} URLs discovered")
        return total_discovered
    
    async def _search_site_year(self, phrase: str, site: str, year: int) -> int:
        """Search calendar captures for a specific site and year.
        
        Args:
            phrase: Search phrase
            site: Site URL to search
            year: Year to search
            
        Returns:
            Number of URLs discovered
        """
        safe_site = urllib.parse.quote_plus(site)
        url = f"{self.calendar_url}?url={safe_site}&date={year}&groupby=day"
        
        try:
            # Apply rate limiting
            await self.rate_limiter.wait()
            
            # Request year calendar
            logger.debug(f"Calendar request: {url}")
            data = await self.http.get_json(url)
            
            # Log success
            self.rate_limiter.on_success()
            self.db.log_request(url, 200, True)
            
            if not data or 'items' not in data:
                logger.debug(f"No calendar data for {site} in {year}")
                return 0
            
            items = data.get('items', [])
            logger.info(f"Found {len(items)} capture days for {site} in {year}")
            
            discovered = 0
            
            # Process each day with captures
            for item in items:
                # item[0] is day data: [YYYYMMDD, count]
                if not item or len(item) < 1:
                    continue
                
                day_data = item[0]
                if isinstance(day_data, list) and len(day_data) >= 1:
                    date_str = str(day_data[0])
                    
                    # Get specific captures for this day
                    day_discovered = await self._search_day_captures(
                        phrase, site, date_str
                    )
                    discovered += day_discovered
            
            return discovered
            
        except aiohttp.ClientError as e:
            logger.error(f"Calendar request failed for {site} {year}: {e}")
            status_code = getattr(e, 'status', 500)
            self.rate_limiter.on_error(status_code)
            self.db.log_request(url, status_code, False)
            return 0
        except Exception as e:
            logger.error(f"Unexpected error in calendar search: {e}")
            self.db.log_request(url, 500, False)
            return 0
    
    async def _search_day_captures(self, phrase: str, site: str, date: str) -> int:
        """Get specific time captures for a day.
        
        Args:
            phrase: Search phrase
            site: Site URL
            date: Date string (YYYYMMDD)
            
        Returns:
            Number of URLs discovered
        """
        safe_site = urllib.parse.quote_plus(site)
        url = f"{self.calendar_url}?url={safe_site}&date={date}"
        
        try:
            # Apply rate limiting
            await self.rate_limiter.wait()
            
            # Request day captures
            logger.debug(f"Day captures request: {url}")
            data = await self.http.get_json(url)
            
            # Log success
            self.rate_limiter.on_success()
            self.db.log_request(url, 200, True)
            
            if not data or 'items' not in data:
                return 0
            
            items = data.get('items', [])
            discovered = 0
            
            # Process each time capture
            for item in items:
                # item[0] is timestamp (HHMMSS)
                # item[1] is status
                if not item or len(item) < 2:
                    continue
                
                time_str = str(item[0]).zfill(6)
                timestamp = f"{date}{time_str}"
                archive_url = f"https://web.archive.org/web/{timestamp}/{site}"
                
                # Save to database
                url_id = self.db.add_discovered_url(
                    original_url=site,
                    archive_url=archive_url,
                    archive_timestamp=timestamp,
                    search_phrase=phrase,
                    metadata={
                        'search_method': 'calendar',
                        'date': date,
                        'time': time_str
                    }
                )
                
                if url_id > 0:
                    discovered += 1
            
            if discovered > 0:
                logger.debug(f"Day {date}: {discovered} captures")
            
            return discovered
            
        except aiohttp.ClientError as e:
            logger.debug(f"Day captures request failed for {date}: {e}")
            status_code = getattr(e, 'status', 500)
            self.rate_limiter.on_error(status_code)
            self.db.log_request(url, status_code, False)
            return 0
        except Exception as e:
            logger.debug(f"Error getting day captures: {e}")
            return 0
