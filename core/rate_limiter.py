"""
Rate Limiting Module

This module provides rate limiting functionality to prevent excessive API calls
and respect external service rate limits (e.g., Kakao Map API).
"""

import time
from collections import deque
from typing import Dict
import sys

class APIRateLimiter:
    """
    Rate limiter to prevent excessive API calls and respect API rate limits.
    
    Kakao API limits:
    - Daily: 100,000 requests
    - Monthly: 3,000,000 requests
    - Recommended: Max 100 requests per minute
    """
    
    def __init__(self, max_calls: int = 100, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum calls allowed in the time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()
    
    def can_call(self) -> bool:
        """
        Check if an API call can be made.
        
        Returns:
            True if call is allowed, False otherwise
        """
        now = time.time()
        
        # Remove old calls outside the time window
        while self.calls and now - self.calls[0] > self.time_window:
            self.calls.popleft()
        
        # Check if we can make another call
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits."""
        if not self.can_call():
            # Calculate how long to wait
            oldest_call = self.calls[0]
            wait_time = self.time_window - (time.time() - oldest_call)
            if wait_time > 0:
                print(f"⏳ Rate limit reached, waiting {wait_time:.1f} seconds...", file=sys.stderr)
                time.sleep(wait_time)
    
    def get_status(self) -> Dict:
        """
        Get current rate limiter status.
        
        Returns:
            Status information including current calls and limits
        """
        now = time.time()
        # Remove old calls
        while self.calls and now - self.calls[0] > self.time_window:
            self.calls.popleft()
        
        return {
            "current_calls": len(self.calls),
            "max_calls": self.max_calls,
            "time_window": self.time_window,
            "calls_remaining": max(0, self.max_calls - len(self.calls))
        }
