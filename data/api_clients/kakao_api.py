"""
Kakao Map API Client Utilities

This module provides comprehensive utilities for interacting with the Kakao Map API.
It includes functions for searching places, getting location autocomplete suggestions,
and formatting results for use in AI prompts.

Key Features:
- Smart caching system with TTL and cache invalidation
- Enhanced place search with multiple candidate collection (10-15 places)
- Batch processing for multiple location types
- Location autocomplete for real-time suggestions
- Result formatting for AI prompt generation
- Error handling and graceful fallbacks

The module uses a smart caching system for performance optimization with
automatic coordinate rounding to handle floating-point precision.
"""

import requests
import json
import time
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from secure.crypto_utils import get_kakao_map_api_key
import sys

# Use the centralized cache manager from core module
from core.cache_manager import CacheManager

# Initialize global cache instance
_cache_manager = CacheManager()

# =============================================================================
# ENHANCED PLACE SEARCH FUNCTIONALITY
# =============================================================================

def search_places(query: str, lat: float, lng: float, radius: int = 1000, size: int = 15):
    """
    Search for places using the Kakao Map API with intelligent caching.
    
    This function searches for places near the specified coordinates using
    the Kakao Map API. Results are cached using the smart cache system
    to avoid duplicate API calls for similar searches.
    
    Args:
        query (str): Search keyword (e.g., "카페", "restaurant", "museum")
        lat (float): Latitude of the center point for the search
        lng (float): Longitude of the center point for the search
        radius (int): Search radius in meters (default: 1000m = 1km)
        size (int): Number of results to return (default: 15, max: 15)
    
    Returns:
        dict: JSON response from the Kakao Map API containing place information
              Includes place details like name, address, coordinates, distance, etc.
    
    Raises:
        requests.HTTPError: If the API request fails (4xx, 5xx status codes)
        requests.RequestException: For network or connection issues
        
    Example:
        >>> results = search_places("카페", 37.5563, 126.9237, 1000, 15)
        >>> print(f"Found {len(results['documents'])} cafes")
        Found 15 cafes
    
    Cache Behavior:
        - Results are cached using the smart cache system
        - Smart cache with TTL and persistent storage
        - Coordinate rounding is handled automatically by the cache system
    """
    # Check cache first using centralized cache manager
    cache_key = _cache_manager._generate_cache_key(query, [query], (lat, lng), radius / 1000.0)
    cached_result = _cache_manager.get_cached_results(cache_key)
    if cached_result:
        return cached_result
    
    # Get the API key from secure storage
    api_key = get_kakao_map_api_key()

    # Kakao Map API endpoint for keyword-based place search
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    
    # Set up request headers with authentication
    headers = {
        "Authorization": f"KakaoAK {api_key}"
    }
    
    # Set up search parameters
    params = {
        "query": query,           # Search keyword
        "x": str(lng),           # Longitude (Kakao API uses x for longitude)
        "y": str(lat),           # Latitude (Kakao API uses y for latitude)
        "radius": radius,         # Search radius in meters
        "size": min(size, 15),   # Number of results to return (max 15)
        "sort": "distance"       # Sort results by distance from center point
    }

    # Make the HTTP GET request to the Kakao Map API
    response = requests.get(url, headers=headers, params=params)
    
    # Raise an exception for HTTP error status codes (4xx, 5xx)
    response.raise_for_status()
    
    # Parse the response
    result = response.json()
    
    # Cache the result
    _cache_manager.cache_results(cache_key, result)
    
    # Return the parsed JSON response
    return result

