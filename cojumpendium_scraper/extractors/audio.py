"""Audio extractor."""

from typing import List, Dict, Any
from bs4 import BeautifulSoup
import re
from .media import MediaExtractor


class AudioExtractor(MediaExtractor):
    """Extract audio from HTML content."""
    
    async def extract(self, html: str, source_url: str) -> List[Dict[str, Any]]:
        """Extract audio from HTML.
        
        Args:
            html: HTML content
            source_url: Source URL
            
        Returns:
            List of audio URLs
        """
        soup = BeautifulSoup(html, 'lxml')
        audio_files = []
        
        # Extract audio tags
        for audio in soup.find_all('audio'):
            src = audio.get('src')
            if src:
                audio_files.append({
                    'url': self._resolve_url(src, source_url),
                    'type': 'audio'
                })
            
            # Check source tags within audio
            for source in audio.find_all('source'):
                src = source.get('src')
                if src:
                    audio_files.append({
                        'url': self._resolve_url(src, source_url),
                        'type': 'audio'
                    })
        
        # Direct audio file links
        audio_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.m4a']
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if any(href.lower().endswith(ext) for ext in audio_extensions):
                audio_files.append({
                    'url': self._resolve_url(href, source_url),
                    'type': 'audio',
                    'title': link.get_text(strip=True)
                })
        
        # Extract Soundcloud embeds
        soundcloud_pattern = r'soundcloud\.com/([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)'
        for match in re.finditer(soundcloud_pattern, html):
            audio_files.append({
                'url': f'https://soundcloud.com/{match.group(1)}',
                'platform': 'soundcloud',
                'type': 'audio'
            })
        
        # MySpace music player (old format)
        myspace_pattern = r'myspace\.com.*?music.*?songId=(\d+)'
        for match in re.finditer(myspace_pattern, html):
            audio_files.append({
                'url': f'https://myspace.com/music/song/{match.group(1)}',
                'platform': 'myspace',
                'type': 'audio'
            })
        
        return audio_files
    
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
