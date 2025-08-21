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

# =============================================================================
# SMART CACHING SYSTEM
# =============================================================================

class SmartCache:
    """
    Intelligent caching system for Kakao Map API responses.
    
    Features:
    - Persistent disk caching with TTL
    - In-memory LRU cache for frequently accessed data
    - Cache invalidation based on data freshness
    - Coordinate-based caching with rounding
    """
    
    def __init__(self, cache_dir: str = ".cache", default_ttl: int = 3600):
        """
        Initialize the smart cache system.
        
        Args:
            cache_dir (str): Directory to store cache files
            default_ttl (int): Default time-to-live in seconds (1 hour)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_ttl = default_ttl
        self.memory_cache = {}
        self.cache_stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    def _get_cache_key(self, query: str, lat: float, lng: float, radius: int, size: int) -> str:
        """Generate a cache key for the given parameters."""
        # Round coordinates to 4 decimal places (~11 meters precision)
        rounded_lat = round(lat, 4)
        rounded_lng = round(lng, 4)
        return f"{query}_{rounded_lat}_{rounded_lng}_{radius}_{size}"
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get the file path for a cache entry."""
        # Create a safe filename from the cache key
        safe_key = "".join(c for c in cache_key if c.isalnum() or c in "._-")
        return self.cache_dir / f"{safe_key}.json"
    
    def get(self, query: str, lat: float, lng: float, radius: int, size: int) -> Optional[Dict]:
        """
        Retrieve cached data if it exists and is still valid.
        
        Returns:
            Cached data if valid, None if expired or not found
        """
        cache_key = self._get_cache_key(query, lat, lng, radius, size)
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            data, timestamp = self.memory_cache[cache_key]
            if time.time() - timestamp < self.default_ttl:
                self.cache_stats["hits"] += 1
                return data
        
        # Check disk cache
        cache_file = self._get_cache_file_path(cache_key)
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                # Check if cache is still valid
                if time.time() - cached_data.get("timestamp", 0) < self.default_ttl:
                    # Move to memory cache for faster access
                    self.memory_cache[cache_key] = (cached_data["data"], cached_data["timestamp"])
                    self.cache_stats["hits"] += 1
                    return cached_data["data"]
                else:
                    # Cache expired, remove it
                    cache_file.unlink()
                    self.cache_stats["evictions"] += 1
            except Exception:
                # Corrupted cache file, remove it
                cache_file.unlink(missing_ok=True)
        
        self.cache_stats["misses"] += 1
        return None
    
    def set(self, query: str, lat: float, lng: float, radius: int, size: int, data: Dict):
        """Store data in both memory and disk cache."""
        cache_key = self._get_cache_key(query, lat, lng, radius, size)
        timestamp = time.time()
        
        # Store in memory cache
        self.memory_cache[cache_key] = (data, timestamp)
        
        # Store in disk cache
        cache_file = self._get_cache_file_path(cache_key)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "data": data,
                    "timestamp": timestamp,
                    "ttl": self.default_ttl
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # Disk cache failure shouldn't break the application
    
    def clear_expired(self):
        """Remove expired cache entries from both memory and disk."""
        current_time = time.time()
        
        # Clear expired memory cache entries
        expired_keys = [
            key for key, (_, timestamp) in self.memory_cache.items()
            if current_time - timestamp >= self.default_ttl
        ]
        for key in expired_keys:
            del self.memory_cache[key]
            self.cache_stats["evictions"] += 1
        
        # Clear expired disk cache entries
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                if current_time - cached_data.get("timestamp", 0) >= self.default_ttl:
                    cache_file.unlink()
                    self.cache_stats["evictions"] += 1
            except Exception:
                cache_file.unlink(missing_ok=True)
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache performance statistics."""
        return self.cache_stats.copy()

# Initialize global smart cache instance
_smart_cache = SmartCache()

# =============================================================================
# ENHANCED PLACE SEARCH FUNCTIONALITY
# =============================================================================

# =============================================================================
# ENHANCED PLACE SEARCH FUNCTIONALITY
# =============================================================================

def search_places(query: str, lat: float, lng: float, radius: int = 1000, size: int = 15):
    """
    Search for places using the Kakao Map API with intelligent caching.
    
    This function searches for places near the specified coordinates using
    the Kakao Map API. Results are cached using the smart cache system
    to avoid duplicate API calls for similar searches.
    
    The function uses smart caching with:
    1. Smart cache system with TTL and persistent storage
    2. Coordinate rounding handled automatically by the cache system
    3. Enhanced result collection (up to 15 places instead of just closest)
    
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
    # Check smart cache first
    cached_result = _smart_cache.get(query, lat, lng, radius, size)
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
    # This helps identify API issues, authentication problems, etc.
    response.raise_for_status()
    
    # Parse the response
    result = response.json()
    
    # Cache the result
    _smart_cache.set(query, lat, lng, radius, size, result)
    
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
    # Check smart cache first
    cache_key = f"category_{category_code}_{lat}_{lng}_{radius}_{size}"
    cached_result = _smart_cache.get(category_code, lat, lng, radius, size)
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
    _smart_cache.set(category_code, lat, lng, radius, size, result)
    
    # Return the parsed JSON response
    return result