def search_multiple_place_types(place_types: List[str], lat: float, lng: float, 
                               radius: int = 1000, places_per_type: int = 15) -> Dict[str, List[Dict]]:
    """
    Search for multiple place types simultaneously with optimized batch processing.
    
    This function efficiently searches for multiple place types in parallel,
    collecting 10-15 places for each type instead of just the closest one.
    It uses smart caching to minimize API calls and provides comprehensive
    candidate pools for better itinerary planning.
    
    Optimization features:
    - Uses category codes when available for more precise results
    - Implements intelligent batching to reduce API calls
    - Smart caching with coordinate rounding
    - Rate limiting awareness
    
    Args:
        place_types (List[str]): List of place types to search for
        lat (float): Latitude of the center point
        lng (float): Longitude of the center point
        radius (int): Search radius in meters (default: 1000m)
        places_per_type (int): Number of places to collect per type (default: 15)
    
    Returns:
        Dict[str, List[Dict]]: Dictionary where keys are place types and values
                               are lists of places with full details
    
    Example:
        >>> types = ["카페", "식당", "공원"]
        >>> results = search_multiple_place_types(types, 37.5563, 126.9237)
        >>> print(f"Found {len(results['카페'])} cafes")
        Found 15 cafes
    """
    results = {}
    
    # Group place types by search method for optimization
    category_search_types = []
    keyword_search_types = []
    
    for place_type in place_types:
        # Check if we have a category code for this place type
        category_code = get_category_code_for_place_type(place_type)
        if category_code:
            category_search_types.append((place_type, category_code))
        else:
            keyword_search_types.append(place_type)
    
    print(f"🔍 Using category search for {len(category_search_types)} types, keyword search for {len(keyword_search_types)} types", file=sys.stderr)
    
    # Process category-based searches first (more precise)
    for place_type, category_code in category_search_types:
        try:
            print(f"🔍 Category search for {place_type} (code: {category_code})", file=sys.stderr)
            search_result = search_places_by_category(category_code, lat, lng, radius, places_per_type)
            documents = search_result.get("documents", [])
            
            # Add category information to each place
            for place in documents:
                place['category_code'] = category_code
                place['category_name'] = KAKAO_CATEGORY_CODES.get(category_code, place_type)
            
            results[place_type] = documents
            print(f"✅ Found {len(documents)} places for {place_type} using category search", file=sys.stderr)
            
        except Exception as e:
            print(f"⚠️ Category search failed for {place_type}: {e}", file=sys.stderr)
            # Fall back to keyword search
            try:
                print(f"🔄 Falling back to keyword search for {place_type}", file=sys.stderr)
                search_result = search_places(place_type, lat, lng, radius, places_per_type)
                documents = search_result.get("documents", [])
                results[place_type] = documents
                print(f"✅ Found {len(documents)} places for {place_type} using keyword search", file=sys.stderr)
            except Exception as fallback_error:
                print(f"❌ Both category and keyword search failed for {place_type}: {fallback_error}", file=sys.stderr)
                results[place_type] = []
    
    # Process keyword-based searches
    for place_type in keyword_search_types:
        try:
            print(f"🔍 Keyword search for {place_type}", file=sys.stderr)
            search_result = search_places(place_type, lat, lng, radius, places_per_type)
            documents = search_result.get("documents", [])
            results[place_type] = documents
            print(f"✅ Found {len(documents)} places for {place_type} using keyword search", file=sys.stderr)
            
        except Exception as e:
            print(f"❌ Keyword search failed for {place_type}: {e}", file=sys.stderr)
            results[place_type] = []
    
    # Log summary
    total_places = sum(len(places) for places in results.values())
    print(f"🎯 Total places found across all types: {total_places}", file=sys.stderr)
    
    return results

# =============================================================================
# LOCATION AUTOCOMPLETE FUNCTIONALITY
# =============================================================================

def autocomplete_location(query: str) -> list:
    """
    Get location autocomplete suggestions from the Kakao Map API.
    
    This function provides real-time location suggestions as users type,
    enabling autocomplete functionality in the UI. It searches for locations
    that match the partial query string and returns up to 5 suggestions.
    
    Args:
        query (str): Partial location query string (e.g., "홍대", "Gang")
    
    Returns:
        list: JSON response from Kakao Map API with location suggestions
              Each suggestion includes place name, coordinates, and other details
    
    Raises:
        requests.HTTPError: If the API request fails
        requests.RequestException: For network or connection issues
        
    Example:
        >>> suggestions = autocomplete_location("홍대")
        >>> for place in suggestions['documents']:
        ...     print(f"- {place['place_name']}")
        - 홍대입구역
        - 홍대거리
        - 홍대입구
    """
    # Get the API key from secure storage
    api_key = get_kakao_map_api_key()

    # Kakao Map API endpoint for keyword search (same as place search)
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    
    # Set up request headers with authentication
    headers = {"Authorization": f"KakaoAK {api_key}"}
    
    # Set up search parameters for autocomplete
    # Limit to 5 results for quick response and manageable UI display
    params = {"query": query, "size": 5}

    # Make the HTTP GET request to the Kakao Map API
    response = requests.get(url, headers=headers, params=params)
    
    # Raise an exception for HTTP error status codes
    response.raise_for_status()
    
    # Return the parsed JSON response with suggestions
    return response.json()

# =============================================================================
# RESULT FORMATTING FOR AI PROMPTS
# =============================================================================

def format_kakao_places_for_prompt(kakao_results: Dict[str, List[Dict]]) -> List[Dict]:
    """
    Format Kakao Map API results into a standardized format for AI prompts.
    
    This function transforms the raw Kakao Map API results into a clean,
    consistent format that can be easily consumed by AI models for generating
    itineraries. It extracts only the essential fields needed for the prompts
    and handles missing or malformed data gracefully.
    
    Args:
        kakao_results (Dict[str, List[Dict]]): Dictionary where keys are place types
                                              and values are lists of places from the API
    
    Returns:
        List[Dict]: List of formatted places with standardized field names
                   Each place contains: place_name, road_address_name, place_type,
                   distance, place_url, latitude, longitude
    
    Example:
        >>> raw_results = {"카페": [{"place_name": "스타벅스", "y": "37.5563", ...}]}
        >>> formatted = format_kakao_places_for_prompt(raw_results)
        >>> print(formatted[0]['place_name'])
        스타벅스
        
    Data Processing:
        - Extracts essential fields from API response
        - Converts string coordinates to float values
        - Handles missing data with sensible defaults
        - Skips places with malformed data
    """
    formatted = []

    # Iterate through each place type and its associated places
    for place_type, places in kakao_results.items():
        for place in places:
            try:
                # Create a standardized place object with essential fields
                formatted.append({
                    "place_name": place.get("place_name", ""),                    # Name of the place
                    "road_address_name": place.get("road_address_name") or place.get("address_name", ""),  # Street address (fallback to general address)
                    "place_type": place_type,                                     # Category/type of place
                    "distance": int(place.get("distance", "99999")),             # Distance in meters (fallback to large number)
                    "place_url": place.get("place_url", ""),                     # URL to place details on Kakao Maps
                    "latitude": float(place.get("y", "0")),                      # Latitude coordinate (convert to float)
                    "longitude": float(place.get("x", "0")),                     # Longitude coordinate (convert to float)
                })
            except Exception as e:
                # Skip places with malformed or missing data
                # This ensures the function continues processing even if some data is invalid
                continue

    # Return the list of formatted places ready for AI prompt generation
    return formatted

