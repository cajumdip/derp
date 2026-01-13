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
        
        # Extract from embed tags (including Flash/SWF)
        for embed in soup.find_all('embed', src=True):
            src = embed['src']
            if self._is_valid_media_url(src):
                embed_type = 'flash' if src.lower().endswith('.swf') else 'embed'
                media_urls.append({
                    'type': embed_type,
                    'url': src
                })
        
        # Extract Flash object tags
        for obj in soup.find_all('object'):
            # Look for Flash embeds in object tags
            for param in obj.find_all('param', {'name': 'movie'}):
                src = param.get('value', '')
                if src and self._is_valid_media_url(src):
                    media_urls.append({
                        'type': 'flash',
                        'url': src
                    })
        
        # Extract YouTube embeds
        for iframe in soup.find_all('iframe', src=True):
            src = iframe['src']
            youtube_match = re.search(r'youtube\.com/embed/([a-zA-Z0-9_-]+)', src)
            if youtube_match:
                video_id = youtube_match.group(1)
                media_urls.append({
                    'type': 'youtube',
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'embed_url': src
                })
        
        # Extract MySpace music player links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'myspace.com/music/player' in href.lower():
                media_urls.append({
                    'type': 'myspace_music',
                    'url': href
                })
        
        # Extract Soundcloud embeds
        for iframe in soup.find_all('iframe', src=True):
            src = iframe['src']
            if 'soundcloud.com' in src.lower():
                media_urls.append({
                    'type': 'soundcloud',
                    'url': src
                })
        
        # Extract direct file links from all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if self._is_direct_media_link(href):
                media_type = self._get_media_type_from_url(href)
                media_urls.append({
                    'type': media_type,
                    'url': href,
                    'link_text': link.get_text(strip=True)[:100]
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
            '.mp3', '.wav', '.ogg', '.flac', '.m4a', '.wma',
            '.swf'  # Flash files
        ]
        
        url_lower = url.lower()
        return any(ext in url_lower for ext in media_extensions)
    
    def _is_direct_media_link(self, url: str) -> bool:
        """Check if URL is a direct media file link.
        
        Args:
            url: URL to check
            
        Returns:
            True if direct media link
        """
        if not url:
            return False
        
        media_extensions = [
            '.mp3', '.mp4', '.flv', '.jpg', '.jpeg', '.png', '.gif',
            '.avi', '.wmv', '.mov', '.wav', '.ogg', '.flac', '.m4a',
            '.wma', '.swf', '.webm', '.bmp', '.webp'
        ]
        
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in media_extensions)
    
    def _get_media_type_from_url(self, url: str) -> str:
        """Get media type from URL extension.
        
        Args:
            url: URL to check
            
        Returns:
            Media type string
        """
        url_lower = url.lower()
        
        if any(url_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']):
            return 'image'
        elif any(url_lower.endswith(ext) for ext in ['.mp4', '.avi', '.flv', '.wmv', '.mov', '.webm']):
            return 'video'
        elif any(url_lower.endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.wma']):
            return 'audio'
        elif url_lower.endswith('.swf'):
            return 'flash'
        else:
            return 'unknown'