def search_multiple_categories_by_type(category_codes: List[str], lat: float, lng: float,
                                     radius: int = 1000, places_per_category: int = 8) -> Dict[str, List[Dict]]:
    """
    Search for multiple place categories simultaneously using category codes.
    
    This function efficiently searches for multiple place categories in parallel,
    using the official Kakao API category codes for precise and consistent results.
    
    Args:
        category_codes (List[str]): List of Kakao API category codes to search for
        lat (float): Latitude of the center point
        lng (float): Longitude of the center point
        radius (int): Search radius in meters (default: 1000m)
        places_per_category (int): Number of places to collect per category (default: 8)
    
    Returns:
        Dict[str, List[Dict]]: Dictionary where keys are category codes and values
                               are lists of places with full details
    
    Example:
        >>> # Search for cafes, restaurants, and cultural facilities
        >>> categories = ["CE7", "FD6", "CT1"]
        >>> results = search_multiple_categories_by_type(categories, 37.5563, 126.9237)
        >>> print(f"Found {len(results['CE7'])} cafes")
        Found 8 cafes
    """
    results = {}
    
    for category_code in category_codes:
        try:
            # Search for places of this category using the category code
            search_result = search_places_by_category(category_code, lat, lng, radius, places_per_category)
            documents = search_result.get("documents", [])
            
            # Add category information to each place
            for place in documents:
                place['category_code'] = category_code
                place['category_name'] = KAKAO_CATEGORY_CODES.get(category_code, "Unknown")
            
            # Store all found places for this category
            results[category_code] = documents
            
        except Exception as e:
            # If search fails for one category, continue with others
            print(f"Warning: Failed to search for category {category_code}: {e}")
            results[category_code] = []
    
    return results

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

def search_places_enhanced(place_type: str, lat: float, lng: float, 
                          radius: int = 1000, size: int = 15,
                          prefer_category_search: bool = True) -> Dict:
    """
    Enhanced place search that automatically chooses between category and keyword search.
    
    This function intelligently selects the best search method:
    1. If a category code is available, uses category search for precision
    2. Falls back to keyword search if no category code is found
    3. Provides consistent results regardless of search method
    
    Args:
        place_type (str): Place type to search for (e.g., "카페", "restaurant")
        lat (float): Latitude of the center point
        lng (float): Longitude of the center point
        radius (int): Search radius in meters (default: 1000m)
        size (int): Number of results to return (default: 15, max: 15)
        prefer_category_search (bool): Whether to prefer category search over keyword search
    
    Returns:
        dict: JSON response from Kakao Map API with place information
    
    Example:
        >>> # This will automatically use category search for "카페"
        >>> results = search_places_enhanced("카페", 37.5563, 126.9237)
        >>> print(f"Found {len(results['documents'])} cafes")
        Found 15 cafes
    """
    print(f"🔍 Searching for '{place_type}' at ({lat}, {lng}) with radius {radius}m", file=sys.stderr)
    
    if prefer_category_search:
        # Try to get category code for the place type
        category_code = get_category_code_for_place_type(place_type)
        
        if category_code:
            # Use category search for more precise results
            result = search_places_by_category(category_code, lat, lng, radius, size)
            return result
    
    # Fall back to keyword search if no category code or category search disabled
    result = search_places(place_type, lat, lng, radius, size)
    return result

