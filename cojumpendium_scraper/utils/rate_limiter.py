"""Advanced rate limiter with exponential backoff and jittering."""

import asyncio
import time
import random
import logging
from typing import Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class AdaptiveRateLimiter:
    """Sophisticated rate limiter for Wayback Machine scraping.
    
    Features:
    - Minimum delay between requests with jittering
    - Exponential backoff on errors
    - Hourly request limits
    - Periodic cooldown periods
    - Request counting and tracking
    """
    
    def __init__(self, config: dict):
        """Initialize rate limiter.
        
        Args:
            config: Rate limiting configuration dict with keys:
                - min_delay: Minimum seconds between requests
                - max_delay: Maximum random delay
                - jitter: Random variance in seconds
                - backoff_base: Initial backoff on error (seconds)
                - backoff_max: Maximum backoff (seconds)
                - requests_per_hour: Max requests per hour
                - cooldown_every: Pause after this many requests
                - cooldown_duration: Pause duration in seconds
        """
        self.min_delay = config.get('min_delay', 5)
        self.max_delay = config.get('max_delay', 15)
        self.jitter = config.get('jitter', 3)
        self.backoff_base = config.get('backoff_base', 30)
        self.backoff_max = config.get('backoff_max', 600)
        self.requests_per_hour = config.get('requests_per_hour', 100)
        self.cooldown_every = config.get('cooldown_every', 50)
        self.cooldown_duration = config.get('cooldown_duration', 180)
        
        # State tracking
        self.current_backoff = 0
        self.requests_this_hour = 0
        self.hour_start = time.time()
        self.request_count = 0
        self.last_request_time = 0
        self.total_requests = 0
        self.total_errors = 0
        
        logger.info(
            f"Rate limiter initialized: {self.min_delay}-{self.max_delay}s delay, "
            f"{self.requests_per_hour} req/hr, cooldown every {self.cooldown_every} requests"
        )
    
    async def wait(self) -> None:
        """Wait before making next request.
        
        This method enforces:
        1. Hourly rate limits
        2. Periodic cooldown periods
        3. Base delay with jittering
        4. Exponential backoff if errors occurred
        """
        # Check hourly limit
        current_time = time.time()
        elapsed_hour = current_time - self.hour_start
        
        if elapsed_hour > 3600:
            # Reset hourly counter
            logger.info(
                f"Hourly window reset: {self.requests_this_hour} requests in last hour"
            )
            self.requests_this_hour = 0
            self.hour_start = current_time
        
        if self.requests_this_hour >= self.requests_per_hour:
            # Hit hourly limit, wait until next hour
            wait_time = 3600 - elapsed_hour
            logger.warning(
                f"Hourly limit reached ({self.requests_per_hour} requests), "
                f"waiting {wait_time:.0f}s until next hour"
            )
            await asyncio.sleep(wait_time)
            self.requests_this_hour = 0
            self.hour_start = time.time()
        
        # Cooldown check
        self.request_count += 1
        if self.request_count % self.cooldown_every == 0:
            logger.info(
                f"Cooldown period: completed {self.request_count} requests, "
                f"pausing for {self.cooldown_duration}s"
            )
            await asyncio.sleep(self.cooldown_duration)
        
        # Calculate base delay with jitter
        delay = random.uniform(self.min_delay, self.max_delay)
        delay += random.uniform(0, self.jitter)
        
        # Add exponential backoff if we've had errors
        if self.current_backoff > 0:
            delay += self.current_backoff
            logger.debug(f"Applying backoff: +{self.current_backoff}s (total delay: {delay:.1f}s)")
        
        # Ensure minimum time since last request
        if self.last_request_time > 0:
            time_since_last = current_time - self.last_request_time
            if time_since_last < delay:
                actual_delay = delay - time_since_last
                logger.debug(f"Waiting {actual_delay:.1f}s before next request")
                await asyncio.sleep(actual_delay)
            else:
                logger.debug(f"No wait needed, {time_since_last:.1f}s since last request")
        else:
            await asyncio.sleep(delay)
        
        # Update counters
        self.last_request_time = time.time()
        self.requests_this_hour += 1
        self.total_requests += 1
    
    def on_success(self) -> None:
        """Call this after a successful request.
        
        Gradually reduces backoff time on success.
        """
        if self.current_backoff > 0:
            # Reduce backoff gradually
            self.current_backoff = max(0, self.current_backoff - 10)
            if self.current_backoff == 0:
                logger.info("Backoff cleared after successful request")
    
    def on_error(self, status_code: int) -> None:
        """Call this after a failed request.
        
        Args:
            status_code: HTTP status code that caused the error
        """
        self.total_errors += 1
        
        # Only apply backoff for rate limit / server errors
        if status_code in [403, 429, 503, 504]:
            if self.current_backoff == 0:
                self.current_backoff = self.backoff_base
                logger.warning(
                    f"Rate limit/error detected (status {status_code}), "
                    f"starting backoff at {self.current_backoff}s"
                )
            else:
                old_backoff = self.current_backoff
                self.current_backoff = min(self.current_backoff * 2, self.backoff_max)
                logger.warning(
                    f"Increasing backoff: {old_backoff}s -> {self.current_backoff}s "
                    f"(status {status_code})"
                )
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics.
        
        Returns:
            Dictionary with current stats
        """
        return {
            'total_requests': self.total_requests,
            'total_errors': self.total_errors,
            'requests_this_hour': self.requests_this_hour,
            'current_backoff': self.current_backoff,
            'error_rate': self.total_errors / max(1, self.total_requests),
            'uptime_seconds': time.time() - self.hour_start if self.total_requests > 0 else 0
        }
    
    def reset(self) -> None:
        """Reset rate limiter state."""
        logger.info("Resetting rate limiter state")
        self.current_backoff = 0
        self.requests_this_hour = 0
        self.hour_start = time.time()
        self.request_count = 0
        self.last_request_time = 0
