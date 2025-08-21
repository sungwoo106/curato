"""
Refactored Preferences and Itinerary Generation Engine

This module is the refactored version of the original preferences.py, now using
a modular architecture with separate components for different responsibilities.

The main Preferences class now orchestrates:
- AI model execution (via GenieRunner)
- Caching (via CacheManager) 
- Rate limiting (via RateLimiter)
- Place management (via PlaceManager)
- Itinerary generation workflow
"""

import json
import sys
import time
from typing import List, Dict, Optional, Callable

from models.genie_runner import GenieRunner
from core.cache_manager import CacheManager
from core.rate_limiter import APIRateLimiter
from core.place_manager import PlaceManager
from core.prompts import build_phi_location_prompt, build_qwen_itinerary_prompt
from data.api_clients.kakao_api import format_kakao_places_for_prompt


class Preferences:
    """
    Main class for managing user preferences and generating personalized itineraries.
    
    This refactored version uses a modular architecture where each component
    handles a specific responsibility, making the code more maintainable and testable.
    """
    
    def __init__(self,
                 companion_type="Solo",
                 budget="low",
                 starting_time=12,
                 max_distance_km=5,
                 start_location=(37.5563, 126.9237),
                 location_name="Seoul",
                 progress_callback=None):
        """
        Initialize a new Preferences instance with user preferences.
        
        Args:
            companion_type: Type of outing (Solo, Couple, Friends, Family)
            budget: Budget level (low, medium, high)
            starting_time: Starting time in 24-hour format (0-23)
            max_distance_km: Maximum search radius in kilometers
            start_location: Starting coordinates (latitude, longitude)
            location_name: Human-readable location name
            progress_callback: Optional callback for progress updates
        """
        # Core user preferences
        self.companion_type = companion_type
        self.budget = budget
        self.starting_time = starting_time
        self.max_distance_km = max_distance_km
        self.start_location = start_location
        self.location_name = location_name
        self.progress_callback = progress_callback
        
        # Initialize modular components
        self.rate_limiter = APIRateLimiter(max_calls=100, time_window=60)
        self.cache_manager = CacheManager()
        self.place_manager = PlaceManager(self.rate_limiter, self.cache_manager)
        
        # Generated data and recommendations
        self.recommendations_json = []

    # =============================================================================
    # PLACE TYPE SELECTION AND COLLECTION
    # =============================================================================
    
    def select_place_types(self, user_selected_types=None):
        """Select appropriate place types based on companion type and user preferences."""
        self.place_manager.select_place_types(user_selected_types, self.companion_type)
        self.selected_types = self.place_manager.selected_types

    def collect_best_place(self):
        """Collect place recommendations using the place manager."""
        self.place_manager.collect_places(
            self.start_location, 
            self.max_distance_km, 
            self.location_name
        )
        self.best_places = self.place_manager.best_places

    def format_recommendations(self):
        """Format the collected place recommendations for use in AI prompts."""
        self.recommendations_json = format_kakao_places_for_prompt(self.best_places)
        return self.recommendations_json

    # =============================================================================
    # ITINERARY GENERATION WORKFLOW
    # =============================================================================
    
    def run_route_planner(self):
        """Generate a route plan using the Phi model."""
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
            
            # Build the prompt for the Phi model
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
            raw_output = runner.run_phi(prompt, "phi_profile")
            
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
        
        # Build the Qwen prompt
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
            
            runner = GenieRunner(progress_callback=self.progress_callback)
            
            # Define streaming callback to send raw tokens directly to frontend for real-time filtering
            def streaming_callback(token, is_final):
                if stream_callback:
                    # Send raw token to frontend - let frontend handle the filtering
                    stream_callback(token, is_final)
                else:
                    # Default behavior: print to stderr for debugging
                    if not is_final:
                        print(token, end='', file=sys.stderr, flush=True)
                    else:
                        print("\n✅ Streaming completed", file=sys.stderr)
            
            # Use streaming method if available, fallback to regular method
            if hasattr(runner, 'run_qwen_streaming'):
                raw_output = runner.run_qwen_streaming(prompt, streaming_callback, "qwen_profile")
            else:
                # Fallback to non-streaming method
                print("⚠️ Streaming not available, using regular generation", file=sys.stderr)
                raw_output = runner.run_qwen(prompt, "qwen_profile")
                # Simulate streaming by sending the complete output
                if stream_callback:
                    stream_callback(raw_output, True)
            
            # For streaming, we return the raw output since frontend handles filtering
            print("✅ Streaming itinerary generation completed successfully", file=sys.stderr)
            return raw_output
                
        except Exception as e:
            print(f"Qwen streaming model failed: {e}", file=sys.stderr)
            if self.progress_callback:
                self.progress_callback(95, "Qwen streaming model failed")
            return f"Failed to generate streaming itinerary: {e}"

    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _extract_places_from_phi_output(self, raw_output: str, recommendations: List[Dict]) -> List[Dict]:
        """
        Extract selected places from Phi's output.
        
        Args:
            raw_output (str): Raw output text from Phi model
            recommendations (List[Dict]): List of formatted place recommendations
            
        Returns:
            List[Dict]: List of selected places with full metadata
        """
        if not raw_output:
            return []
        
        selected_places = []
        lines = raw_output.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and line[0].isdigit() and '.' in line:
                try:
                    parts = line.split('.', 1)
                    if len(parts) == 2:
                        place_info = parts[1].strip()
                        
                        if ' - ' in place_info:
                            place_name = place_info.split(' - ', 1)[0].strip()
                        elif ' (' in place_info and place_info.endswith(')'):
                            place_name = place_info.split(' (')[0].strip()
                        else:
                            place_name = place_info.strip()
                        
                        if place_name in ['[Place Name]', 'Place Name', 'Unknown']:
                            continue
                        
                        matching_place = self._find_matching_place(place_name, recommendations)
                        if matching_place:
                            selected_places.append(matching_place)
                            
                except Exception as e:
                    continue
        
        # Deduplicate places
        return self._deduplicate_places(selected_places)

    def _find_matching_place(self, place_name: str, recommendations: List[Dict]) -> Optional[Dict]:
        """
        Find a matching place in the recommendations list.
        
        Args:
            place_name (str): Name of the place to find
            recommendations (List[Dict]): List of place recommendations to search in
            
        Returns:
            Optional[Dict]: Matching place dict if found, None otherwise
        """
        # Try exact match first
        for place in recommendations:
            if place.get('place_name') == place_name:
                return place
        
        # Try normalized matching
        normalized_name = ''.join(c.lower() for c in place_name if c.isalnum())
        for place in recommendations:
            candidate_name = place.get('place_name', '')
            normalized_candidate = ''.join(c.lower() for c in candidate_name if c.isalnum())
            if normalized_name in normalized_candidate or normalized_candidate in normalized_name:
                return place
        
        # Try partial match as last resort
        for place in recommendations:
            candidate_name = place.get('place_name', '')
            if place_name.lower() in candidate_name.lower() or candidate_name.lower() in place_name.lower():
                return place
        
        return None
    
    def _deduplicate_places(self, selected_places: List[Dict]) -> List[Dict]:
        """
        Remove duplicate places from the selected places list.
        
        Args:
            selected_places (List[Dict]): List of places that may contain duplicates
            
        Returns:
            List[Dict]: Deduplicated list of places
        """
        if not selected_places:
            return []
        
        unique_places = {}
        for place in selected_places:
            place_name = place.get('place_name', 'Unknown')
            if place_name not in unique_places:
                unique_places[place_name] = place
        
        deduplicated_list = list(unique_places.values())
        
        # Ensure we don't exceed the intended number of places (4-5)
        max_places = 5
        if len(deduplicated_list) > max_places:
            deduplicated_list = deduplicated_list[:max_places]
        
        return deduplicated_list

    def _convert_places_to_json(self, selected_places: List[Dict]) -> str:
        """
        Convert selected places to JSON format for WPF frontend.
        
        Args:
            selected_places (List[Dict]): List of selected places with metadata
            
        Returns:
            Optional[str]: JSON string representation of places, or None if conversion fails
        """
        try:
            if not selected_places:
                return None
            
            formatted_places = []
            for place in selected_places:
                try:
                    place_name = place.get('place_name')
                    if not place_name:
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
                    
                except (ValueError, TypeError) as e:
                    continue
            
            if not formatted_places:
                return None
            
            json_output = json.dumps(formatted_places, ensure_ascii=False)
            return json_output
            
        except Exception as e:
            print(f"❌ Failed to convert places to JSON: {e}", file=sys.stderr)
            return None

    def _create_simple_fallback_route_plan(self) -> str:
        """
        Create a simple fallback route plan when Phi fails.
        
        Returns:
            Optional[str]: JSON string with fallback route plan, or None if no places available
        """
        print("⚠️ Creating simple fallback route plan", file=sys.stderr)
        
        all_places = []
        for place_type, places in self.best_places.items():
            all_places.extend(places)
        
        if not all_places:
            return None
        
        num_to_select = min(5, len(all_places))
        selected_places = all_places[:num_to_select]
        
        return self._convert_places_to_json(selected_places)


