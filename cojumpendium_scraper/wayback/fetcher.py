"""Page fetcher for downloading and analyzing archived pages."""

import logging
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path
import asyncio
import aiohttp
from ..extractors.content import ContentAnalyzer


logger = logging.getLogger(__name__)


class PageFetcher:
    """Fetches and analyzes archived pages."""
    
    def __init__(self, config, database, http_client, rate_limiter):
        """Initialize page fetcher.
        
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
        self.content_analyzer = ContentAnalyzer(config)
        
        # Get pages directory
        self.pages_dir = Path(config.get('storage', 'pages', default='./pages'))
        self.pages_dir.mkdir(parents=True, exist_ok=True)
    
    async def fetch_pending_urls(self, limit: int = 100) -> Dict[str, int]:
        """Fetch and analyze pending URLs.
        
        Args:
            limit: Maximum number of URLs to fetch
            
        Returns:
            Dictionary with statistics
        """
        logger.info(f"Fetching up to {limit} pending URLs")
        
        # Get pending URLs
        pending_urls = self.db.get_pending_discovered_urls(limit=limit)
        
        if not pending_urls:
            logger.info("No pending URLs to fetch")
            return {
                'fetched': 0,
                'analyzed': 0,
                'errors': 0
            }
        
        logger.info(f"Found {len(pending_urls)} pending URLs")
        
        stats = {
            'fetched': 0,
            'analyzed': 0,
            'errors': 0
        }
        
        for url_record in pending_urls:
            success = await self.fetch_url(url_record)
            
            if success:
                stats['fetched'] += 1
                stats['analyzed'] += 1
            else:
                stats['errors'] += 1
        
        logger.info(
            f"Fetch complete: {stats['fetched']} fetched, "
            f"{stats['analyzed']} analyzed, {stats['errors']} errors"
        )
        
        return stats
    
    async def fetch_url(self, url_record: Dict[str, Any]) -> bool:
        """Fetch and analyze a single URL.
        
        Args:
            url_record: URL record from database
            
        Returns:
            True if successful
        """
        url_id = url_record['id']
        archive_url = url_record['archive_url']
        
        logger.debug(f"Fetching {archive_url}")
        
        try:
            # Apply rate limiting
            await self.rate_limiter.wait()
            
            # Fetch page
            html = await self.http.get_text(archive_url)
            
            # Log success
            self.rate_limiter.on_success()
            self.db.log_request(archive_url, 200, True)
            
            if not html:
                logger.warning(f"No content from {archive_url}")
                self.db.update_discovered_url_status(url_id, 'error')
                return False
            
            # Calculate content hash
            content_hash = hashlib.sha256(html.encode()).hexdigest()
            
            # Save HTML to file
            html_path = self.pages_dir / f"{content_hash}.html"
            html_path.write_text(html, encoding='utf-8', errors='replace')
            
            # Update status to fetched
            self.db.update_discovered_url_status(url_id, 'fetched', content_hash)
            
            # Analyze content
            analysis = self.content_analyzer.analyze(html, archive_url)
            
            # If phrases found or has media, save media references
            if analysis['phrases_found'] or analysis['has_media']:
                logger.info(
                    f"Found content in {archive_url}: "
                    f"phrases={analysis['phrases_found']}, "
                    f"media_count={len(analysis['media_urls'])}"
                )
                
                # Save media URLs
                for media in analysis['media_urls']:
                    self.db.add_media(
                        url_id=url_id,
                        media_url=media['url'],
                        media_type=media['type']
                    )
                
                # Update status to analyzed
                self.db.update_discovered_url_status(url_id, 'analyzed', content_hash)
            else:
                # No relevant content found
                self.db.update_discovered_url_status(url_id, 'analyzed', content_hash)
            
            return True
            
        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch {archive_url}: {e}")
            status_code = getattr(e, 'status', 500)
            self.rate_limiter.on_error(status_code)
            self.db.log_request(archive_url, status_code, False)
            self.db.update_discovered_url_status(url_id, 'error')
            return False
        except Exception as e:
            logger.error(f"Unexpected error fetching {archive_url}: {e}")
            self.db.log_request(archive_url, 500, False)
            self.db.update_discovered_url_status(url_id, 'error')
            return False