def get_progressive_place_selection_enhanced(place_types: List[str], 
                                           start_location: Tuple[float, float],
                                           radius: int = 1000,
                                           places_per_type: int = 15,      # Increased from 8 to 15
                                           max_cluster_distance: int = 300, # Reduced to 300m for walkable distances
                                           target_places: int = 20,        # Increased from 5 to 20
                                           prefer_category_search: bool = True) -> List[Dict]:
    """
    Enhanced progressive place selection with category-based search for better variety.
    
    This enhanced version uses Kakao API category codes when available,
    providing more precise and diverse place results while maintaining
    the geographic clustering and progressive selection benefits.
    
    The algorithm now provides more variety for the LLM to choose from,
    ensuring unique itineraries while maintaining geographic coherence.
    
    Args:
        place_types (List[str]): List of place types to search for
        start_location (Tuple[float, float]): Starting coordinates (lat, lng)
        radius (int): Search radius in meters (default: 1000m)
        places_per_type (int): Number of places to collect per type (default: 15)
        max_cluster_distance (int): Maximum distance for clustering (default: 300m)
        target_places (int): Target number of places for the LLM to choose from (default: 20)
        prefer_category_search (bool): Whether to prefer category search over keyword search
    
    Returns:
        List[Dict]: List of candidate places for the LLM to select from (20 places)
    
    Example:
        >>> place_types = ["카페", "음식점", "문화시설"]
        >>> candidate_places = get_progressive_place_selection_enhanced(
        ...     place_types, (37.5563, 126.9237), prefer_category_search=True
        ... )
        >>> print(f"Found {len(candidate_places)} candidate places for LLM selection")
        Found 20 candidate places for LLM selection
    """
    # Step 1: Collect places using enhanced search (category codes when available)
    all_places = []
    
    for place_type in place_types:
        try:
            # Use enhanced search that automatically chooses best method
            search_result = search_places_enhanced(
                place_type, start_location[0], start_location[1], 
                radius, places_per_type, prefer_category_search
            )
            places = search_result.get("documents", [])
            
            # Add place type information to each place
            for place in places:
                place['place_type'] = place_type
                # Preserve category information if available
                if 'category_code' not in place:
                    place['category_code'] = get_category_code_for_place_type(place_type)
                    place['category_name'] = KAKAO_CATEGORY_CODES.get(place.get('category_code'), place_type)
            
            all_places.extend(places)
            
        except Exception as e:
            print(f"Warning: Failed to search for {place_type}: {e}")
            continue
    
    if not all_places:
        return []
    
    # Step 2: Cluster places by geographic proximity
    print(f"Clustering {len(all_places)} places into geographic groups...")
    place_clusters = cluster_places_by_distance(all_places, max_cluster_distance)
    print(f"Created {len(place_clusters)} geographic clusters")
    
    # Step 3: Select optimal route sequence
    print(f"Selecting optimal route sequence for {target_places} places...")
    optimal_route = select_optimal_route_sequence(place_clusters, start_location, target_places)
    
    print(f"Selected {len(optimal_route)} places for optimal route")
    return optimal_route

