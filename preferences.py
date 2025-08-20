"""
Preferences and Itinerary Generation Engine

This module contains the core Preferences class that manages user preferences and
generates personalized itineraries. It orchestrates the entire workflow from
user input to final itinerary generation, including:
- Managing companion type, budget, timing, and location preferences
- Selecting appropriate place types based on companion type
- Collecting place recommendations from external APIs
- Generating route plans and emotional storytelling content
- Supporting real-time progress updates during LLM generation

The class serves as the main interface between the UI layer and the backend
AI models and external services.
"""

from core.prompts import build_phi_location_prompt, build_qwen_itinerary_prompt
from models.genie_runner import GenieRunner
from data.api_clients.kakao_api import format_kakao_places_for_prompt, search_multiple_place_types
from constants import USER_SELECTABLE_PLACE_TYPES, COMPANION_PLACE_TYPES, COMPANION_TYPES, BUDGET, LOCATION, MAX_DISTANCE_KM, STARTING_TIME
import random
import json
import sys
import time
from typing import Tuple, List, Dict, Optional
from collections import deque

class RateLimiter:
    """
    Rate limiter to prevent excessive API calls and respect Kakao API rate limits.
    
    Kakao API limits:
    - Daily: 100,000 requests
    - Monthly: 3,000,000 requests
    - Recommended: Max 100 requests per minute
    """
    
    def __init__(self, max_calls: int = 100, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_calls (int): Maximum calls allowed in the time window
            time_window (int): Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()
    
    def can_call(self) -> bool:
        """
        Check if an API call can be made.
        
        Returns:
            bool: True if call is allowed, False otherwise
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
        """
        Wait if necessary to respect rate limits.
        """
        if not self.can_call():
            # Calculate how long to wait
            oldest_call = self.calls[0]
            wait_time = self.time_window - (time.time() - oldest_call)
            if wait_time > 0:
                print(f"⏳ Rate limit reached, waiting {wait_time:.1f} seconds...", file=sys.stderr)
                time.sleep(wait_time)
    
    def get_status(self) -> dict:
        """
        Get current rate limiter status.
        
        Returns:
            dict: Status information
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

class Preferences:
    """
    Main class for managing user preferences and generating personalized itineraries.
    
    This class encapsulates all the logic needed to create a customized day plan
    based on user preferences including companion type, budget, timing, and location.
    It coordinates between different services (Kakao API, AI models) to generate
    coherent and enjoyable itineraries with real-time progress updates.
    """
    
    def __init__(self,
                 companion_type=COMPANION_TYPES[0],
                 budget=BUDGET[0],
                 starting_time=STARTING_TIME,
                 max_distance_km=MAX_DISTANCE_KM,
                 start_location=LOCATION,
                 location_name="Seoul",
                 progress_callback=None):
        """
        Initialize a new Preferences instance with user preferences.
        
        Args:
            companion_type (str): Type of outing (Solo, Couple, Friends, Family)
            budget (str): Budget level (low, medium, high)
            starting_time (int): Starting time in 24-hour format (0-23)
            max_distance_km (int): Maximum search radius in kilometers
            start_location (tuple): Starting coordinates (latitude, longitude)
            location_name (str): Human-readable location name (e.g., "Seongsu", "Gangnam", "Seoul")
            progress_callback (callable): Optional callback for progress updates
        """
        # Core user preferences
        self.companion_type = companion_type
        self.budget = budget
        self.starting_time = starting_time
        self.max_distance_km = max_distance_km
        self.start_location = start_location
        self.location_name = location_name
        self.progress_callback = progress_callback
        
        # Generated data and recommendations
        self.selected_types = []        # Place types selected for this itinerary
        self.best_places = {}           # Dictionary of place type -> list of places
        self.recommendations_json = []  # Formatted recommendations for AI prompts
        
        # Initialize rate limiter for API calls
        self.rate_limiter = RateLimiter(max_calls=100, time_window=60)  # 100 calls per minute

    # =============================================================================
    # SETTER METHODS FOR UPDATING PREFERENCES
    # =============================================================================
    
    def set_start_location(self, start_location: tuple):
        """Update the starting location coordinates."""
        self.start_location = start_location

    def set_companion_type(self, companion_type: str):
        """Update the companion type for the outing."""
        self.companion_type = companion_type

    def set_budget(self, budget: str):
        """Update the budget level for the outing."""
        self.budget = budget

    def set_starting_time(self, starting_time: int):
        """Update the starting time for the outing."""
        self.starting_time = starting_time

    def set_max_distance_km(self, max_distance_km: int):
        """Update the maximum search distance in kilometers."""
        self.max_distance_km = max_distance_km

    # =============================================================================
    # PLACE TYPE SELECTION LOGIC
    # =============================================================================
    
    def select_place_types(self, user_selected_types=None):
        """
        Select appropriate place types based on companion type and user preferences.
        
        This method intelligently combines:
        1. User manually selected types (highest priority)
        2. Companion-specific recommendations (expanded selection)
        3. Additional variety types for rich experience
        4. Ensures variety while respecting user choices
        
        Args:
            user_selected_types (list, optional): User's manually selected place types
        """
        # Start with user-selected types as highest priority
        if user_selected_types:
            self.selected_types = user_selected_types.copy()
            print(f"🔍 User selected place types: {self.selected_types}", file=sys.stderr)
        else:
            self.selected_types = []
        
        # Get companion-specific place type recommendations
        companion_places = COMPANION_PLACE_TYPES.get(self.companion_type.lower(), [])
        
        # Add companion types for variety
        max_companion_types = 3
        if len(companion_places) > 0:
            available_companion_types = [t for t in companion_places if t not in self.selected_types]
            if available_companion_types:
                num_to_add = min(max_companion_types, len(available_companion_types))
                additional_types = available_companion_types[:num_to_add]
                self.selected_types.extend(additional_types)
                print(f"🔍 Added {len(additional_types)} companion-specific types: {additional_types}", file=sys.stderr)
        
        # Add variety types for rich experience
        from constants import VARIETY_PLACE_TYPES
        variety_types = VARIETY_PLACE_TYPES
        
        available_variety = [t for t in variety_types if t not in self.selected_types]
        if available_variety:
            num_variety = min(2, len(available_variety))
            selected_variety = available_variety[:num_variety]
            self.selected_types.extend(selected_variety)
            print(f"🔍 Added {len(selected_variety)} variety types: {selected_variety}", file=sys.stderr)
        
        # Ensure we have at least 6 types for rich variety
        if len(self.selected_types) < 6:
            from constants import DEFAULT_PLACE_TYPES
            for default_type in DEFAULT_PLACE_TYPES:
                if default_type not in self.selected_types and len(self.selected_types) < 6:
                    self.selected_types.append(default_type)
            print(f"🔍 Added default types to ensure minimum variety: {self.selected_types}", file=sys.stderr)
        
        # Limit total types to prevent overwhelming the search
        if len(self.selected_types) > 10:
            user_types = [t for t in self.selected_types if t in (user_selected_types or [])]
            other_types = [t for t in self.selected_types if t not in user_types]
            self.selected_types = user_types + other_types[:7]
            print(f"🔍 Limited total types to prevent search overload: {self.selected_types}", file=sys.stderr)
        
        print(f"🔍 Final selected place types: {self.selected_types} (Total: {len(self.selected_types)})", file=sys.stderr)

    # =============================================================================
    # SIMPLIFIED PLACE RECOMMENDATION COLLECTION
    # =============================================================================
    
    def collect_best_place(self):
        """
        Collect place recommendations using an optimized approach with batch API calls.
        
        This method:
        1. Makes batch API calls to reduce the number of requests
        2. Gets 10-15 places from each place type within walking distance
        3. Combines all places into a single list
        4. Reduces to 20 candidates ensuring variety of place types
        5. Implements smart caching to minimize API calls
        
        Returns:
            dict: Dictionary where keys are place types and values are lists of places
        """
        print(f"🔍 Collecting places for types: {self.selected_types}", file=sys.stderr)
        
        # Check if we have cached results for this location and place types
        cache_key = self._generate_cache_key()
        cached_results = self._get_cached_results(cache_key)
        
        if cached_results:
            print(f"✅ Using cached results for location {self.location_name}", file=sys.stderr)
            self.best_places = cached_results
            return
        
        # Make batch API calls instead of individual calls for each type
        all_places = []
        
        # Group place types into batches to minimize API calls
        # Kakao API can handle multiple place types in a single request
        batch_size = 3  # Process 3 place types per batch
        place_type_batches = [self.selected_types[i:i + batch_size] 
                            for i in range(0, len(self.selected_types), batch_size)]
        
        print(f"🔍 Processing {len(self.selected_types)} place types in {len(place_type_batches)} batches", file=sys.stderr)
        
        for batch_idx, place_types_batch in enumerate(place_type_batches):
            try:
                print(f"🔍 Processing batch {batch_idx + 1}: {place_types_batch}", file=sys.stderr)
                
                # Check rate limits before making API call
                self.rate_limiter.wait_if_needed()
                
                # Make a single API call for multiple place types
                search_result = search_multiple_place_types(
                    place_types_batch,  # Pass multiple types at once
                    self.start_location[0], 
                    self.start_location[1], 
                    int(self.max_distance_km * 1000), 
                    15  # Get 15 places per type
                )
                
                # Log rate limiter status
                status = self.rate_limiter.get_status()
                print(f"📊 Rate limiter status: {status['current_calls']}/{status['max_calls']} calls in {status['time_window']}s window", file=sys.stderr)
                
                # Process results for each place type in the batch
                for place_type in place_types_batch:
                    if place_type in search_result:
                        places = search_result[place_type]
                        # Add place type information to each place
                        for place in places:
                            place['place_type'] = place_type
                        
                        all_places.extend(places)
                        print(f"🔍 Found {len(places)} places for {place_type}", file=sys.stderr)
                        
                        # Debug: show first place structure
                        if places:
                            print(f"🔍 Sample place structure: {list(places[0].keys())}", file=sys.stderr)
                    else:
                        print(f"⚠️ No results found for {place_type}", file=sys.stderr)
                
                # Add small delay between batches to respect API rate limits
                if batch_idx < len(place_type_batches) - 1:
                    time.sleep(0.2)  # 200ms delay between batches
                
            except Exception as e:
                print(f"Warning: Failed to search for batch {place_types_batch}: {e}", file=sys.stderr)
                continue
        
        if not all_places:
            print("❌ No places found for any type", file=sys.stderr)
            return
        
        print(f"🔍 Total places found: {len(all_places)}", file=sys.stderr)
        
        # Reduce to 20 candidates ensuring variety
        self.best_places = self._reduce_to_20_candidates(all_places)
        
        print(f"🔍 Reduced to {len(self.best_places)} place types with variety", file=sys.stderr)
        for place_type, places in self.best_places.items():
            print(f"🔍 {place_type}: {len(places)} places", file=sys.stderr)
        
        # Cache the results for future use
        self._cache_results(cache_key, self.best_places)

    def _generate_cache_key(self) -> str:
        """
        Generate a cache key based on location, place types, and search parameters.
        
        Returns:
            str: Unique cache key for this search
        """
        # Sort place types for consistent cache keys
        sorted_types = sorted(self.selected_types)
        types_str = "_".join(sorted_types)
        
        # Round coordinates to 2 decimal places (~1km precision)
        # This provides better cache hit rates while maintaining reasonable accuracy
        rounded_lat = round(self.start_location[0], 2)
        rounded_lng = round(self.start_location[1], 2)
        
        # Include search radius in cache key
        radius_m = int(self.max_distance_km * 1000)
        
        cache_key = f"{self.location_name}_{types_str}_{rounded_lat}_{rounded_lng}_{radius_m}"
        return cache_key

    def _get_cached_results(self, cache_key: str) -> Dict[str, List[Dict]]:
        """
        Retrieve cached results if available and not expired.
        
        Args:
            cache_key (str): Cache key for the search
            
        Returns:
            Dict[str, List[Dict]]: Cached results or None if not found/expired
        """
        try:
            # Simple in-memory cache with TTL
            if not hasattr(self, '_cache'):
                self._cache = {}
                self._cache_timestamps = {}
            
            # Check if cache entry exists and is not expired
            if cache_key in self._cache:
                timestamp = self._cache_timestamps.get(cache_key, 0)
                current_time = time.time()
                cache_ttl = 3600  # 1 hour cache TTL
                
                if current_time - timestamp < cache_ttl:
                    print(f"✅ Cache hit for key: {cache_key[:50]}...", file=sys.stderr)
                    return self._cache[cache_key]
                else:
                    # Cache expired, remove it
                    print(f"🔄 Cache expired for key: {cache_key[:50]}...", file=sys.stderr)
                    del self._cache[cache_key]
                    del self._cache_timestamps[cache_key]
            
            return None
            
        except Exception as e:
            print(f"⚠️ Cache retrieval failed: {e}", file=sys.stderr)
            return None

    def _cache_results(self, cache_key: str, results: Dict[str, List[Dict]]):
        """
        Cache the search results for future use.
        
        Args:
            cache_key (str): Cache key for the search
            results (Dict[str, List[Dict]]): Results to cache
        """
        try:
            if not hasattr(self, '_cache'):
                self._cache = {}
                self._cache_timestamps = {}
            
            # Store results and timestamp
            self._cache[cache_key] = results
            self._cache_timestamps[cache_key] = time.time()
            
            print(f"💾 Cached results for key: {cache_key[:50]}...", file=sys.stderr)
            
            # Implement cache size limit to prevent memory issues
            max_cache_size = 50
            if len(self._cache) > max_cache_size:
                self._cleanup_cache()
                
        except Exception as e:
            print(f"⚠️ Caching failed: {e}", file=sys.stderr)

    def _cleanup_cache(self):
        """
        Clean up old cache entries to prevent memory issues.
        """
        try:
            if not hasattr(self, '_cache') or not hasattr(self, '_cache_timestamps'):
                return
            
            # Remove oldest entries
            current_time = time.time()
            cache_ttl = 3600  # 1 hour
            
            expired_keys = []
            for key, timestamp in self._cache_timestamps.items():
                if current_time - timestamp > cache_ttl:
                    expired_keys.append(key)
            
            # Remove expired entries
            for key in expired_keys:
                del self._cache[key]
                del self._cache_timestamps[key]
            
            # If still too many entries, remove oldest ones
            if len(self._cache) > 50:
                # Sort by timestamp and keep only the 50 most recent
                sorted_keys = sorted(self._cache_timestamps.items(), key=lambda x: x[1], reverse=True)
                keys_to_keep = [key for key, _ in sorted_keys[:50]]
                
                keys_to_remove = [key for key in self._cache.keys() if key not in keys_to_keep]
                for key in keys_to_remove:
                    del self._cache[key]
                    del self._cache_timestamps[key]
                
                print(f"🧹 Cleaned up cache, removed {len(keys_to_remove)} old entries", file=sys.stderr)
                
        except Exception as e:
            print(f"⚠️ Cache cleanup failed: {e}", file=sys.stderr)

    def get_performance_stats(self) -> dict:
        """
        Get comprehensive performance statistics for monitoring and optimization.
        
        Returns:
            dict: Performance statistics including cache hits, API calls, and rate limiting
        """
        stats = {
            "cache_stats": {},
            "rate_limiter_stats": {},
            "api_call_efficiency": {}
        }
        
        # Cache statistics
        if hasattr(self, '_cache'):
            stats["cache_stats"] = {
                "total_cached_entries": len(self._cache),
                "cache_size_limit": 50,
                "cache_utilization_percent": (len(self._cache) / 50) * 100
            }
            
            # Calculate cache hit rate if we have timestamps
            if hasattr(self, '_cache_timestamps'):
                current_time = time.time()
                expired_entries = sum(1 for ts in self._cache_timestamps.values() 
                                   if current_time - ts > 3600)
                stats["cache_stats"]["expired_entries"] = expired_entries
                stats["cache_stats"]["active_entries"] = len(self._cache) - expired_entries
        else:
            stats["cache_stats"] = {"status": "Cache not initialized"}
        
        # Rate limiter statistics
        if hasattr(self, 'rate_limiter'):
            rate_stats = self.rate_limiter.get_status()
            stats["rate_limiter_stats"] = {
                "current_calls": rate_stats["current_calls"],
                "max_calls": rate_stats["max_calls"],
                "calls_remaining": rate_stats["calls_remaining"],
                "utilization_percent": (rate_stats["current_calls"] / rate_stats["max_calls"]) * 100,
                "time_window_seconds": rate_stats["time_window"]
            }
        else:
            stats["rate_limiter_stats"] = {"status": "Rate limiter not initialized"}
        
        # API call efficiency
        if hasattr(self, 'selected_types'):
            total_place_types = len(self.selected_types)
            batch_size = 3
            total_batches = (total_place_types + batch_size - 1) // batch_size
            
            stats["api_call_efficiency"] = {
                "total_place_types": total_place_types,
                "batch_size": batch_size,
                "total_batches": total_batches,
                "api_calls_per_itinerary": total_batches,
                "improvement_from_individual": f"{((total_place_types - total_batches) / total_place_types) * 100:.1f}%"
            }
        
        return stats

    def clear_cache(self):
        """
        Clear all cached results to force fresh API calls.
        Useful for testing or when you want to refresh data.
        """
        if hasattr(self, '_cache'):
            cache_size = len(self._cache)
            self._cache.clear()
            self._cache_timestamps.clear()
            print(f"🧹 Cleared {cache_size} cached entries", file=sys.stderr)
        else:
            print("ℹ️ No cache to clear", file=sys.stderr)

    def get_cache_status(self) -> dict:
        """
        Get detailed cache status information.
        
        Returns:
            dict: Cache status including size, utilization, and entry details
        """
        if not hasattr(self, '_cache'):
            return {"status": "Cache not initialized"}
        
        current_time = time.time()
        cache_ttl = 3600  # 1 hour
        
        # Analyze cache entries
        active_entries = 0
        expired_entries = 0
        entry_details = []
        
        for key, timestamp in self._cache_timestamps.items():
            age = current_time - timestamp
            if age < cache_ttl:
                active_entries += 1
                entry_details.append({
                    "key": key[:50] + "..." if len(key) > 50 else key,
                    "age_seconds": int(age),
                    "status": "active"
                })
            else:
                expired_entries += 1
                entry_details.append({
                    "key": key[:50] + "..." if len(key) > 50 else key,
                    "age_seconds": int(age),
                    "status": "expired"
                })
        
        return {
            "total_entries": len(self._cache),
            "active_entries": active_entries,
            "expired_entries": expired_entries,
            "cache_utilization_percent": (len(self._cache) / 50) * 100,
            "cache_size_limit": 50,
            "cache_ttl_seconds": cache_ttl,
            "entry_details": entry_details[:10]  # Show first 10 entries
        }

    def _reduce_to_20_candidates(self, all_places: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Reduce the list of places to 20 candidates ensuring variety of place types.
        
        Args:
            all_places (List[Dict]): List of all places found
            
        Returns:
            Dict[str, List[Dict]]: Dictionary with place types as keys and reduced lists as values
        """
        # Group places by type
        places_by_type = {}
        for place in all_places:
            place_type = place.get('place_type', 'Unknown')
            if place_type not in places_by_type:
                places_by_type[place_type] = []
            places_by_type[place_type].append(place)
        
        # Calculate how many places to take from each type to get 20 total
        total_types = len(places_by_type)
        places_per_type = max(1, 20 // total_types)  # At least 1 per type
        
        # Select places from each type
        reduced_places = {}
        total_selected = 0
        
        for place_type, places in places_by_type.items():
            # Take up to places_per_type from each type
            selected = places[:places_per_type]
            reduced_places[place_type] = selected
            total_selected += len(selected)
            
            # If we have more than 20, stop
            if total_selected >= 20:
                break
        
        # If we have fewer than 20, add more from types with more places
        if total_selected < 20:
            remaining_needed = 20 - total_selected
            
            # Sort types by number of available places (descending)
            sorted_types = sorted(places_by_type.items(), key=lambda x: len(x[1]), reverse=True)
            
            for place_type, places in sorted_types:
                if total_selected >= 20:
                    break
                    
                # How many more we can take from this type
                already_taken = len(reduced_places.get(place_type, []))
                available = len(places) - already_taken
                can_take = min(available, remaining_needed)
                
                if can_take > 0:
                    # Take additional places
                    additional = places[already_taken:already_taken + can_take]
                    reduced_places[place_type].extend(additional)
                    total_selected += can_take
                    remaining_needed -= can_take
        
        print(f"✅ Reduced to {total_selected} total candidates across {len(reduced_places)} place types", file=sys.stderr)
        return reduced_places

    def format_recommendations(self):
        """
        Format the collected place recommendations for use in AI prompts.
        
        This method converts the raw place data into a format that can be
        easily consumed by the AI models for generating itineraries.
        
        Returns:
            list: Formatted recommendations ready for AI prompt generation
        """
        # Use the existing format_kakao_places_for_prompt function which properly
        # converts Kakao API response format to our standardized format
        self.recommendations_json = format_kakao_places_for_prompt(self.best_places)
        return self.recommendations_json

    # =============================================================================
    # SIMPLIFIED ITINERARY GENERATION WORKFLOW
    # =============================================================================
    
    def run_route_planner(self):
        """
        Generate a route plan using the Phi model with simplified logic.
        
        This method:
        1. Collects place recommendations (10-15 per type, reduced to 20 total)
        2. Builds a simple prompt for the Phi model
        3. Asks Phi to randomly select 4-5 places from the 20 candidates
        4. Converts the selection to JSON format for the WPF frontend
        
        Returns:
            str: JSON string with route plan or None if failed
        """
        try:
            # Collect place recommendations
            if self.progress_callback:
                self.progress_callback(60, "Collecting place recommendations...")
            
            self.collect_best_place()
            
            # Validate that we have places to work with
            if not self.best_places:
                print("❌ No places collected, cannot generate route plan", file=sys.stderr)
                if self.progress_callback:
                    self.progress_callback(75, "No places found")
                return None
            
            if self.progress_callback:
                self.progress_callback(65, "Building route planning prompt...")
            
            # Format the recommendations for the prompt
            recommendations = self.format_recommendations()
            
            # Validate recommendations
            if not recommendations:
                print("❌ No recommendations formatted, cannot generate route plan", file=sys.stderr)
                if self.progress_callback:
                    self.progress_callback(75, "Recommendations formatting failed")
                return None
            
            # Debug: Check the structure of recommendations
            print(f"🔍 Recommendations structure: {type(recommendations)}", file=sys.stderr)
            print(f"🔍 Number of recommendations: {len(recommendations)}", file=sys.stderr)
            if recommendations:
                print(f"🔍 First recommendation keys: {list(recommendations[0].keys()) if recommendations else 'None'}", file=sys.stderr)
                print(f"🔍 Sample recommendation: {recommendations[0] if recommendations else 'None'}", file=sys.stderr)
            
            # Build the simple prompt for the Phi model
            prompt = build_phi_location_prompt(
                self.start_location,
                self.companion_type,
                self.starting_time,
                self.budget,
                recommendations,
                self.location_name
            )
            
            if self.progress_callback:
                self.progress_callback(70, "Running Phi model for route planning...")
            
            # Run the Phi model
            runner = GenieRunner(progress_callback=self.progress_callback)
            raw_output = runner.run_phi(prompt)
            
            # Validate Phi output
            if not raw_output:
                print("❌ Phi model returned no output", file=sys.stderr)
                if self.progress_callback:
                    self.progress_callback(75, "Phi model failed - no output")
                fallback_plan = self._create_simple_fallback_route_plan()
                return fallback_plan
            
            if self.progress_callback:
                self.progress_callback(75, "Processing route planning results...")
            
            # Extract the selected places from Phi's output
            selected_places = self._extract_places_from_phi_output(raw_output, recommendations)
            
            # Debug: Check what Phi returned
            print(f"🔍 Phi raw output length: {len(raw_output) if raw_output else 0}", file=sys.stderr)
            print(f"🔍 Phi extracted places: {len(selected_places)}", file=sys.stderr)
            if selected_places:
                print(f"🔍 Selected place names: {[p.get('place_name', 'Unknown') for p in selected_places]}", file=sys.stderr)
            
            if selected_places:
                # Convert to JSON format for WPF
                route_plan_json = self._convert_places_to_json(selected_places)
                if route_plan_json:
                    print(f"✅ Successfully generated route plan with {len(selected_places)} places", file=sys.stderr)
                    return route_plan_json
                else:
                    # Add explicit fallback when JSON conversion fails
                    print("⚠️ JSON conversion failed, using fallback", file=sys.stderr)
                    fallback_plan = self._create_simple_fallback_route_plan()
                    return fallback_plan
            
            # If Phi failed, create a simple fallback
            print("⚠️ Phi model failed, creating simple fallback route plan", file=sys.stderr)
            fallback_plan = self._create_simple_fallback_route_plan()
            return fallback_plan
            
        except Exception as e:
            print(f"Route planner failed: {e}", file=sys.stderr)
            if self.progress_callback:
                self.progress_callback(75, "Route planning failed")
            
            # Try fallback as last resort
            try:
                fallback_plan = self._create_simple_fallback_route_plan()
                return fallback_plan
            except Exception as fallback_error:
                print(f"Fallback route plan also failed: {fallback_error}", file=sys.stderr)
                return None

    def _extract_places_from_phi_output(self, raw_output: str, recommendations: List[Dict]) -> List[Dict]:
        """
        Extract selected places from Phi's output.
        
        Args:
            raw_output (str): Raw output from Phi model
            recommendations (List[Dict]): List of candidate places
            
        Returns:
            List[Dict]: List of selected places
        """
        if not raw_output:
            print("⚠️ No raw output from Phi model", file=sys.stderr)
            return []
        
        print(f"🔍 Processing Phi output: {len(raw_output)} characters", file=sys.stderr)
        print(f"🔍 Available recommendations: {len(recommendations)} places", file=sys.stderr)
        
        # Extract place names from Phi's numbered list format
        selected_places = []
        lines = raw_output.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line and line[0].isdigit() and '.' in line:
                try:
                    # Look for patterns like "1. Place Name - Reason"
                    parts = line.split('.', 1)
                    if len(parts) == 2:
                        place_info = parts[1].strip()
                        if ' - ' in place_info:
                            place_name, reason = place_info.split(' - ', 1)
                            place_name = place_name.strip()
                            
                            print(f"🔍 Line {line_num}: Extracted place name: '{place_name}'", file=sys.stderr)
                            
                            # Find the matching place in recommendations
                            matching_place = self._find_matching_place(place_name, recommendations)
                            if matching_place:
                                selected_places.append(matching_place)
                                print(f"✅ Found match: '{place_name}' -> '{matching_place.get('place_name')}'", file=sys.stderr)
                            else:
                                print(f"⚠️ No match found for: '{place_name}'", file=sys.stderr)
                        else:
                            print(f"⚠️ Line {line_num}: No reason separator found in '{line}'", file=sys.stderr)
                    else:
                        print(f"⚠️ Line {line_num}: Invalid format in '{line}'", file=sys.stderr)
                except Exception as e:
                    print(f"⚠️ Line {line_num}: Error processing '{line}': {e}", file=sys.stderr)
                    continue
        
        print(f"🔍 Successfully extracted {len(selected_places)} places from Phi output", file=sys.stderr)
        if selected_places:
            print(f"🔍 Selected place names: {[p.get('place_name', 'Unknown') for p in selected_places]}", file=sys.stderr)
        
        return selected_places

    def _find_matching_place(self, place_name: str, recommendations: List[Dict]) -> Optional[Dict]:
        """
        Find a matching place in the recommendations list.
        
        Args:
            place_name (str): Place name from Phi output
            recommendations (List[Dict]): List of candidate places
            
        Returns:
            Optional[Dict]: Matching place or None if not found
        """
        # Try exact match first
        for place in recommendations:
            if place.get('place_name') == place_name:
                return place
        
        # Try normalized matching (remove spaces, special chars, case-insensitive)
        normalized_name = ''.join(c.lower() for c in place_name if c.isalnum())
        for place in recommendations:
            candidate_name = place.get('place_name', '')
            normalized_candidate = ''.join(c.lower() for c in candidate_name if c.isalnum())
            if normalized_name in normalized_candidate or normalized_candidate in normalized_name:
                print(f"🔍 Normalized match found: '{place_name}' -> '{candidate_name}'", file=sys.stderr)
                return place
        
        # Try partial match as last resort
        for place in recommendations:
            candidate_name = place.get('place_name', '')
            if place_name.lower() in candidate_name.lower() or candidate_name.lower() in place_name.lower():
                print(f"🔍 Partial match found: '{place_name}' -> '{candidate_name}'", file=sys.stderr)
                return place
        
        print(f"⚠️ No match found for: '{place_name}'", file=sys.stderr)
        return None

    def _convert_places_to_json(self, selected_places: List[Dict]) -> str:
        """
        Convert selected places to JSON format for WPF frontend.
        
        Args:
            selected_places (List[Dict]): List of selected places
            
        Returns:
            str: JSON string with route plan
        """
        try:
            if not selected_places:
                print("⚠️ No places to convert to JSON", file=sys.stderr)
                return None
            
            # Ensure we have the required fields for WPF
            formatted_places = []
            for i, place in enumerate(selected_places):
                try:
                    # Validate required fields
                    place_name = place.get('place_name')
                    if not place_name:
                        print(f"⚠️ Place {i} missing place_name, skipping", file=sys.stderr)
                        continue
                    
                    formatted_place = {
                        "place_name": place_name,
                        "road_address_name": place.get('road_address_name', ''),
                        "place_type": place.get('place_type', 'Unknown'),
                        "distance": int(place.get('distance', 0)),
                        "place_url": place.get('place_url', ''),
                        "latitude": float(place.get('latitude', 0)),
                        "longitude": float(place.get('longitude', 0)),
                        "selection_reason": "Selected by Phi model for itinerary"
                    }
                    formatted_places.append(formatted_place)
                    print(f"✅ Formatted place {i+1}: {place_name}", file=sys.stderr)
                    
                except (ValueError, TypeError) as e:
                    print(f"⚠️ Error formatting place {i}: {e}, skipping", file=sys.stderr)
                    continue
            
            if not formatted_places:
                print("❌ No valid places to convert to JSON", file=sys.stderr)
                return None
            
            json_output = json.dumps(formatted_places, ensure_ascii=False)
            print(f"✅ Successfully converted {len(formatted_places)} places to JSON format", file=sys.stderr)
            return json_output
            
        except Exception as e:
            print(f"❌ Failed to convert places to JSON: {e}", file=sys.stderr)
            return None

    def _create_simple_fallback_route_plan(self) -> str:
        """
        Create a simple fallback route plan when Phi fails.
        
        Returns:
            str: JSON string with fallback route plan
        """
        print("⚠️ Creating simple fallback route plan", file=sys.stderr)
        
        # Get all available places
        all_places = []
        for place_type, places in self.best_places.items():
            all_places.extend(places)
        
        if not all_places:
            print("❌ No places available for fallback", file=sys.stderr)
            return None
        
        # Select first 4-5 places
        num_to_select = min(5, len(all_places))
        selected_places = all_places[:num_to_select]
        
        # Convert to JSON
        return self._convert_places_to_json(selected_places)

    def run_qwen_itinerary(self, route_plan_json=None):
        """
        Generate a comprehensive itinerary using the Qwen model.
        
        This method takes the route plan from run_route_planner and generates
        a detailed itinerary that covers all selected places.
        
        Args:
            route_plan_json (str, optional): Pre-generated route plan JSON. 
                                          If None, will call run_route_planner().
        
        Returns:
            str: Comprehensive itinerary text or error message
        """
        # Get the route plan - either from parameter or by calling route planner
        if route_plan_json is None:
            route_plan_json = self.run_route_planner()
        
        if not route_plan_json:
            return "Failed to generate route plan - cannot create itinerary"
        
        try:
            # Parse the JSON route plan
            selected_locations = json.loads(route_plan_json)
            
            # Safety check: Ensure we have valid locations
            if not selected_locations or not isinstance(selected_locations, list):
                return "Invalid route plan format - no locations found"
            
            if len(selected_locations) == 0:
                return "No locations selected for itinerary - cannot generate story"
            
            print(f"✅ Proceeding with {len(selected_locations)} locations for Qwen story generation", file=sys.stderr)
            
        except Exception as e:
            print(f"Failed to parse route plan: {e}", file=sys.stderr)
            return f"Failed to parse route plan: {e}"
        
        # Build the simple Qwen prompt
        prompt = build_qwen_itinerary_prompt(
            self.companion_type,
            self.budget,
            self.starting_time,
            selected_locations,
        )
        
        # Run the Qwen model to generate the itinerary
        try:
            if self.progress_callback:
                self.progress_callback(80, "Running Qwen model for itinerary generation...")
            
            runner = GenieRunner(progress_callback=self.progress_callback)
            raw_output = runner.run_qwen(prompt)
            
            # Extract clean story text from the model output
            clean_story = self._extract_story_from_output(raw_output)
            
            if clean_story:
                print("✅ Itinerary generated successfully", file=sys.stderr)
                return clean_story
            else:
                print("❌ Failed to extract story from Qwen output", file=sys.stderr)
                return "Failed to generate itinerary - no story content found"
                
        except Exception as e:
            print(f"Qwen model failed: {e}", file=sys.stderr)
            if self.progress_callback:
                self.progress_callback(95, "Qwen model failed")
            return f"Failed to generate itinerary: {e}"
    
    def _extract_story_from_output(self, raw_output: str) -> str:
        """
        Extract clean story text from the Qwen model output.
        
        Args:
            raw_output (str): Raw output from the Qwen model
            
        Returns:
            str: Cleaned story text, or None if no story found
        """
        if not raw_output:
            return None
            
        print(f"Raw Qwen model output: {raw_output[:500]}...", file=sys.stderr)
        
        # Clean the output by removing technical markers
        cleaned_content = self._clean_story_content(raw_output)
        if cleaned_content:
            print(f"✅ Cleaned story content: {cleaned_content[:100]}...", file=sys.stderr)
            return cleaned_content
        
        return None
    
    def _clean_story_content(self, content: str) -> str:
        """
        Clean story content by removing technical markers and debug information.
        
        Args:
            content (str): Raw content to clean
            
        Returns:
            str: Cleaned story content
        """
        if not content:
            return None
        
        # Remove technical markers and debug info
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip technical markers and debug info
            if (line and 
                not line.startswith('Using libGenie.so') and
                not line.startswith('[INFO]') and
                not line.startswith('[PROMPT]:') and
                not line.startswith('<|system|>') and
                not line.startswith('<|user|>') and
                not line.startswith('<|assistant|>') and
                not line.startswith('<|end|>') and
                not line.startswith('<|im_start|>') and
                not line.startswith('<|im_end|>') and
                not line.startswith('Note:') and
                not line.startswith('[KPIS]:') and
                not line.startswith('Init Time:') and
                not line.startswith('Prompt Processing Time:') and
                not line.startswith('Token Generation Time:') and
                not line.startswith('Prompt Processing Rate:') and
                not line.startswith('Token Generation Rate:')):
                
                cleaned_lines.append(line)
        
        cleaned_content = '\n'.join(cleaned_lines).strip()
        
        if cleaned_content:
            return cleaned_content
        
        return None
    