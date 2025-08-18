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

Note: This module requires a valid Kakao Map API key to function properly.
"""

import requests
from secure.crypto_utils import get_kakao_map_api_key

def get_location_coordinates(location_name: str):
    """
    Return coordinates for the first Kakao Map search result.
    
    This function takes a human-readable location name (e.g., "홍대입구", "Gangnam Station")
    and returns the corresponding latitude and longitude coordinates. It uses the
    Kakao Map API to perform the search and extracts coordinates from the first result.
    
    The old implementation prompted the user to select from search results.
    For automated scripts like "main.py" we instead simply return the
    coordinates of the first result. "None" is returned if the query yields
    no results or if the request fails.
    
    Args:
        location_name (str): Name of the location to search for.
                           Can be in Korean or English.
                           Examples: "홍대입구", "Gangnam", "이태원", "Itaewon"
    
    Returns:
        tuple: (latitude, longitude) coordinates as floats, or None on failure.
               Coordinates are returned as (y, x) from Kakao API, which corresponds
               to (latitude, longitude) in standard geographic notation.
    
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
    # Note: The API key is encrypted and needs to be decrypted using the private key.
    # This ensures the API key is not exposed in plain text in the code.
    api_key = get_kakao_map_api_key()
    
    # Kakao Map API endpoint for keyword-based location search
    # This endpoint searches for places based on text queries
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    
    # Set up the request headers with the API key
    # Kakao API requires the key to be prefixed with "KakaoAK "
    headers = {"Authorization": f"KakaoAK {api_key}"}
    
    # Set up the search parameters
    # - query: The location name to search for
    # - size: Number of results to return (we only need the first one)
    params = {"query": location_name, "size": 1}
    
    try:
        # Make the HTTP GET request to the Kakao Map API
        response = requests.get(url, headers=headers, params=params)
        
        # Raise an exception for HTTP error status codes (4xx, 5xx)
        # This helps identify API issues, authentication problems, etc.
        response.raise_for_status()
        
        # Parse the JSON response from the API
        data = response.json()
        
        # Extract the documents array from the response
        # This contains the actual location results
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
        # This includes:
        # - HTTP errors (4xx, 5xx status codes)
        # - Network connection issues
        # - JSON parsing errors
        # - API key authentication failures
        # - Rate limiting or quota exceeded
        
        # On any failure return None so callers can fall back to defaults
        # This ensures the application continues to function even if the
        # location service is temporarily unavailable
        return None
