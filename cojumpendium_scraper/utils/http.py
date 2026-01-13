"""HTTP utilities for async requests with rate limiting and retries."""

import asyncio
import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for HTTP requests."""
    
    def __init__(self, requests_per_minute: int = 30):
        """Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
        """
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request = None
    
    async def wait(self) -> None:
        """Wait if necessary to respect rate limit."""
        if self.last_request:
            elapsed = (datetime.now() - self.last_request).total_seconds()
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
        self.last_request = datetime.now()


class HTTPClient:
    """Async HTTP client with rate limiting and retry logic."""
    
    def __init__(self, user_agent: str, timeout: int = 30, 
                 max_retries: int = 3, rate_limiter: Optional[RateLimiter] = None):
        """Initialize HTTP client.
        
        Args:
            user_agent: User agent string
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            rate_limiter: Optional rate limiter
        """
        self.user_agent = user_agent
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.rate_limiter = rate_limiter
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers={'User-Agent': self.user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get(self, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """Perform GET request with retries.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for aiohttp
            
        Returns:
            Response object or None on failure
        """
        if not self.session:
            raise RuntimeError("HTTPClient must be used as async context manager")
        
        for attempt in range(self.max_retries):
            try:
                if self.rate_limiter:
                    await self.rate_limiter.wait()
                
                async with self.session.get(url, **kwargs) as response:
                    response.raise_for_status()
                    return response
                    
            except aiohttp.ClientError as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                return None
        
        return None
    
    async def get_text(self, url: str, **kwargs) -> Optional[str]:
        """Get text content from URL.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments
            
        Returns:
            Text content or None
        """
        response = await self.get(url, **kwargs)
        if response:
            return await response.text()
        return None
    
    async def get_json(self, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Get JSON content from URL.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments
            
        Returns:
            JSON data or None
        """
        response = await self.get(url, **kwargs)
        if response:
            try:
                return await response.json()
            except Exception as e:
                logger.error(f"Failed to parse JSON from {url}: {e}")
        return None
    
    async def download_file(self, url: str, output_path: str) -> bool:
        """Download file from URL.
        
        Args:
            url: URL to download
            output_path: Path to save file
            
        Returns:
            True if successful
        """
        response = await self.get(url)
        if response:
            try:
                with open(output_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                return True
            except Exception as e:
                logger.error(f"Failed to download {url}: {e}")
        return False
