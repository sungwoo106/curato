"""
Enhanced Kakao Map API Client Package

This package provides comprehensive utilities for interacting with the Kakao Map API
with advanced features including smart caching, batch processing, and enhanced
place selection logic.

Key Features:
- Smart caching system with TTL and persistent storage
- Batch processing for multiple location types
- Enhanced place selection (10-15 places per type instead of just closest)
- Comprehensive error handling and fallbacks
- Cache management utilities
"""

from .kakao_api import (
    search_places,
    autocomplete_location,
    format_kakao_places_for_prompt,
    # Enhanced search and selection
    get_progressive_place_selection_enhanced,
    # Cache management
    clear_cache,
    get_cache_stats,
    clear_expired_cache
)

from .location_fetcher import (
    get_location_coordinates,
    get_multiple_location_coordinates,
    validate_coordinates,
    get_location_with_fallback
)

__all__ = [
    # Core search functions
    'search_places',
    
    # Location utilities
    'autocomplete_location',
    'get_location_coordinates',
    'get_multiple_location_coordinates',
    'validate_coordinates',
    'get_location_with_fallback',
    
    # Enhanced search and selection
    'get_progressive_place_selection_enhanced',
    
    # Data formatting
    'format_kakao_places_for_prompt',
    
    # Cache management
    'clear_cache',
    'get_cache_stats',
    'clear_expired_cache'
]