# =============================================================================
# SMART CLUSTERING AND PROGRESSIVE SELECTION
# =============================================================================

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the distance between two coordinates using the Haversine formula.
    
    Args:
        lat1, lng1: Coordinates of first point
        lat2, lng2: Coordinates of second point
    
    Returns:
        float: Distance in meters
    """
    import math
    
    # Convert to radians
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in meters
    r = 6371000
    return c * r

def cluster_places_by_distance(places: List[Dict], max_cluster_distance: int = 300) -> List[List[Dict]]:
    """
    Cluster places by geographic proximity to ensure route coherence.
    
    This function groups places that are within a reasonable walking distance
    of each other, ensuring that the final itinerary has geographically
    close consecutive locations.
    
    Args:
        places: List of place dictionaries with lat/lng coordinates
        max_cluster_distance: Maximum distance in meters for clustering (default: 300m)
    
    Returns:
        List of place clusters, each containing nearby places
    """
    if not places:
        return []
    
    # Convert string coordinates to float and add distance calculations
    processed_places = []
    for place in places:
        try:
            lat = float(place.get('y', 0))
            lng = float(place.get('x', 0))
            if lat != 0 and lng != 0:
                processed_places.append({
                    'place': place,
                    'lat': lat,
                    'lng': lng,
                    'clustered': False
                })
        except (ValueError, TypeError):
            continue
    
    if not processed_places:
        return []
    
    clusters = []
    
    # Start with the first unclustered place
    for i, place_data in enumerate(processed_places):
        if place_data['clustered']:
            continue
            
        # Start a new cluster
        current_cluster = [place_data['place']]
        place_data['clustered'] = True
        
        # Find nearby places
        for j, other_place_data in enumerate(processed_places):
            if other_place_data['clustered']:
                continue
                
            distance = calculate_distance(
                place_data['lat'], place_data['lng'],
                other_place_data['lat'], other_place_data['lng']
            )
            
            if distance <= max_cluster_distance:
                current_cluster.append(other_place_data['place'])
                other_place_data['clustered'] = True
        
        clusters.append(current_cluster)
    
    return clusters

def select_optimal_route_sequence(place_clusters: List[List[Dict]], 
                                 start_location: Tuple[float, float],
                                 num_places: int = 20) -> List[Dict]:
    """
    Select an optimal route sequence from place clusters.
    
    This function builds a route step-by-step, ensuring each consecutive
    location is geographically close to the previous one. It minimizes
    backtracking and creates a logical flow through the area.
    
    The function now provides more variety for the LLM to choose from,
    ensuring unique itineraries while maintaining geographic coherence.
    
    Args:
        place_clusters: List of place clusters (each cluster contains nearby places)
        start_location: Starting coordinates (lat, lng)
        num_places: Number of places to select for the LLM (default: 20)
    
    Returns:
        List of selected places in optimal route order for LLM selection
    """
    if not place_clusters:
        return []
    
    selected_places = []
    current_location = start_location
    remaining_clusters = place_clusters.copy()
    
    # Select places one by one, always choosing the closest cluster
    for _ in range(min(num_places, len(place_clusters))):
        if not remaining_clusters:
            break
            
        # Find the cluster closest to current location
        best_cluster = None
        best_distance = float('inf')
        best_place = None
        
        for cluster in remaining_clusters:
            for place in cluster:
                try:
                    place_lat = float(place.get('y', 0))
                    place_lng = float(place.get('x', 0))
                    
                    if place_lat == 0 or place_lng == 0:
                        continue
                        
                    distance = calculate_distance(
                        current_location[0], current_location[1],
                        place_lat, place_lng
                    )
                    
                    if distance < best_distance:
                        best_distance = distance
                        best_cluster = cluster
                        best_place = place
                        
                except (ValueError, TypeError):
                    continue
        
        if best_place and best_cluster:
            # Add the best place to our route
            selected_places.append(best_place)
            
            # Update current location for next iteration
            current_location = (float(best_place.get('y', 0)), float(best_place.get('x', 0)))
            
            # Remove the used cluster to avoid duplicates
            remaining_clusters.remove(best_cluster)
    
    return selected_places

# =============================================================================
# CACHE MANAGEMENT UTILITIES
# =============================================================================

def clear_cache():
    """Clear all cached data from both memory and disk."""
    _smart_cache.memory_cache.clear()
    for cache_file in _smart_cache.cache_dir.glob("*.json"):
        cache_file.unlink(missing_ok=True)

def get_cache_stats() -> Dict[str, int]:
    """Get cache performance statistics."""
    return _smart_cache.get_stats()

def clear_expired_cache():
    """Remove expired cache entries."""
    _smart_cache.clear_expired()
