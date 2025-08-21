"""
Cache Management Module

This module handles caching of place search results to improve performance
and reduce API calls to external services.
"""

import time
from typing import Dict, List, Optional
import sys

def _log(level: str, message: str):
    """Simple logging function."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {level} - {message}", file=sys.stderr)

class CacheManager:
    """
    Manages caching of place search results with TTL and size limits.
    
    Features:
    - Time-based expiration (1 hour TTL)
    - Size-based cleanup (max 50 entries)
    - Automatic cleanup of expired entries
    - Cache key generation based on search parameters
    """
    
    def __init__(self):
        """Initialize the cache manager."""
        self._cache = {}
        self._cache_timestamps = {}
        self._cache_ttl = 3600  # 1 hour
        self._max_cache_size = 50
    
    def _generate_cache_key(self, location_name: str, place_types: List[str], 
                           start_location: tuple, max_distance_km: float) -> str:
        """
        Generate a cache key based on search parameters.
        
        Args:
            location_name: Human-readable location name
            place_types: List of place types to search for
            start_location: Starting coordinates (lat, lng)
            max_distance_km: Search radius in kilometers
            
        Returns:
            str: Unique cache key for this search
        """
        # Sort place types for consistent cache keys
        sorted_types = sorted(place_types)
        types_str = "_".join(sorted_types)
        
        # Round coordinates to 2 decimal places (~1km precision)
        rounded_lat = round(start_location[0], 2)
        rounded_lng = round(start_location[1], 2)
        
        # Include search radius in cache key
        radius_m = int(max_distance_km * 1000)
        
        cache_key = f"{location_name}_{types_str}_{rounded_lat}_{rounded_lng}_{radius_m}"
        return cache_key
    
    def get_cached_results(self, cache_key: str) -> Optional[Dict[str, List[Dict]]]:
        """
        Retrieve cached results if available and not expired.
        
        Args:
            cache_key: Cache key for the search
            
        Returns:
            Cached results or None if not found/expired
        """
        try:
            if cache_key in self._cache:
                timestamp = self._cache_timestamps.get(cache_key, 0)
                current_time = time.time()
                
                if current_time - timestamp < self._cache_ttl:
                    _log("SUCCESS", f"Cache hit for key: {cache_key[:50]}...")
                    return self._cache[cache_key]
                else:
                    # Cache expired, remove it
                    del self._cache[cache_key]
                    del self._cache_timestamps[cache_key]
            
            return None
            
        except Exception as e:
            _log("WARNING", f"Cache retrieval failed: {e}")
            return None
    
    def cache_results(self, cache_key: str, results: Dict[str, List[Dict]]):
        """
        Cache the search results for future use.
        
        Args:
            cache_key: Cache key for the search
            results: Results to cache
        """
        try:
            # Store results and timestamp
            self._cache[cache_key] = results
            self._cache_timestamps[cache_key] = time.time()
            
            # Implement cache size limit to prevent memory issues
            if len(self._cache) > self._max_cache_size:
                self._cleanup_cache()
                
        except Exception as e:
            _log("WARNING", f"Caching failed: {e}")
    
    def _cleanup_cache(self):
        """Clean up old cache entries to prevent memory issues."""
        try:
            # Remove expired entries
            current_time = time.time()
            expired_keys = []
            
            for key, timestamp in self._cache_timestamps.items():
                if current_time - timestamp > self._cache_ttl:
                    expired_keys.append(key)
            
            # Remove expired entries
            for key in expired_keys:
                del self._cache[key]
                del self._cache_timestamps[key]
            
            # If still too many entries, remove oldest ones
            if len(self._cache) > self._max_cache_size:
                # Sort by timestamp and keep only the most recent
                sorted_keys = sorted(self._cache_timestamps.items(), key=lambda x: x[1], reverse=True)
                keys_to_keep = [key for key, _ in sorted_keys[:self._max_cache_size]]
                
                keys_to_remove = [key for key in self._cache.keys() if key not in keys_to_keep]
                for key in keys_to_remove:
                    del self._cache[key]
                    del self._cache_timestamps[key]
                
        except Exception as e:
            _log("WARNING", f"⚠️ Cache cleanup failed: {e}")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics for monitoring."""
        current_time = time.time()
        expired_entries = sum(1 for ts in self._cache_timestamps.values() 
                           if current_time - ts > self._cache_ttl)
        
        return {
            "total_cached_entries": len(self._cache),
            "cache_size_limit": self._max_cache_size,
            "cache_utilization_percent": (len(self._cache) / self._max_cache_size) * 100,
            "expired_entries": expired_entries,
            "active_entries": len(self._cache) - expired_entries
        }
