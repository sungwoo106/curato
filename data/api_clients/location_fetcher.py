"""
Location Coordinate Fetcher

This module provides functionality to convert location names into geographic coordinates
using the Kakao Map API. It serves as the bridge between user-friendly location names
and the precise coordinates needed for distance calculations and place searches.

The function handles:
- Location name queries in both Korean and English
- API key management and security
- Error handling and fallback behavior
- Coordinate extraction from API responses
- Batch processing for multiple locations
- Smart caching integration

Note: This module requires a valid Kakao Map API key to function properly.
"""

import requests
import time
from typing import List, Tuple, Optional, Dict
from secure.crypto_utils import get_kakao_map_api_key

def get_location_coordinates(location_name: str):
    """
    Return coordinates for the first Kakao Map search result.
    
    This function takes a human-readable location name (e.g., "홍대입구", "Gangnam Station")
    and returns the corresponding latitude and longitude coordinates. It uses the
    Kakao Map API to perform the search and extracts coordinates from the first result.
    
    Args:
        location_name (str): Name of the location to search for.
                           Can be in Korean or English.
                           Examples: "홍대입구", "Gangnam", "이태원", "Itaewon"
    
    Returns:
        Optional[Tuple[float, float]]: (latitude, longitude) coordinates as floats, 
                                      or None on failure.
                                      Coordinates are returned as (y, x) from Kakao API, 
                                      which corresponds to (latitude, longitude) in 
                                      standard geographic notation.
    
    Raises:
        None: All exceptions are caught and handled gracefully, returning None instead.
    
    Example:
        >>> get_location_coordinates("홍대입구")
        (37.5563, 126.9237)
        
        >>> get_location_coordinates("Gangnam Station")
        (37.4980, 127.0276)
        
        >>> get_location_coordinates("nonexistent_location")
        None
    """
    # Fetch the API key from secure storage
    api_key = get_kakao_map_api_key()
    
    # Kakao Map API endpoint for keyword-based location search
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    
    # Set up the request headers with the API key
    headers = {"Authorization": f"KakaoAK {api_key}"}
    
    # Set up the search parameters
    params = {"query": location_name, "size": 1}
    
    try:
        # Make the HTTP GET request to the Kakao Map API
        response = requests.get(url, headers=headers, params=params)
        
        # Raise an exception for HTTP error status codes (4xx, 5xx)
        response.raise_for_status()
        
        # Parse the JSON response from the API
        data = response.json()
        
        # Extract the documents array from the response
        documents = data.get("documents", [])
        
        # Check if any results were returned
        if not documents:
            # No locations found for the given query
            return None
        
        # Get the first (and only) result from the search
        first = documents[0]
        
        # Extract and convert coordinates to float values
        # Kakao API returns coordinates as strings, so we convert them
        # Note: Kakao API uses (y, x) format which corresponds to (latitude, longitude)
        return float(first["y"]), float(first["x"])
        
    except Exception:
        # Catch all exceptions to ensure graceful failure
        # On any failure return None so callers can fall back to defaults
        return None

def get_multiple_location_coordinates(location_names: List[str], 
                                    delay_between_requests: float = 0.1) -> Dict[str, Optional[Tuple[float, float]]]:
    """
    Get coordinates for multiple locations with batch processing and rate limiting.
    
    This function efficiently processes multiple location queries while respecting
    API rate limits and providing comprehensive results. It's useful for bulk
    location processing in itinerary planning.
    
    Args:
        location_names (List[str]): List of location names to search for
        delay_between_requests (float): Delay between API requests in seconds (default: 0.1)
    
    Returns:
        Dict[str, Optional[Tuple[float, float]]]: Dictionary mapping location names to coordinates
                                                 Failed lookups return None
    
    Example:
        >>> locations = ["홍대입구", "강남역", "이태원"]
        >>> results = get_multiple_location_coordinates(locations)
        >>> print(f"Found coordinates for {len([v for v in results.values() if v])} locations")
        Found coordinates for 3 locations
    """
    results = {}
    
    for location_name in location_names:
        try:
            # Get coordinates for this location
            coords = get_location_coordinates(location_name)
            results[location_name] = coords
            
            # Add delay between requests to respect API rate limits
            if delay_between_requests > 0:
                time.sleep(delay_between_requests)
                
        except Exception as e:
            # If one location fails, continue with others
            print(f"Warning: Failed to get coordinates for '{location_name}': {e}")
            results[location_name] = None
    
    return results

def validate_coordinates(lat: float, lng: float) -> bool:
    """
    Validate that coordinates are within reasonable bounds for Korea.
    
    Args:
        lat (float): Latitude value
        lng (float): Longitude value
    
    Returns:
        bool: True if coordinates are valid for Korea, False otherwise
    """
    # Korea's approximate coordinate bounds
    KOREA_BOUNDS = {
        'lat_min': 33.0,   # Southernmost point
        'lat_max': 38.6,   # Northernmost point
        'lng_min': 124.5,  # Westernmost point
        'lng_max': 132.0   # Easternmost point
    }
    
    return (KOREA_BOUNDS['lat_min'] <= lat <= KOREA_BOUNDS['lat_max'] and
            KOREA_BOUNDS['lng_min'] <= lng <= KOREA_BOUNDS['lng_max'])

def get_location_with_fallback(location_name: str, fallback_coordinates: Tuple[float, float]) -> Tuple[float, float]:
    """
    Get location coordinates with fallback to default coordinates.
    
    This function attempts to resolve the given location name, but falls back
    to the provided default coordinates if the lookup fails. This ensures
    the application always has valid coordinates to work with.
    
    Args:
        location_name (str): Name of the location to search for
        fallback_coordinates (Tuple[float, float]): Default coordinates to use if lookup fails
    
    Returns:
        Tuple[float, float]: Resolved coordinates or fallback coordinates
    
    Example:
        >>> coords = get_location_with_fallback("홍대입구", (37.5563, 126.9237))
        >>> print(f"Using coordinates: {coords}")
        Using coordinates: (37.5563, 126.9237)
    """
    coords = get_location_coordinates(location_name)
    
    if coords and validate_coordinates(*coords):
        return coords
    else:
        print(f"Location lookup failed for '{location_name}', using fallback coordinates")
        return fallback_coordinates
