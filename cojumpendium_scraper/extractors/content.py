"""Content analyzer for detecting phrases in archived pages."""

import logging
from typing import List, Dict, Any, Optional, Set
from bs4 import BeautifulSoup
import re


logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """Analyzes HTML content for target phrases."""
    
    def __init__(self, config):
        """Initialize content analyzer.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.search_phrases = config.get('search', 'phrases', default=[
            "Cojum Dip",
            "cojumdip",
            "bkaraca",
            "Bora Karaca"
        ])
    
    def analyze(self, html: str, url: str) -> Dict[str, Any]:
        """Analyze HTML content for phrases.
        
        Args:
            html: HTML content
            url: URL of the page
            
        Returns:
            Dictionary with analysis results
        """
        results = {
            'url': url,
            'phrases_found': [],
            'phrase_count': {},
            'text_length': 0,
            'has_media': False,
            'media_urls': []
        }
        
        try:
            # Parse HTML
            soup = BeautifulSoup(html, 'lxml')
            
            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            results['text_length'] = len(text)
            
            # Search for each phrase
            phrases_found = set()
            phrase_counts = {}
            
            for phrase in self.search_phrases:
                # Case-insensitive search
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                matches = pattern.findall(text)
                
                if matches:
                    phrases_found.add(phrase)
                    phrase_counts[phrase] = len(matches)
                    logger.debug(f"Found '{phrase}' {len(matches)} times in {url}")
            
            results['phrases_found'] = list(phrases_found)
            results['phrase_count'] = phrase_counts
            
            # Check for media
            media_urls = self._extract_media_urls(soup)
            results['has_media'] = len(media_urls) > 0
            results['media_urls'] = media_urls
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing content from {url}: {e}")
            return results
    
    def _extract_media_urls(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract media URLs from HTML.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of media URL dictionaries
        """
        media_urls = []
        
        # Extract images
        for img in soup.find_all('img', src=True):
            src = img['src']
            if self._is_valid_media_url(src):
                media_urls.append({
                    'type': 'image',
                    'url': src,
                    'alt': img.get('alt', '')
                })
        
        # Extract videos
        for video in soup.find_all('video', src=True):
            src = video['src']
            if self._is_valid_media_url(src):
                media_urls.append({
                    'type': 'video',
                    'url': src
                })
        
        # Extract video sources
        for source in soup.find_all('source', src=True):
            src = source['src']
            if self._is_valid_media_url(src):
                media_type = 'video' if 'video' in source.get('type', '') else 'audio'
                media_urls.append({
                    'type': media_type,
                    'url': src
                })
        
        # Extract audio
        for audio in soup.find_all('audio', src=True):
            src = audio['src']
            if self._is_valid_media_url(src):
                media_urls.append({
                    'type': 'audio',
                    'url': src
                })
        
        # Extract from embed tags
        for embed in soup.find_all('embed', src=True):
            src = embed['src']
            if self._is_valid_media_url(src):
                media_urls.append({
                    'type': 'embed',
                    'url': src
                })
        
        return media_urls
    
    def _is_valid_media_url(self, url: str) -> bool:
        """Check if URL is a valid media URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if valid media URL
        """
        if not url:
            return False
        
        # Skip data URLs, tracking pixels, etc.
        if url.startswith('data:'):
            return False
        
        if url.endswith(('.gif', '.png', '.jpg', '.jpeg')) and ('1x1' in url or 'pixel' in url):
            return False
        
        # Check for valid extensions
        media_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
            '.mp4', '.avi', '.flv', '.wmv', '.mov', '.webm',
            '.mp3', '.wav', '.ogg', '.flac', '.m4a', '.wma'
        ]
        
        url_lower = url.lower()
        return any(ext in url_lower for ext in media_extensions)
