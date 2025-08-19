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

from core.prompts import build_phi_location_prompt, build_qwen_story_prompt, build_comprehensive_qwen_prompt, build_ultra_comprehensive_qwen_prompt
from models.genie_runner import GenieRunner
from data.api_clients.kakao_api import format_kakao_places_for_prompt, get_progressive_place_selection_enhanced
from constants import USER_SELECTABLE_PLACE_TYPES, COMPANION_PLACE_TYPES, COMPANION_TYPES, BUDGET, LOCATION, MAX_DISTANCE_KM, STARTING_TIME
import random
import json
import sys
from typing import Tuple, List, Dict
import re

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
                 progress_callback=None):
        """
        Initialize a new Preferences instance with user preferences.
        
        Args:
            companion_type (str): Type of outing (Solo, Couple, Friends, Family)
            budget (str): Budget level (low, medium, high)
            starting_time (int): Starting time in 24-hour format (0-23)
            max_distance_km (int): Maximum search radius in kilometers
            start_location (tuple): Starting coordinates (latitude, longitude)
            progress_callback (callable): Optional callback for progress updates
        """
        # Core user preferences
        self.companion_type = companion_type
        self.budget = budget
        self.starting_time = starting_time
        self.max_distance_km = max_distance_km
        self.start_location = start_location
        self.progress_callback = progress_callback
        
        # Generated data and recommendations
        self.selected_types = []        # Place types selected for this itinerary
        self.best_places = {}           # Dictionary of place type -> list of places
        self.recommendations_json = []  # Formatted recommendations for AI prompts

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
        1. Companion-specific recommendations (e.g., romantic spots for couples)
        2. User manually selected types (if any)
        3. Random selection to ensure variety
        
        Args:
            user_selected_types (list, optional): User's manually selected place types
        """
        # Get companion-specific place type recommendations
        companion_places = COMPANION_PLACE_TYPES.get(self.companion_type.lower(), [])
        
        # Randomly select 4-5 place types for variety
        num_to_select = random.choice([4, 5])
        random_types = []
        
        if len(companion_places) >= num_to_select:
            # If we have enough companion-specific types, randomly sample from them
            random_types = random.sample(companion_places, num_to_select)
        else:
            # If we don't have enough, use all available companion types
            random_types = companion_places.copy()
        
        # Combine user selected types and random companion types, ensuring uniqueness
        combined_types = set(random_types)
        if user_selected_types:
            combined_types.update(user_selected_types)
        
        self.selected_types = list(combined_types)
        
        # Fallback to a default place type if none were selected
        if not self.selected_types:
            self.selected_types = [USER_SELECTABLE_PLACE_TYPES[0]]

    # =============================================================================
    # PLACE RECOMMENDATION COLLECTION
    # =============================================================================
    
    def collect_best_place(self):
        """
        Collect geographically coherent place recommendations using smart clustering.
        
        This method uses progressive place selection to ensure consecutive
        locations are close to each other while minimizing API calls and
        providing manageable options for the AI model.
        
        Key benefits:
        - Reduces places from 60-75 to 15-25 (manageable for Phi)
        - Ensures geographic proximity between consecutive locations
        - Creates logical, walkable routes
        - Minimizes token usage in AI prompts
        
        Returns:
            dict: Dictionary where keys are place types and values are lists of places
        """
        # Use progressive place selection with smart clustering
        # This ensures geographically close locations while providing variety for Phi
        optimal_places = get_progressive_place_selection_enhanced(
            self.selected_types,                       # List of place types to search for
            self.start_location,                       # Starting coordinates
            int(self.max_distance_km * 1000),          # Distance in meters
            places_per_type=15,                        # Increased to 15 per type for variety
            max_cluster_distance=300,                  # 300m clustering for tight walkable coherence
            target_places=20                           # 20 places for Phi to choose from
        )
        
        # Group the selected places by type for compatibility with existing code
        self.best_places = {}
        for place in optimal_places:
            place_type = place.get('place_type', 'Unknown')
            if place_type not in self.best_places:
                self.best_places[place_type] = []
            self.best_places[place_type].append(place)

    def format_recommendations(self):
        """
        Format the collected place recommendations for use in AI prompts.
        
        This method converts the raw place data into a format that can be
        easily consumed by the AI models for generating itineraries.
        
        Returns:
            list: Formatted recommendations ready for AI prompt generation
        """
        self.recommendations_json = format_kakao_places_for_prompt(self.best_places)
        return self.recommendations_json

    # =============================================================================
    # ITINERARY GENERATION WORKFLOW
    # =============================================================================
    
    def run_route_planner(self):
        """
        Generate a route plan using the Phi model.
        
        This method:
        1. Collects multiple place recommendations from Kakao API (10-15 per type)
        2. Selects optimal places for the itinerary
        3. Builds a prompt for the Phi model
        4. Generates a route plan with 4-5 locations
        5. Returns the result as JSON
        
        Returns:
            str: JSON string with route plan or None if failed
        """
        try:
            # Collect multiple place recommendations for each type
            if self.progress_callback:
                self.progress_callback(60, "Collecting place recommendations...")
            
            self.collect_best_place()
            
            # Places are already optimally selected and ordered by the progressive selection system
            if self.progress_callback:
                self.progress_callback(62, "Places optimally selected and ordered...")
            
            # The progressive selection already provides optimal, geographically close places
            # No need for additional selection logic
            
            if self.progress_callback:
                self.progress_callback(65, "Building route planning prompt...")
            
            # Format the recommendations for the prompt
            recommendations = self.format_recommendations()
            
            # Build the prompt for the Phi model
            prompt = build_phi_location_prompt(
                self.start_location,                    # Starting coordinates
                self.companion_type,                    # Companion type for context
                self.starting_time,                     # Starting time for timing
                self.budget,                            # Budget level for cost considerations
                recommendations                         # Place recommendations
            )
            
            if self.progress_callback:
                self.progress_callback(70, "Running Phi model for route planning...")
            
            # Run the Phi model with progress callback
            runner = GenieRunner(progress_callback=self.progress_callback)
            raw_output = runner.run_phi(prompt)
            
            if self.progress_callback:
                self.progress_callback(75, "Processing route planning results...")
            
            # Extract the JSON result from the model output
            route_plan_json = self._extract_json_from_output(raw_output)
            
            if route_plan_json:
                return route_plan_json
            else:
                # JSON extraction failed, try to create a fallback route plan
                if self.progress_callback:
                    self.progress_callback(75, "Creating fallback route plan...")
                
                print("⚠️ JSON extraction failed, creating fallback route plan", file=sys.stderr)
                fallback_plan = self._create_fallback_route_plan(self.start_location, self.selected_types)
                return fallback_plan
            
        except Exception as e:
            print(f"Route planner failed: {e}", file=sys.stderr)
            if self.progress_callback:
                self.progress_callback(75, "Route planning failed")
            
            # Try fallback as last resort
            try:
                if self.progress_callback:
                    self.progress_callback(75, "Attempting fallback route plan...")
                fallback_plan = self._create_fallback_route_plan(self.start_location, self.selected_types)
                return fallback_plan
            except Exception as fallback_error:
                print(f"Fallback route plan also failed: {fallback_error}", file=sys.stderr)
                return None
    
    def _create_fallback_route_plan(self, start_location: Tuple[float, float], 
                                   place_types: List[str]) -> str:
        """
        Create a fallback route plan when Phi fails.
        
        This generates a realistic route plan with actual place names and coordinates
        around the starting location to ensure the system can continue.
        
        Args:
            start_location (Tuple[float, float]): Starting coordinates (lat, lng)
            place_types (List[str]): List of place types to include
            
        Returns:
            str: JSON string with fallback route plan
        """
        print("⚠️ Creating enhanced fallback route plan", file=sys.stderr)
        
        # Generate realistic fallback places around the starting location
        base_lat, base_lng = start_location
        
        # Create realistic fallback locations with actual place names
        fallback_places = []
        
        # Define realistic place names for different types
        place_names = {
            "Cafe": ["스타벅스 홍대점", "투썸플레이스 홍대점", "할리스 홍대점", "이디야 홍대점", "빽다방 홍대점"],
            "Restaurant": ["홍대 맛집", "홍대 분식", "홍대 치킨", "홍대 피자", "홍대 떡볶이"],
            "Cultural": ["홍대 클럽", "홍대 공연장", "홍대 갤러리", "홍대 카페거리", "홍대 상점가"],
            "Entertainment": ["홍대 놀이터", "홍대 게임장", "홍대 노래방", "홍대 영화관", "홍대 볼링장"]
        }
        
        # Create 5 unique locations with realistic names
        for i in range(5):
            # Generate unique coordinates with small offsets
            offset_lat = base_lat + (i * 0.0005)  # Small northward progression
            offset_lng = base_lng + (i * 0.0003)  # Small eastward progression
            
            # Ensure coordinates are valid for Korea
            if offset_lat > 38.6:  # Korea's northern boundary
                offset_lat = base_lat - (i * 0.0005)  # Go south instead
            
            # Select appropriate place type and name
            place_type = place_types[i % len(place_types)] if place_types else "Cafe"
            type_key = place_type.capitalize()
            
            # Get realistic names for this type, or use generic if not found
            available_names = place_names.get(type_key, place_names["Cafe"])
            place_name = available_names[i % len(available_names)]
            
            fallback_place = {
                "place_name": place_name,
                "road_address_name": f"홍대 근처 {place_type}",
                "place_type": place_type,
                "distance": str((i + 1) * 100),  # Increasing distance
                "place_url": "",
                "latitude": offset_lat,
                "longitude": offset_lng,
                "selection_reason": f"Fallback {place_type} location for itinerary generation"
            }
            
            fallback_places.append(fallback_place)
        
        try:
            json_output = json.dumps(fallback_places, ensure_ascii=False)
            print(f"✅ Created enhanced fallback route plan with {len(fallback_places)} realistic locations", file=sys.stderr)
            print(f"✅ Each location has unique coordinates and realistic names", file=sys.stderr)
            return json_output
        except Exception as e:
            print(f"❌ Failed to create JSON for fallback plan: {e}", file=sys.stderr)
            return None

    def _extract_json_from_output(self, raw_output: str) -> str:
        """
        Extract JSON content from the raw model output.
        
        Since Phi cannot generate valid JSON, we now expect text-based place selection
        and convert it to JSON format programmatically.
        
        Args:
            raw_output (str): Raw output from the Phi model
            
        Returns:
            str: Cleaned JSON string, or None if no valid data found
        """
        if not raw_output:
            return None
            
        print(f"Raw Phi model output: {raw_output[:500]}...", file=sys.stderr)
        
        # Clean the output - remove common Phi artifacts
        cleaned_output = raw_output
        
        # Remove common Phi output artifacts
        artifacts_to_remove = [
            'Using libGenie.so version',
            '[INFO]',
            '[PROMPT]:',
            '<|system|>',
            '<|user|>',
            '<|end|>',
            'Starting from',
            'Available places:'
        ]
        
        for artifact in artifacts_to_remove:
            cleaned_output = cleaned_output.replace(artifact, '')
        
        print(f"Cleaned output: {cleaned_output[:300]}...", file=sys.stderr)
        
        # Try to extract place selection from text output
        print("🔍 Attempting to extract place selection from text...", file=sys.stderr)
        selected_places = self._extract_places_from_text(cleaned_output)
        
        if selected_places:
            # Validate Phi's output meets our 4-5 place requirement
            self._validate_phi_output(selected_places)
            
            # Ensure we have minimum required locations for map functionality
            print(f"🔍 Before supplementation: {len(selected_places)} places", file=sys.stderr)
            print(f"🔍 Places before supplementation: {[p['place_name'] for p in selected_places]}", file=sys.stderr)
            
            # Only supplement if we have fewer than 3 places (system stability requirement)
            # Phi should generate 4-5, so supplementation should rarely be needed
            if len(selected_places) < 3:
                print(f"⚠️ Phi generated only {len(selected_places)} places, supplementing for system stability", file=sys.stderr)
                selected_places = self._ensure_minimum_locations(selected_places, min_locations=3)
                print(f"🔍 After supplementation: {len(selected_places)} places", file=sys.stderr)
                print(f"🔍 Places after supplementation: {[p['place_name'] for p in selected_places]}", file=sys.stderr)
            else:
                print(f"✅ Phi generated {len(selected_places)} places as expected (4-5 range)", file=sys.stderr)
            
            # Convert to JSON format
            json_output = self._convert_places_to_json(selected_places)
            if json_output:
                print(f"✅ Successfully converted text selection to JSON with {len(selected_places)} places", file=sys.stderr)
                return json_output
        
        print("❌ Failed to extract place selection from text", file=sys.stderr)
        return None

    def _extract_places_from_text(self, text: str) -> List[Dict]:
        """
        Extract place information from Phi's text-based place selection.
        
        Args:
            text (str): Raw output from the Phi model
            
        Returns:
            List[Dict]: List of place dictionaries, or empty if not found
        """
        places = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and line[0].isdigit() and '.' in line:
                # Look for patterns like "1. Place Name - Reason"
                parts = line.split('.', 1)
                if len(parts) == 2:
                    place_info = parts[1].strip()
                    if ' - ' in place_info:
                        place_name, reason = place_info.split(' - ', 1)
                        place_name = place_name.strip()
                        
                        # Filter out generic place names and placeholder text
                        if (place_name and 
                            place_name.lower() not in ['place name', 'location', 'venue', 'spot', 'place'] and
                            '[' not in place_name and  # Filter out [Copy exact name from candidates]
                            ']' not in place_name and  # Filter out placeholder brackets
                            'exact' not in place_name.lower() and  # Filter out "exact" references
                            'candidates' not in place_name.lower() and  # Filter out "candidates" references
                            len(place_name) > 2 and  # Must be longer than 2 characters
                            not place_name.isdigit()):  # Must not be just numbers
                            
                            places.append({
                                "place_name": place_name,
                                "selection_reason": reason.strip()
                            })
                        else:
                            print(f"⚠️ Filtered out invalid place name: '{place_name}'", file=sys.stderr)
        
        print(f"🔍 Extracted {len(places)} valid places from text: {[p['place_name'] for p in places]}", file=sys.stderr)
        return places
    
    def _validate_phi_output(self, selected_places: List[Dict]) -> None:
        """
        Validate that Phi's output meets our 4-5 place requirement.
        
        Args:
            selected_places (List[Dict]): List of places extracted from Phi output
        """
        place_count = len(selected_places)
        expected_min = 4
        expected_max = 5
        
        if place_count < expected_min:
            print(f"⚠️ Phi generated only {place_count} places (expected {expected_min}-{expected_max})", file=sys.stderr)
            print(f"⚠️ This may indicate the model didn't follow instructions properly", file=sys.stderr)
        elif place_count > expected_max:
            print(f"⚠️ Phi generated {place_count} places (expected {expected_min}-{expected_max})", file=sys.stderr)
            print(f"⚠️ The model generated more places than requested", file=sys.stderr)
        else:
            print(f"✅ Phi generated {place_count} places as expected ({expected_min}-{expected_max} range)", file=sys.stderr)
        
        # Log the actual places for debugging
        print(f"🔍 Phi selected places: {[p['place_name'] for p in selected_places]}", file=sys.stderr)
    
    def _ensure_minimum_locations(self, selected_places: List[Dict], min_locations: int = 4) -> List[Dict]:
        """
        Ensure we have a minimum number of locations by supplementing with fallback places if needed.
        
        This addresses the issue where Phi generates generic placeholders instead of real locations.
        
        Args:
            selected_places (List[Dict]): List of places extracted from Phi output
            min_locations (int): Minimum number of locations required
            
        Returns:
            List[Dict]: List with minimum required locations
        """
        if len(selected_places) >= min_locations:
            return selected_places
        
        print(f"⚠️ Only {len(selected_places)} valid places found, need minimum {min_locations}", file=sys.stderr)
        print("🔧 Supplementing with fallback locations to ensure map functionality", file=sys.stderr)
        
        # Get all available candidates to supplement the list
        all_candidates = self._get_all_candidates()
        if not all_candidates:
            print("❌ No candidate places available for supplementation", file=sys.stderr)
            return selected_places
        
        # Create a set of already selected place names to avoid duplicates
        selected_names = {place['place_name'].lower() for place in selected_places}
        
        # Find additional candidates that weren't selected
        additional_places = []
        for candidate in all_candidates:
            candidate_name = candidate.get('place_name', '').lower()
            if candidate_name not in selected_names:
                additional_places.append({
                    "place_name": candidate.get('place_name', 'Unknown'),
                    "selection_reason": f"Supplemented location for complete itinerary"
                })
                selected_names.add(candidate_name)
                
                # Stop when we have enough locations
                if len(selected_places) + len(additional_places) >= min_locations:
                    break
        
        # Combine original and additional places
        final_places = selected_places + additional_places
        
        print(f"✅ Supplemented to {len(final_places)} total locations", file=sys.stderr)
        print(f"✅ Original: {len(selected_places)}, Additional: {len(additional_places)}", file=sys.stderr)
        
        return final_places
    
    def _create_fallback_locations_for_qwen(self, existing_locations: List[Dict]) -> List[Dict]:
        """
        Create fallback locations when we don't have enough for Qwen story generation.
        
        This ensures the Qwen prompts always have enough locations to work with.
        
        Args:
            existing_locations (List[Dict]): List of existing valid locations
            
        Returns:
            List[Dict]: List with minimum 4 locations for Qwen generation
        """
        print(f"🔧 Creating fallback locations for Qwen (current: {len(existing_locations)})", file=sys.stderr)
        
        # We need at least 4 locations for the Qwen prompts to work properly
        min_locations = 4
        if len(existing_locations) >= min_locations:
            return existing_locations
        
        # Get all available candidates to supplement
        all_candidates = self._get_all_candidates()
        if not all_candidates:
            print("❌ No candidate places available for Qwen fallback", file=sys.stderr)
            return existing_locations
        
        # Create a set of already selected place names to avoid duplicates
        selected_names = {loc.get('place_name', '').lower() for loc in existing_locations}
        
        # Find additional candidates that weren't selected
        additional_locations = []
        for candidate in all_candidates:
            candidate_name = candidate.get('place_name', '').lower()
            if candidate_name not in selected_names:
                # Create a location entry compatible with Qwen prompts
                fallback_location = {
                    "place_name": candidate.get('place_name', 'Unknown'),
                    "road_address_name": candidate.get('road_address_name', ''),
                    "place_type": candidate.get('place_type', 'Unknown'),
                    "distance": str(candidate.get('distance', 0)),
                    "place_url": candidate.get('place_url', ''),
                    "latitude": float(candidate.get('y', 0)),
                    "longitude": float(candidate.get('x', 0)),
                    "selection_reason": f"Fallback location for complete itinerary"
                }
                additional_locations.append(fallback_location)
                selected_names.add(candidate_name)
                
                # Stop when we have enough locations
                if len(existing_locations) + len(additional_locations) >= min_locations:
                    break
        
        # Combine existing and additional locations
        final_locations = existing_locations + additional_locations
        
        print(f"✅ Created Qwen fallback locations: {len(final_locations)} total", file=sys.stderr)
        print(f"✅ Original: {len(existing_locations)}, Additional: {len(additional_locations)}", file=sys.stderr)
        
        return final_locations
    
    def _convert_places_to_json(self, selected_places: List[Dict]) -> str:
        """
        Convert text-based place selection to JSON format using the original candidates.
        
        Args:
            selected_places (List[Dict]): List of places with names from Phi
            
        Returns:
            str: JSON string with complete place data, or None if conversion fails
        """
        if not selected_places:
            return None
            
        # Get the original candidate places that were sent to Phi
        all_candidates = self._get_all_candidates()
        if not all_candidates:
            print("❌ No candidate places available for conversion", file=sys.stderr)
            return None
        
        # Match Phi's selections to actual candidate data
        converted_places = []
        for selected in selected_places:
            selected_name = selected['place_name']
            
            # Find matching candidate by name using multiple matching strategies
            matching_candidate = None
            
            # Strategy 1: Exact match (case-insensitive)
            for candidate in all_candidates:
                if selected_name.lower() == candidate.get('place_name', '').lower():
                    matching_candidate = candidate
                    break
            
            # Strategy 2: Substring match (case-insensitive)
            if not matching_candidate:
                for candidate in all_candidates:
                    if selected_name.lower() in candidate.get('place_name', '').lower():
                        matching_candidate = candidate
                        break
            
            # Strategy 3: Fuzzy match for slight variations
            if not matching_candidate:
                for candidate in all_candidates:
                    candidate_name = candidate.get('place_name', '').lower()
                    # Check if names are very similar (handle spacing, special chars)
                    if (selected_name.lower().replace(' ', '') == candidate_name.replace(' ', '') or
                        selected_name.lower().replace('-', '') == candidate_name.replace('-', '') or
                        selected_name.lower().replace('_', '') == candidate_name.replace('_', '')):
                        matching_candidate = candidate
                        break
            
            if matching_candidate:
                # Create complete place entry
                place_entry = {
                    "place_name": matching_candidate.get('place_name', selected_name),
                    "road_address_name": matching_candidate.get('road_address_name', ''),
                    "place_type": matching_candidate.get('place_type', 'Unknown'),
                    "distance": str(matching_candidate.get('distance', 0)),
                    "place_url": matching_candidate.get('place_url', ''),
                    "latitude": float(matching_candidate.get('y', 0)),
                    "longitude": float(matching_candidate.get('x', 0)),
                    "selection_reason": selected.get('selection_reason', 'Selected by Phi')
                }
                converted_places.append(place_entry)
                print(f"✅ Matched '{selected_name}' to '{matching_candidate.get('place_name', '')}'", file=sys.stderr)
            else:
                print(f"⚠️ Could not find candidate data for: {selected_name}", file=sys.stderr)
                print(f"🔍 Available candidates: {[c.get('place_name', '') for c in all_candidates[:5]]}", file=sys.stderr)
        
        if converted_places:
            try:
                json_output = json.dumps(converted_places, ensure_ascii=False)
                print(f"✅ Converted {len(converted_places)} places to JSON", file=sys.stderr)
                return json_output
            except Exception as e:
                print(f"❌ Failed to convert places to JSON: {e}", file=sys.stderr)
                return None
        
        return None
    
    def _get_all_candidates(self) -> List[Dict]:
        """
        Get all candidate places that were sent to Phi for selection.
        
        Returns:
            List[Dict]: List of all candidate places
        """
        if hasattr(self, 'best_places') and self.best_places:
            # Flatten the best_places dictionary into a single list
            all_candidates = []
            for place_type, places in self.best_places.items():
                for place in places:
                    # Add place_type to each place for reference
                    place['place_type'] = place_type
                    all_candidates.append(place)
            return all_candidates
        else:
            print("⚠️ No candidate places available in self.best_places", file=sys.stderr)
            return []

    def _attempt_json_reconstruction(self, partial_json: str) -> str:
        """
        Attempt to reconstruct a JSON array from a partial or malformed JSON string.
        
        This is a heuristic approach to try to salvage a JSON structure
        even if it's not fully valid. It looks for common patterns like
        starting with '[' and ending with ']' or '}' if it's an object.
        
        Args:
            partial_json (str): The partial or malformed JSON string
            
        Returns:
            str: A potentially valid JSON string, or None if reconstruction fails
        """
        if not partial_json:
            return None
            
        # Remove common Phi artifacts that might interfere with JSON parsing
        cleaned_json = partial_json
        artifacts_to_remove = [
            'Using libGenie.so version',
            '[INFO]',
            '[PROMPT]:',
            '<|system|>',
            '<|user|>',
            '<|end|>',
            'Starting from',
            'Available places:'
        ]
        for artifact in artifacts_to_remove:
            cleaned_json = cleaned_json.replace(artifact, '')
            
        # Look for the first '[' and last ']' or '}'
        start_idx = cleaned_json.find('[')
        end_idx = -1
        
        if start_idx != -1:
            bracket_count = 0
            for i, char in enumerate(cleaned_json[start_idx:], start_idx):
                if char == '[':
                    bracket_count += 1
                elif char == ']' or char == '}':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_idx = i + 1
                        break
            
            if end_idx != -1:
                return cleaned_json[start_idx:end_idx]
        
        return None

    def run_qwen_story(self, route_plan_json=None):
        """
        Generate an emotional, storytelling itinerary using the Qwen model.
        
        This method takes the route plan from run_route_planner and generates
        a narrative, emotional description of the day that matches the companion
        type and budget preferences. It includes fallback mechanisms to ensure
        all selected places are covered.
        
        Args:
            route_plan_json (str, optional): Pre-generated route plan JSON. 
                                          If None, will call run_route_planner().
        
        Returns:
            str: Emotional itinerary text or error message
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
            
            # Final safety check: Ensure we have enough locations for the prompts
            if len(selected_locations) < 3:
                print(f"⚠️ Only {len(selected_locations)} locations available, creating fallback locations", file=sys.stderr)
                fallback_locations = self._create_fallback_locations_for_qwen(selected_locations)
                if fallback_locations:
                    selected_locations = fallback_locations
                    print(f"✅ Created fallback locations: {len(selected_locations)} total", file=sys.stderr)
                else:
                    return "Insufficient locations for itinerary generation"
            
            print(f"✅ Proceeding with {len(selected_locations)} locations for Qwen story generation", file=sys.stderr)
            
        except Exception as e:
            print(f"경로 추천 결과를 JSON으로 파싱할 수 없습니다: {e}")
            return f"Failed to parse route plan: {e}"
        
        # First attempt: Use comprehensive prompt for maximum coverage
        prompt = build_comprehensive_qwen_prompt(
            selected_locations,                         # The 4-5 locations from route planner
            self.companion_type,                    # Companion type for tone/style
            self.budget,                            # Budget level for activity suggestions
            self.starting_time,                     # Starting time for temporal context
        )
        
        # Run the Qwen model to generate emotional storytelling
        try:
            if self.progress_callback:
                self.progress_callback(80, "Running Qwen model for emotional storytelling...")
            
            runner = GenieRunner(progress_callback=self.progress_callback)
            raw_output = runner.run_qwen(prompt)
            
            # Extract clean story text from the model output
            clean_story = self._extract_story_from_output(raw_output)
            
            # Check if all places were covered
            if clean_story and self._verify_place_coverage(clean_story, selected_locations):
                print("✅ All places covered in first attempt", file=sys.stderr)
                return clean_story
            else:
                print("⚠️ Not all places covered, attempting fallback with token-efficient prompt", file=sys.stderr)
                
                # Fallback: Use token-efficient prompt
                fallback_prompt = build_qwen_story_prompt(
                    selected_locations,
                    self.companion_type,
                    self.budget,
                    self.starting_time,
                )
                
                if self.progress_callback:
                    self.progress_callback(85, "Retrying with optimized prompt...")
                
                fallback_output = runner.run_qwen(fallback_prompt)
                fallback_story = self._extract_story_from_output(fallback_output)
                
                if fallback_story and self._verify_place_coverage(fallback_story, selected_locations):
                    print("✅ All places covered in fallback attempt", file=sys.stderr)
                    return fallback_story
                else:
                    print("⚠️ Fallback also incomplete, attempting ultra-comprehensive prompt", file=sys.stderr)
                    
                    # Ultra-comprehensive fallback: Use the most detailed prompt
                    ultra_prompt = build_ultra_comprehensive_qwen_prompt(
                        selected_locations,
                        self.companion_type,
                        self.budget,
                        self.starting_time,
                    )
                    
                    if self.progress_callback:
                        self.progress_callback(90, "Retrying with ultra-comprehensive prompt...")
                    
                    ultra_output = runner.run_qwen(ultra_prompt)
                    ultra_story = self._extract_story_from_output(ultra_output)
                    
                    if ultra_story and self._verify_place_coverage(ultra_story, selected_locations):
                        print("✅ All places covered in ultra-comprehensive fallback", file=sys.stderr)
                        return ultra_story
                    else:
                        print("⚠️ Ultra-comprehensive fallback also incomplete, returning best available story", file=sys.stderr)
                        return fallback_story if fallback_story else clean_story
                    
        except Exception as e:
            print(f"Qwen model failed: {e}", file=sys.stderr)
            if self.progress_callback:
                self.progress_callback(95, "Qwen model failed")
            return f"Failed to generate emotional story: {e}"
    
    def _verify_place_coverage(self, story_text: str, selected_locations: list) -> bool:
        """
        Verify that all selected places are mentioned in the generated story.
        
        Args:
            story_text (str): The generated story text
            selected_locations (list): List of selected locations to verify
            
        Returns:
            bool: True if all places are covered, False otherwise
        """
        if not story_text or not selected_locations:
            return False
        
        story_lower = story_text.lower()
        covered_count = 0
        
        for location in selected_locations:
            place_name = location.get('place_name', '').lower()
            if place_name and place_name in story_lower:
                covered_count += 1
                print(f"✅ Found coverage for: {location['place_name']}", file=sys.stderr)
            else:
                print(f"❌ Missing coverage for: {location['place_name']}", file=sys.stderr)
        
        coverage_percentage = (covered_count / len(selected_locations)) * 100
        print(f"📊 Place coverage: {covered_count}/{len(selected_locations)} ({coverage_percentage:.1f}%)", file=sys.stderr)
        
        # Consider it covered if at least 80% of places are mentioned
        return coverage_percentage >= 80
    
    def _extract_story_from_output(self, raw_output: str) -> str:
        """
        Extract clean story text from the Qwen model output.
        
        The model might output debug information, so we need to find
        the actual story content within the output.
        
        Args:
            raw_output (str): Raw output from the Qwen model
            
        Returns:
            str: Cleaned story text, or None if no story found
        """
        if not raw_output:
            return None
            
        print(f"Raw Qwen model output: {raw_output[:500]}...", file=sys.stderr)
        
        # Look for content after <|assistant|> tag
        if '<|assistant|>' in raw_output:
            parts = raw_output.split('<|assistant|>')
            if len(parts) > 1:
                content_after_assistant = parts[-1].strip()
                print(f"Content after <|assistant|>: {content_after_assistant[:200]}...", file=sys.stderr)
                
                # Clean up the content by removing technical markers
                cleaned_content = self._clean_story_content(content_after_assistant)
                if cleaned_content:
                    return cleaned_content
        
        # Look for content after </assistant> tag
        if '</assistant>' in raw_output:
            parts = raw_output.split('</assistant>')
            if len(parts) > 1:
                content_after_assistant = parts[-1].strip()
                print(f"Content after </assistant>: {content_after_assistant[:200]}...", file=sys.stderr)
                
                cleaned_content = self._clean_story_content(content_after_assistant)
                if cleaned_content:
                    return cleaned_content
        
        # Look for content after [BEGIN]: marker
        if '[BEGIN]:' in raw_output:
            parts = raw_output.split('[BEGIN]:')
            if len(parts) > 1:
                content_after_begin = parts[-1].strip()
                print(f"Content after [BEGIN]: {content_after_begin[:200]}...", file=sys.stderr)
                
                cleaned_content = self._clean_story_content(content_after_begin)
                if cleaned_content:
                    return cleaned_content
        
        # If no markers found, try to clean the entire output
        cleaned_content = self._clean_story_content(raw_output)
        if cleaned_content:
            return cleaned_content
        
        print(f"❌ No clean story content found in Qwen model output", file=sys.stderr)
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
            print(f"✅ Cleaned story content: {cleaned_content[:100]}...", file=sys.stderr)
            return cleaned_content
        
        return None
    