"""
Place Management Module

This module handles place type selection, place collection, and place processing
for trip planning and itinerary generation.
"""

import random
import time
import sys
from typing import List, Dict
from constants import USER_SELECTABLE_PLACE_TYPES, COMPANION_PLACE_TYPES, VARIETY_PLACE_TYPES, DEFAULT_PLACE_TYPES
from data.api_clients.kakao_api import search_multiple_place_types

def _log(level: str, message: str):
    """Simple logging function."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {level} - {message}", file=sys.stderr)

class PlaceManager:
    """
    Manages place type selection and place collection for trip planning.
    
    This class handles:
    - Intelligent place type selection based on companion type
    - Batch API calls to collect place recommendations
    - Place reduction and candidate selection
    - Integration with caching and rate limiting
    """
    
    def __init__(self, rate_limiter, cache_manager):
        """
        Initialize the place manager.
        
        Args:
            rate_limiter: Rate limiter instance for API calls
            cache_manager: Cache manager instance for results
        """
        self.rate_limiter = rate_limiter
        self.cache_manager = cache_manager
        self.selected_types = []
        self.best_places = {}
    
    def select_place_types(self, user_selected_types: List[str] = None, companion_type: str = "Solo"):
        """
        Select appropriate place types based on companion type and user preferences.
        
        Args:
            user_selected_types: User's manually selected place types
            companion_type: Type of outing (Solo, Couple, Friends, Family)
        """
        # Start with user-selected types as highest priority
        if user_selected_types:
            self.selected_types = user_selected_types.copy()
        else:
            self.selected_types = []
        
        # Get companion-specific place type recommendations
        companion_places = COMPANION_PLACE_TYPES.get(companion_type.lower(), [])
        
        # Add companion types for variety
        max_companion_types = 3
        if len(companion_places) > 0:
            available_companion_types = [t for t in companion_places if t not in self.selected_types]
            if available_companion_types:
                num_to_add = min(max_companion_types, len(available_companion_types))
                additional_types = available_companion_types[:num_to_add]
                self.selected_types.extend(additional_types)
        
        # Add variety types for rich experience
        available_variety = [t for t in VARIETY_PLACE_TYPES if t not in self.selected_types]
        if available_variety:
            num_variety = min(2, len(available_variety))
            selected_variety = available_variety[:num_variety]
            self.selected_types.extend(selected_variety)
        
        # Ensure we have at least 6 types for rich variety
        if len(self.selected_types) < 6:
            for default_type in DEFAULT_PLACE_TYPES:
                if default_type not in self.selected_types and len(self.selected_types) < 6:
                    self.selected_types.append(default_type)
        
        # Limit total types to prevent overwhelming the search
        if len(self.selected_types) > 10:
            user_types = [t for t in self.selected_types if t in (user_selected_types or [])]
            other_types = [t for t in self.selected_types if t not in user_types]
            self.selected_types = user_types + other_types[:7]
    
    def collect_places(self, start_location: tuple, max_distance_km: float, location_name: str):
        """
        Collect place recommendations using batch API calls.
        
        Args:
            start_location: Starting coordinates (lat, lng)
            max_distance_km: Maximum search radius in kilometers
            location_name: Human-readable location name for caching
        """
        # Check cache first
        cache_key = self.cache_manager._generate_cache_key(
            location_name, self.selected_types, start_location, max_distance_km
        )
        cached_results = self.cache_manager.get_cached_results(cache_key)
        
        if cached_results:
            _log("SUCCESS", f"Using cached results for location {location_name}")
            self.best_places = cached_results
            return
        
        # Make batch API calls
        all_places = []
        batch_size = 3
        place_type_batches = [self.selected_types[i:i + batch_size] 
                            for i in range(0, len(self.selected_types), batch_size)]
        
        for batch_idx, place_types_batch in enumerate(place_type_batches):
            try:
                self.rate_limiter.wait_if_needed()
                
                # Make a single API call for multiple place types
                search_result = search_multiple_place_types(
                    place_types_batch,
                    start_location[0], 
                    start_location[1], 
                    int(max_distance_km * 1000), 
                    15  # Get 15 places per type
                )
                
                # Process results for each place type in the batch
                for place_type in place_types_batch:
                    if place_type in search_result:
                        places = search_result[place_type]
                        # Add place type information to each place
                        for place in places:
                            place['place_type'] = place_type
                        
                        all_places.extend(places)
                    else:
                        _log("WARNING", f"No results found for {place_type}")
            
                # Add small delay between batches to respect API rate limits
                if batch_idx < len(place_type_batches) - 1:
                    time.sleep(0.2)  # 200ms delay between batches
            
            except Exception as e:
                _log("WARNING", f"Failed to search for batch {place_types_batch}: {e}")
                continue
        
        if not all_places:
            _log("ERROR", "No places found for any type")
            return
        
        # Reduce to 20 candidates ensuring variety
        self.best_places = self._reduce_to_20_candidates(all_places)
        
        # Cache the results for future use
        self.cache_manager.cache_results(cache_key, self.best_places)
    
    def _reduce_to_20_candidates(self, all_places: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Reduce the list of places to 20 candidates using random selection.
        
        Args:
            all_places: List of all places found
            
        Returns:
            Dictionary with place types as keys and reduced lists as values
        """
        if not all_places:
            return {}
        
        # Shuffle ALL places randomly for true randomness
        random.shuffle(all_places)
        
        # Take the first 20 places from the shuffled list
        selected_places = all_places[:20]
        
        # Group the selected places by type for the return format
        reduced_places = {}
        for place in selected_places:
            place_type = place.get('place_type', 'Unknown')
            if place_type not in reduced_places:
                reduced_places[place_type] = []
            reduced_places[place_type].append(place)
        
        return reduced_places
