"""Video extractor."""

from typing import List, Dict, Any
from bs4 import BeautifulSoup
import re
from .media import MediaExtractor


class VideoExtractor(MediaExtractor):
    """Extract videos from HTML content."""
    
    async def extract(self, html: str, source_url: str) -> List[Dict[str, Any]]:
        """Extract videos from HTML.
        
        Args:
            html: HTML content
            source_url: Source URL
            
        Returns:
            List of video URLs
        """
        soup = BeautifulSoup(html, 'lxml')
        videos = []
        
        # Extract YouTube embeds
        youtube_patterns = [
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'youtu\.be/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in youtube_patterns:
            for match in re.finditer(pattern, html):
                video_id = match.group(1)
                videos.append({
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'platform': 'youtube',
                    'video_id': video_id,
                    'type': 'video'
                })
        
        # Extract video tags
        for video in soup.find_all('video'):
            src = video.get('src')
            if src:
                videos.append({
                    'url': self._resolve_url(src, source_url),
                    'type': 'video'
                })
            
            # Check source tags within video
            for source in video.find_all('source'):
                src = source.get('src')
                if src:
                    videos.append({
                        'url': self._resolve_url(src, source_url),
                        'type': 'video'
                    })
        
        # Direct video file links
        video_extensions = ['.mp4', '.avi', '.flv', '.wmv', '.mov']
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if any(href.lower().endswith(ext) for ext in video_extensions):
                videos.append({
                    'url': self._resolve_url(href, source_url),
                    'type': 'video'
                })
        
        return videos
    
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
