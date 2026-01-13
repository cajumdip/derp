"""Base media extractor."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from ..config import Config
from ..database import Database
from ..utils.http import HTTPClient
from ..utils.hashing import hash_file


logger = logging.getLogger(__name__)


class MediaExtractor(ABC):
    """Base class for media extractors."""
    
    def __init__(self, config: Config, database: Database, http_client: HTTPClient):
        """Initialize extractor.
        
        Args:
            config: Configuration object
            database: Database instance
            http_client: HTTP client
        """
        self.config = config
        self.db = database
        self.http = http_client
        self.download_dir = Path(config.get('general', 'download_dir', default='./downloads'))
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    async def extract(self, html: str, source_url: str) -> List[Dict[str, Any]]:
        """Extract media from HTML content.
        
        Args:
            html: HTML content
            source_url: Source URL
            
        Returns:
            List of extracted media items
        """
        pass
    
    async def download_media(self, media_url: str, media_type: str, 
                            source_url: str, url_id: Optional[int] = None) -> bool:
        """Download media file.
        
        Args:
            media_url: URL of media to download
            media_type: Type of media (image/video/audio)
            source_url: Source page URL
            url_id: Associated URL ID
            
        Returns:
            True if successful
        """
        try:
            # Create subdirectory for media type
            type_dir = self.download_dir / media_type
            type_dir.mkdir(exist_ok=True)
            
            # Generate filename from URL
            filename = Path(media_url).name
            if not filename:
                filename = hash_file(media_url)[:16]
            
            output_path = type_dir / filename
            
            # Download file
            success = await self.http.download_file(media_url, str(output_path))
            
            if success and output_path.exists():
                # Calculate hash
                file_hash = hash_file(str(output_path))
                file_size = output_path.stat().st_size
                
                # Save to database
                media_id = self.db.add_media_file(
                    file_path=str(output_path),
                    file_type=media_type,
                    file_hash=file_hash,
                    file_size=file_size,
                    original_url=media_url,
                    url_id=url_id
                )
                
                if media_id == -1:
                    logger.info(f"Skipping duplicate file: {filename}")
                    output_path.unlink()  # Remove duplicate
                    return False
                
                logger.info(f"Downloaded {media_type}: {filename}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to download {media_url}: {e}")
            return False
