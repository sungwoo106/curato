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
import re
from typing import Tuple, List, Dict, Optional
from collections import deque

# =============================================================================
# CENTRALIZED LOGGING UTILITY
# =============================================================================

# Simple logging utility
def _log(level: str, message: str):
    """Simple logging function."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {level} - {message}", file=sys.stderr)

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
        
        # Initialize reusable AI model instances for better performance
        # These will be loaded once and reused across multiple requests
        self._phi_runner = None
        self._qwen_runner = None
        self._models_initialized = False

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
    # AI MODEL INSTANCE MANAGEMENT
    # =============================================================================
    
    def _initialize_models(self):
        """
        Initialize AI model instances lazily (only when first needed).
        
        This method creates reusable GenieRunner instances for Phi and Qwen models,
        which eliminates the overhead of creating new instances for each request.
        """
        if not self._models_initialized:
            try:
                _log("INFO", "🚀 Initializing AI model instances for better performance...")
                
                # Create reusable model instances
                self._phi_runner = GenieRunner(progress_callback=self.progress_callback)
                self._qwen_runner = GenieRunner(progress_callback=self.progress_callback)
                
                # Validate the setup
                if self._phi_runner.validate_setup() and self._qwen_runner.validate_setup():
                    self._models_initialized = True
                    _log("SUCCESS", "✅ AI model instances initialized successfully")
                    _log("INFO", f"   Phi bundle: {self._phi_runner.phi_bundle_path}")
                    _log("INFO", f"   Qwen bundle: {self._qwen_runner.qwen_bundle_path}")
                else:
                    _log("WARNING", "⚠️ Some model validation failed, but continuing...")
                    self._models_initialized = True  # Still mark as initialized to avoid repeated attempts
                    
            except Exception as e:
                _log("ERROR", f"❌ Failed to initialize AI model instances: {e}")
                # Fall back to creating new instances each time
                self._models_initialized = True  # Prevent repeated initialization attempts
                self._phi_runner = None
                self._qwen_runner = None
    
    def _get_phi_runner(self):
        """
        Get the Phi model runner instance, initializing if necessary.
        
        Returns:
            GenieRunner: Initialized Phi model runner
        """
        if not self._models_initialized:
            self._initialize_models()
        
        if self._phi_runner is None:
            # Fallback: create new instance if initialization failed
            _log("WARNING", "⚠️ Using fallback Phi runner (new instance)")
            return GenieRunner(progress_callback=self.progress_callback)
        
        return self._phi_runner
    
    def _get_qwen_runner(self):
        """
        Get the Qwen model runner instance, initializing if necessary.
        
        Returns:
            GenieRunner: Initialized Qwen model runner
        """
        if not self._models_initialized:
            self._initialize_models()
        
        if self._qwen_runner is None:
            # Fallback: create new instance if initialization failed
            _log("WARNING", "⚠️ Using fallback Qwen runner (new instance)")
            return GenieRunner(progress_callback=self.progress_callback)
        
        return self._qwen_runner
    

    
    def get_performance_stats(self):
        """
        Get performance statistics for the AI model instances.
        
        Returns:
            dict: Performance information including initialization status
        """
        return {
            "models_initialized": self._models_initialized,
            "phi_runner_available": self._phi_runner is not None,
            "qwen_runner_available": self._qwen_runner is not None,
            "optimization_enabled": self._models_initialized and self._phi_runner and self._qwen_runner
        }

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
        
        # Add variety types for rich experience
        from constants import VARIETY_PLACE_TYPES
        variety_types = VARIETY_PLACE_TYPES
        
        available_variety = [t for t in variety_types if t not in self.selected_types]
        if available_variety:
            num_variety = min(2, len(available_variety))
            selected_variety = available_variety[:num_variety]
            self.selected_types.extend(selected_variety)
        
        # Ensure we have at least 6 types for rich variety
        if len(self.selected_types) < 6:
            from constants import DEFAULT_PLACE_TYPES
            for default_type in DEFAULT_PLACE_TYPES:
                if default_type not in self.selected_types and len(self.selected_types) < 6:
                    self.selected_types.append(default_type)
        
        # Limit total types to prevent overwhelming the search
        if len(self.selected_types) > 10:
            user_types = [t for t in self.selected_types if t in (user_selected_types or [])]
            other_types = [t for t in self.selected_types if t not in user_types]
            self.selected_types = user_types + other_types[:7]

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

        
        # Check if we have cached results for this location and place types
        cache_key = self._generate_cache_key()
        cached_results = self._get_cached_results(cache_key)
        
        if cached_results:
            _log("SUCCESS", f"Using cached results for location {self.location_name}")
            self.best_places = cached_results
            return
        
        # Make batch API calls instead of individual calls for each type
        all_places = []
        
        # Group place types into batches to minimize API calls
        # Kakao API can handle multiple place types in a single request
        batch_size = 3  # Process 3 place types per batch
        place_type_batches = [self.selected_types[i:i + batch_size] 
                            for i in range(0, len(self.selected_types), batch_size)]
        
        for batch_idx, place_types_batch in enumerate(place_type_batches):
            try:
                self.rate_limiter.wait_if_needed()
                
                # Make a single API call for multiple place types
                search_result = search_multiple_place_types(
                    place_types_batch,  # Pass multiple types at once
                    self.start_location[0], 
                    self.start_location[1], 
                    int(self.max_distance_km * 1000), 
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
            
            # Implement cache size limit to prevent memory issues
            max_cache_size = 50
            if len(self._cache) > max_cache_size:
                self._cleanup_cache()
                
        except Exception as e:
            _log("WARNING", f"Caching failed: {e}")

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
                
        except Exception as e:
            _log("WARNING", f"⚠️ Cache cleanup failed: {e}")





    def _reduce_to_20_candidates(self, all_places: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Reduce the list of places to 20 candidates using TRUE RANDOM selection.
        
        This method now randomly selects from ALL places regardless of type,
        allowing natural variety to emerge rather than forcing type distribution.
        
        Args:
            all_places (List[Dict]): List of all places found
            
        Returns:
            Dict[str, List[Dict]]: Dictionary with place types as keys and reduced lists as values
        """
        if not all_places:
            return {}
        
        # Show distribution of place types before selection
        type_counts = {}
        for place in all_places:
            place_type = place.get('place_type', 'Unknown')
            type_counts[place_type] = type_counts.get(place_type, 0) + 1
        
        # IMPORTANT: Shuffle ALL places randomly for true randomness
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
            
            # Format the recommendations for the prompt
            recommendations = self.format_recommendations()
            
            # Validate recommendations
            if not recommendations:
                print("❌ No recommendations formatted, cannot generate route plan", file=sys.stderr)
                if self.progress_callback:
                    self.progress_callback(75, "Recommendations formatting failed")
                return None
            
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
            
            # Run the Phi model using reusable instance for better performance
            runner = self._get_phi_runner()
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
                    # Look for patterns like "1. Place Name - Reason" or "1. Place Name (Type)"
                    parts = line.split('.', 1)
                    if len(parts) == 2:
                        place_info = parts[1].strip()
                        
                        # Handle both formats: "Place Name - Reason" and "Place Name (Type)"
                        if ' - ' in place_info:
                            # Format: "Place Name - Reason"
                            place_name, reason = place_info.split(' - ', 1)
                            place_name = place_name.strip()
                        elif ' (' in place_info and place_info.endswith(')'):
                            # Format: "Place Name (Type)" - extract just the place name
                            place_name = place_info.split(' (')[0].strip()
                        else:
                            # Try to extract place name from any other format
                            place_name = place_info.strip()
                        
                        # Skip template placeholders
                        if place_name in ['[Place Name]', 'Place Name', 'Unknown']:
                            print(f"⚠️ Line {line_num}: Skipping template placeholder '{place_name}'", file=sys.stderr)
                            continue
                        
                        print(f"🔍 Line {line_num}: Extracted place name: '{place_name}'", file=sys.stderr)
                        
                        # Find the matching place in recommendations
                        matching_place = self._find_matching_place(place_name, recommendations)
                        if matching_place:
                            selected_places.append(matching_place)
                            print(f"✅ Found match: '{place_name}' -> '{matching_place.get('place_name')}'", file=sys.stderr)
                        else:
                            print(f"⚠️ No match found for: '{place_name}'", file=sys.stderr)
                    else:
                        print(f"⚠️ Line {line_num}: Invalid format in '{line}'", file=sys.stderr)
                except Exception as e:
                    print(f"⚠️ Line {line_num}: Error processing '{line}': {e}", file=sys.stderr)
                    continue
        
        print(f"🔍 Successfully extracted {len(selected_places)} places from Phi output", file=sys.stderr)
        if selected_places:
            print(f"🔍 Selected place names: {[p.get('place_name', 'Unknown') for p in selected_places]}", file=sys.stderr)
        
        # Deduplicate places to ensure only unique locations are selected
        deduplicated_places = self._deduplicate_places(selected_places)
        
        print(f"🔍 After deduplication: {len(deduplicated_places)} unique places", file=sys.stderr)
        if deduplicated_places:
            print(f"🔍 Final unique place names: {[p.get('place_name', 'Unknown') for p in deduplicated_places]}", file=sys.stderr)
        
        return deduplicated_places

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
    
    def _deduplicate_places(self, selected_places: List[Dict]) -> List[Dict]:
        """
        Remove duplicate places from the selected places list.
        
        Args:
            selected_places (List[Dict]): List of selected places (may contain duplicates)
            
        Returns:
            List[Dict]: List of unique places
        """
        if not selected_places:
            return []
        
        # Use a dictionary to track unique places by place_name
        unique_places = {}
        duplicates_found = 0
        
        for place in selected_places:
            place_name = place.get('place_name', 'Unknown')
            
            if place_name not in unique_places:
                # First occurrence - add to unique places
                unique_places[place_name] = place
            else:
                # Duplicate found - skip and count
                duplicates_found += 1
                print(f"⚠️ Duplicate place skipped: '{place_name}' (already selected)", file=sys.stderr)
        
        # Convert back to list
        deduplicated_list = list(unique_places.values())
        
        print(f"🔍 Deduplication complete: {len(selected_places)} -> {len(deduplicated_list)} places", file=sys.stderr)
        if duplicates_found > 0:
            print(f"⚠️ Removed {duplicates_found} duplicate places", file=sys.stderr)
        
        # Ensure we don't exceed the intended number of places (4-5)
        max_places = 5
        if len(deduplicated_list) > max_places:
            print(f"⚠️ Too many places ({len(deduplicated_list)}), limiting to {max_places}", file=sys.stderr)
            deduplicated_list = deduplicated_list[:max_places]
        
        # Validate that we have the expected number of places
        min_places = 4
        if len(deduplicated_list) < min_places:
            print(f"⚠️ Too few places ({len(deduplicated_list)}), expected {min_places}-{max_places}", file=sys.stderr)
            # This might indicate the Phi model didn't follow instructions properly
        
        return deduplicated_list

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
        
        # Run the Qwen model to generate the itinerary using reusable instance for better performance
        try:
            if self.progress_callback:
                self.progress_callback(80, "Running Qwen model for itinerary generation...")
            
            runner = self._get_qwen_runner()
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
    
    def run_qwen_itinerary_streaming(self, route_plan_json=None, stream_callback=None):
        """
        Generate a comprehensive itinerary using the Qwen model with real-time streaming.
        
        This method takes the route plan from run_route_planner and generates
        a detailed itinerary that covers all selected places, streaming the output
        in real-time for immediate display.
        
        Args:
            route_plan_json (str, optional): Pre-generated route plan JSON. 
                                          If None, will call run_route_planner().
            stream_callback (callable, optional): Callback function for streaming updates.
                                               Should accept (token, is_final) parameters.
        
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
            
            print(f"✅ Proceeding with {len(selected_locations)} locations for Qwen streaming story generation", file=sys.stderr)
            
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
        
        # Run the Qwen model with streaming to generate the itinerary
        try:
            if self.progress_callback:
                self.progress_callback(80, "Running Qwen model with streaming for real-time itinerary generation...")
            
            runner = self._get_qwen_runner()
            
            # Define streaming callback to send real-time updates
            def streaming_callback(token, is_final):
                if stream_callback:
                    stream_callback(token, is_final)
                else:
                    # Default behavior: print to stderr for debugging
                    if not is_final:
                        print(token, end='', file=sys.stderr, flush=True)
                    else:
                        print("\n✅ Streaming completed", file=sys.stderr)
            
            # Use streaming method if available, fallback to regular method
            if hasattr(runner, 'run_qwen_streaming'):
                raw_output = runner.run_qwen_streaming(prompt, streaming_callback)
            else:
                # Fallback to non-streaming method
                print("⚠️ Streaming not available, using regular generation", file=sys.stderr)
                raw_output = runner.run_qwen(prompt)
                # Simulate streaming by sending the complete output
                if stream_callback:
                    stream_callback(raw_output, True)
            
            # Extract clean story text from the model output
            clean_story = self._extract_story_from_output(raw_output)
            
            if clean_story:
                print("✅ Streaming itinerary generation completed successfully", file=sys.stderr)
                return clean_story
            else:
                print("❌ Failed to extract story from Qwen streaming output", file=sys.stderr)
                return "Failed to generate itinerary - no story content found"
                
        except Exception as e:
            print(f"Qwen streaming model failed: {e}", file=sys.stderr)
            if self.progress_callback:
                self.progress_callback(95, "Qwen streaming model failed")
            return f"Failed to generate streaming itinerary: {e}"
    
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
            
        print(f"🔍 Raw Qwen model output length: {len(raw_output)}", file=sys.stderr)
        print(f"🔍 Raw Qwen model output first 500 chars: {raw_output[:500]}...", file=sys.stderr)
        
        # Clean the output by removing technical markers
        cleaned_content = self._clean_story_content(raw_output)
        if cleaned_content:
            print(f"✅ Cleaned story content length: {len(cleaned_content)}", file=sys.stderr)
            print(f"✅ Cleaned story content first 200 chars: {cleaned_content[:200]}...", file=sys.stderr)
            print(f"✅ Cleaned story content last 200 chars: {cleaned_content[-200:] if len(cleaned_content) > 200 else cleaned_content}...", file=sys.stderr)
            return cleaned_content
        
        print(f"❌ Failed to clean story content", file=sys.stderr)
        return None
    
    def _clean_story_content(self, content: str) -> str:
        """
        Clean story content by extracting only the assistant's response.
        
        Args:
            content (str): Raw content from the model
            
        Returns:
            str: Cleaned story content
        """
        if not content:
            return None
        
        print(f"🔍 Cleaning story content: {len(content)} characters", file=sys.stderr)
        print(f"🔍 First 200 chars: {content[:200]}...", file=sys.stderr)
        
        # Remove unwanted tokens first
        content = re.sub(r'\[END\]', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<\|end\|>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<\|im_end\|>', '', content, flags=re.IGNORECASE)
        
        # Extract content after <|im_start|> assistant marker
        assistant_content = self._extract_assistant_response(content)
        if assistant_content:
            print(f"✅ Successfully extracted assistant content: {len(assistant_content)} characters", file=sys.stderr)
            print(f"✅ First 200 chars of extracted content: {assistant_content[:200]}...", file=sys.stderr)
            return assistant_content
        
        print(f"⚠️ Failed to extract assistant content, returning cleaned original", file=sys.stderr)
        # If no assistant marker found, return the cleaned content as fallback
        return content.strip()
    

    
    def _extract_assistant_response(self, content: str) -> str:
        """
        Extract content after <|im_start|> assistant marker, stopping at technical markers.
        
        Args:
            content (str): Raw content from the model
            
        Returns:
            str: Extracted content after assistant marker or None if not found
        """
        # Look for content after <|im_start|> assistant marker (with or without space)
        pattern = r'<\|im_start\|>\s*assistant\s*(.*)'
        print(f"🔍 Searching for pattern: {pattern}", file=sys.stderr)
        print(f"🔍 Content length: {len(content)}", file=sys.stderr)
        print(f"🔍 Content contains '<|im_start|>': {'<|im_start|>' in content}", file=sys.stderr)
        print(f"🔍 Content contains 'assistant': {'assistant' in content}", file=sys.stderr)
        print(f"🔍 Content contains '<|im_start|>assistant': {'<|im_start|>assistant' in content}", file=sys.stderr)
        
        match = re.search(pattern, content, re.DOTALL)
        if match:
            extracted_content = match.group(1).strip()
            print(f"✅ Regex match found! Extracted {len(extracted_content)} characters", file=sys.stderr)
            
            # Clean up the extracted content by removing technical markers
            # Stop at common technical markers that indicate the end of useful content
            technical_markers = [
                'Note: The KPIS stdout below is deprecated',
                '[KPIS]:',
                'Init Time:',
                'Token Generation Time:',
                'Prompt Processing Time:',
                'Token Generation Rate:',
                'Prompt Processing Rate:'
            ]
            
            # Find the earliest technical marker
            earliest_marker_pos = len(extracted_content)
            for marker in technical_markers:
                pos = extracted_content.find(marker)
                if pos != -1 and pos < earliest_marker_pos:
                    earliest_marker_pos = pos
                    print(f"🔍 Found technical marker '{marker}' at position {pos}", file=sys.stderr)
            
            # Cut off at the first technical marker
            if earliest_marker_pos < len(extracted_content):
                extracted_content = extracted_content[:earliest_marker_pos].strip()
                print(f"✅ Extracted content after <|im_start|> assistant (stopped at technical marker): {len(extracted_content)} characters", file=sys.stderr)
            else:
                print(f"✅ Extracted content after <|im_start|> assistant (no technical markers found): {len(extracted_content)} characters", file=sys.stderr)
            
            return extracted_content
        else:
            print(f"⚠️ <|im_start|> assistant marker not found in content", file=sys.stderr)
            print(f"🔍 Content preview (first 300 chars): {content[:300]}...", file=sys.stderr)
            print(f"🔍 Content preview (last 300 chars): {content[-300:] if len(content) > 300 else content}...", file=sys.stderr)
            return None
    

    