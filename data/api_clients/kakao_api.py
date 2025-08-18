"""
Kakao Map API Client Utilities

This module provides comprehensive utilities for interacting with the Kakao Map API.
It includes functions for searching places, getting location autocomplete suggestions,
and formatting results for use in AI prompts.

Key Features:
- Intelligent caching with coordinate rounding to avoid duplicate API calls
- Place search with distance-based sorting
- Location autocomplete for real-time suggestions
- Result formatting for AI prompt generation
- Error handling and graceful fallbacks

The module uses functools.lru_cache for performance optimization and includes
a custom decorator for coordinate-based caching to handle floating-point precision.
"""

import requests
from typing import Dict, List, Optional
from functools import lru_cache, wraps
from secure.crypto_utils import get_kakao_map_api_key

# =============================================================================
# CACHING DECORATOR FOR COORDINATE-BASED CACHING
# =============================================================================

def _rounded_cache(func):
    """
    Custom decorator that rounds latitude and longitude before caching.
    
    This decorator addresses the issue of floating-point precision in coordinates
    that could cause cache misses for nearly identical locations. By rounding
    coordinates to 4 decimal places (~11 meters precision), we ensure that
    searches for very close locations use cached results when appropriate.
    
    Args:
        func: The function to be wrapped with coordinate rounding
        
    Returns:
        wrapper: Function wrapper that rounds coordinates before calling the original function
        
    Example:
        >>> @_rounded_cache
        ... def search_places(query, lat, lng, radius):
        ...     pass
        >>> # Coordinates (37.5563, 126.9237) and (37.5564, 126.9238) 
        >>> # will use the same cache entry
    """
    @wraps(func)
    def wrapper(query: str, lat: float, lng: float, *args, **kwargs):
        # Round coordinates to 4 decimal places (~11 meters precision)
        # This prevents cache misses for nearly identical locations
        rounded_lat = round(lat, 4)
        rounded_lng = round(lng, 4)
        return func(query, rounded_lat, rounded_lng, *args, **kwargs)

    # Preserve cache management methods from the original function
    # This allows callers to clear cache or get cache info
    wrapper.cache_clear = getattr(func, "cache_clear", lambda: None)
    wrapper.cache_info = getattr(func, "cache_info", lambda: None)
    return wrapper

# =============================================================================
# CORE PLACE SEARCH FUNCTIONALITY
# =============================================================================

@_rounded_cache
@lru_cache(maxsize=128)
def search_places(query: str, lat: float, lng: float, radius: int = 1000, size: int = 10):
    """
    Search for places using the Kakao Map API with intelligent caching.
    
    This function searches for places near the specified coordinates using
    the Kakao Map API. Results are cached based on query and rounded coordinates
    to avoid duplicate API calls for similar searches.
    
    The function uses two levels of caching:
    1. Custom coordinate rounding to handle floating-point precision
    2. LRU cache with 128 entries for performance optimization
    
    Args:
        query (str): Search keyword (e.g., "카페", "restaurant", "museum")
        lat (float): Latitude of the center point for the search
        lng (float): Longitude of the center point for the search
        radius (int): Search radius in meters (default: 1000m = 1km)
        size (int): Number of results to return (default: 10, max: 15)
    
    Returns:
        dict: JSON response from the Kakao Map API containing place information
              Includes place details like name, address, coordinates, distance, etc.
    
    Raises:
        requests.HTTPError: If the API request fails (4xx, 5xx status codes)
        requests.RequestException: For network or connection issues
        
    Example:
        >>> results = search_places("카페", 37.5563, 126.9237, 1000, 5)
        >>> print(f"Found {len(results['documents'])} cafes")
        Found 5 cafes
    
    Cache Behavior:
        - Results are cached based on query and rounded coordinates
        - Cache size limited to 128 entries (LRU eviction)
        - Coordinate rounding prevents cache misses for nearby locations
    """
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
        "size": size,            # Number of results to return
        "sort": "distance"       # Sort results by distance from center point
    }

    # Make the HTTP GET request to the Kakao Map API
    response = requests.get(url, headers=headers, params=params)
    
    # Raise an exception for HTTP error status codes (4xx, 5xx)
    # This helps identify API issues, authentication problems, etc.
    response.raise_for_status()
    
    # Return the parsed JSON response
    return response.json()

def get_closest_place(query: str, lat: float, lng: float, radius: int = 1000, size: int = 10) -> Optional[Dict]:
    """
    Get the closest place result for the given query and location.
    
    This function searches for places and returns only the closest one
    based on the distance field from the Kakao Map API response. It's
    useful when you need just one optimal location rather than a list
    of options.
    
    Args:
        query (str): Search keyword (e.g., "카페", "restaurant")
        lat (float): Latitude of the center point
        lng (float): Longitude of the center point
        radius (int): Search radius in meters (default: 1000m)
        size (int): Maximum number of results to consider (default: 10)
    
    Returns:
        Optional[Dict]: The closest place as a dictionary with place details,
                       or None if no results found or if the search fails
    
    Example:
        >>> closest_cafe = get_closest_place("카페", 37.5563, 126.9237, 1000)
        >>> if closest_cafe:
        ...     print(f"Closest cafe: {closest_cafe['place_name']}")
        ...     print(f"Distance: {closest_cafe['distance']}m")
        Closest cafe: 스타벅스 홍대점
        Distance: 150m
    """
    # Search for places using the cached search function
    data = search_places(query, lat, lng, radius, size)
    
    # Extract the documents array from the API response
    documents = data.get("documents", [])
    
    # Return None if no results were found
    if not documents:
        return None
    
    # Find the closest place by comparing distance values
    # The distance field contains the distance in meters as a string
    # We convert to int for comparison, with a fallback for missing values
    return min(documents, key=lambda d: int(d.get("distance", "999999")))

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