# =============================================================================
# KAKAO API CATEGORY CODES AND ENHANCED SEARCH
# =============================================================================

# Import category codes from centralized constants
from constants import KAKAO_CATEGORY_CODES, PLACE_TYPE_CATEGORY_MAPPINGS

def search_places_by_category(category_code: str, lat: float, lng: float, 
                             radius: int = 1000, size: int = 15) -> Dict:
    """
    Search for places using Kakao API category codes for precise place type filtering.
    
    This function uses the official Kakao API category codes instead of text queries,
    providing more accurate and consistent results for specific place types.
    
    Args:
        category_code (str): Kakao API category code (e.g., "CE7" for cafes)
        lat (float): Latitude of the center point
        lng (float): Longitude of the center point
        radius (int): Search radius in meters (default: 1000m)
        size (int): Number of results to return (default: 15, max: 15)
    
    Returns:
        dict: JSON response from Kakao Map API with places of the specified category
    
    Example:
        >>> # Search for cafes using category code
        >>> cafes = search_places_by_category("CE7", 37.5563, 126.9237, 1000, 15)
        >>> print(f"Found {len(cafes['documents'])} cafes")
        Found 15 cafes
    """
    # Check cache first using centralized cache manager
    cache_key = _cache_manager._generate_cache_key(category_code, [category_code], (lat, lng), radius / 1000.0)
    cached_result = _cache_manager.get_cached_results(cache_key)
    if cached_result:
        return cached_result
    
    # Get the API key from secure storage
    api_key = get_kakao_map_api_key()

    # Kakao Map API endpoint for category-based search
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    
    # Set up request headers with authentication
    headers = {
        "Authorization": f"KakaoAK {api_key}"
    }
    
    # Set up search parameters for category search
    params = {
        "category_group_code": category_code,  # Category code (e.g., "CE7" for cafes)
        "x": str(lng),                        # Longitude
        "y": str(lat),                        # Latitude
        "radius": radius,                      # Search radius in meters
        "size": min(size, 15),                # Number of results (max 15)
        "sort": "distance"                    # Sort by distance
    }

    # Make the HTTP GET request to the Kakao Map API
    response = requests.get(url, headers=headers, params=params)
    
    # Raise an exception for HTTP error status codes
    response.raise_for_status()
    
    # Parse the response
    result = response.json()
    
    # Cache the result
    _cache_manager.cache_results(cache_key, result)
    
    # Return the parsed JSON response
    return result

def get_category_code_for_place_type(place_type: str) -> Optional[str]:
    """
    Get the Kakao API category code for a given place type.
    
    This function maps human-readable place types to the official
    Kakao API category codes for more precise searching.
    
    Args:
        place_type (str): Human-readable place type (e.g., "카페", "restaurant")
    
    Returns:
        Optional[str]: Kakao API category code if found, None otherwise
    
    Example:
        >>> get_category_code_for_place_type("카페")
        'CE7'
        >>> get_category_code_for_place_type("restaurant")
        'FD6'
    """
    # Check for exact matches first using centralized mappings
    if place_type in PLACE_TYPE_CATEGORY_MAPPINGS:
        return PLACE_TYPE_CATEGORY_MAPPINGS[place_type]
    
    # Check for partial matches (case-insensitive)
    place_type_lower = place_type.lower()
    for key, value in PLACE_TYPE_CATEGORY_MAPPINGS.items():
        if place_type_lower in key.lower() or key.lower() in place_type_lower:
            return value
    
    # If no match found, return None
    return None

# =============================================================================
# CACHE MANAGEMENT UTILITIES
# =============================================================================

def clear_cache():
    """
    Clear all cached data.
    
    This function removes all entries from the cache, including both
    the cached results and their timestamps.
    """
    _cache_manager._cache.clear()
    _cache_manager._cache_timestamps.clear()

def clear_expired_cache():
    """
    Remove expired cache entries.
    
    This function calls the cache manager's cleanup method to remove
    all expired entries based on the TTL (Time To Live) setting.
    """
    _cache_manager._cleanup_cache()
