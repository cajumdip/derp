"""User agent rotation utility."""

import random
from typing import List


class UserAgentRotator:
    """Rotates through a list of user agent strings."""
    
    def __init__(self, user_agents: List[str]):
        """Initialize with list of user agents.
        
        Args:
            user_agents: List of user agent strings
        """
        self.user_agents = user_agents
        self.current_index = 0
    
    def get_random(self) -> str:
        """Get a random user agent.
        
        Returns:
            Random user agent string
        """
        return random.choice(self.user_agents)
    
    def get_next(self) -> str:
        """Get next user agent in rotation.
        
        Returns:
            Next user agent string
        """
        ua = self.user_agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.user_agents)
        return ua


# Default user agents to use
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
]
