"""
Location Autocomplete Suggestion Engine

This module provides location autocomplete functionality using the Kakao Map API.
It takes partial location queries and returns a list of suggested locations
with their coordinates, enabling real-time search suggestions in the UI.

The module serves as a standalone script that can be called from external
applications (like the C# frontend) to provide location suggestions as
users type their location queries.

Key Features:
- Real-time location suggestions based on partial input
- Coordinate extraction for suggested locations
- JSON output format for easy integration
- Error handling with graceful fallbacks
"""

import sys
import json
import os
import io

# =============================================================================
# ENCODING SETUP
# =============================================================================
# Ensure proper UTF-8 encoding for Korean text output
# This is crucial for handling Korean location names correctly
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# =============================================================================
# PATH SETUP
# =============================================================================
# Add project root to Python path so we can import from other modules
# This allows us to use the kakao_api module for location autocomplete
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

# Import the Kakao API autocomplete function
from data.api_clients.kakao_api import autocomplete_location

def suggest_locations(query):
    """
    Generate location suggestions based on a partial query string.
    
    This function takes a partial location name (e.g., "홍대", "Gang") and
    returns a list of suggested locations that match the query. Each suggestion
    includes the full location name and its coordinates for immediate use.
    
    The function is designed to be called from external applications and
    outputs results in JSON format for easy parsing.
    
    Args:
        query (str): Partial location query string to search for
                    Examples: "홍대", "Gang", "이태", "Ita"
    
    Returns:
        None: Outputs results directly to stdout in JSON format
        
    Output Format:
        JSON array of location objects, each containing:
        - name: Full location name
        - longitude: Longitude coordinate
        - latitude: Latitude coordinate
        
    Example Output:
        [
            {
                "name": "홍대입구역",
                "longitude": 126.9237,
                "latitude": 37.5563
            },
            {
                "name": "홍대거리",
                "longitude": 126.9245,
                "latitude": 37.5571
            }
        ]
    """
    try:
        # Call the Kakao API autocomplete service with the query
        # This returns a list of potential location matches
        results = autocomplete_location(query)
        
        # Initialize the suggestions list to store processed results
        suggestions = []

        # Process each place result from the API response
        for place in results.get("documents", []):
            # Extract the essential information from each place
            name = place.get("place_name")      # Full location name
            x = place.get("x")                  # Longitude (Kakao API format)
            y = place.get("y")                  # Latitude (Kakao API format)
            
            # Only include suggestions that have all required data
            if name and x and y:
                suggestions.append({
                    "name": name,
                    "longitude": float(x),      # Convert to float for precision
                    "latitude": float(y)        # Convert to float for precision
                })

        # Output the suggestions as JSON to stdout
        # This allows external applications to capture the results
        print(json.dumps(suggestions, ensure_ascii=False))
        
    except Exception as e:
        # If any error occurs during the suggestion process:
        # - API failures
        # - Network issues
        # - Data parsing errors
        # - Authentication problems
        
        # Return an empty array to indicate no suggestions available
        # This ensures the calling application doesn't crash
        print(json.dumps([], ensure_ascii=False))

# =============================================================================
# SCRIPT EXECUTION ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    # Check if a query argument was provided
    if len(sys.argv) < 2:
        # No query provided, return empty suggestions
        print(json.dumps([], ensure_ascii=False))
    else:
        # Extract the query from command line arguments
        # The first argument (sys.argv[0]) is the script name
        # The second argument (sys.argv[1]) is the location query
        query = sys.argv[1]
        
        # Generate and output location suggestions for the query
        suggest_locations(query)
