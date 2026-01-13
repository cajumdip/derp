"""Image extractor."""

from typing import List, Dict, Any
from bs4 import BeautifulSoup
import re
from .media import MediaExtractor


class ImageExtractor(MediaExtractor):
    """Extract images from HTML content."""
    
    async def extract(self, html: str, source_url: str) -> List[Dict[str, Any]]:
        """Extract images from HTML.
        
        Args:
            html: HTML content
            source_url: Source URL
            
        Returns:
            List of image URLs
        """
        soup = BeautifulSoup(html, 'lxml')
        images = []
        
        # Extract from img tags
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                images.append({
                    'url': self._resolve_url(src, source_url),
                    'alt': img.get('alt', ''),
                    'type': 'image'
                })
        
        # Extract from CSS background images
        for element in soup.find_all(style=re.compile(r'background-image')):
            style = element.get('style', '')
            urls = re.findall(r'url\(["\']?([^"\']+)["\']?\)', style)
            for url in urls:
                images.append({
                    'url': self._resolve_url(url, source_url),
                    'type': 'image',
                    'source': 'css'
                })
        
        return images
    
    def _resolve_url(self, url: str, base_url: str) -> str:
        """Resolve relative URLs.
        
        Args:
            url: URL to resolve
            base_url: Base URL
            
        Returns:
            Absolute URL
        """
        from urllib.parse import urljoin
        return urljoin(base_url, url)
