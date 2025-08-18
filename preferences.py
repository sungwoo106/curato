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

from core.prompts import build_phi_location_prompt, build_qwen_story_prompt
from models.genie_runner import GenieRunner
from data.api_clients.kakao_api import get_closest_place, format_kakao_places_for_prompt
from constants import USER_SELECTABLE_PLACE_TYPES, COMPANION_PLACE_TYPES, COMPANION_TYPES, BUDGET, LOCATION, MAX_DISTANCE_KM, STARTING_TIME
import random
import json
import sys

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
        Collect the best place recommendations for each selected place type.
        
        This method queries the Kakao Map API to find the closest and most
        relevant places for each selected place type within the specified
        distance radius.
        
        Returns:
            dict: Dictionary where keys are place types and values are lists of places
        """
        self.best_places = {}
        
        for pt in self.selected_types:
            # Search for the closest place of this type within the distance limit
            best_place = get_closest_place(
                pt,                                    # Place type to search for
                self.start_location[0],                # Latitude
                self.start_location[1],                # Longitude
                int(self.max_distance_km * 1000),      # Distance in meters
                10,                                    # Number of results to return
            )
            
            # Store the result (even if empty) for this place type
            self.best_places[pt] = [best_place] if best_place else []

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
        1. Collects place recommendations from Kakao API
        2. Builds a prompt for the Phi model
        3. Generates a route plan with 4-5 locations
        4. Returns the result as JSON
        
        Returns:
            str: JSON string with route plan or None if failed
        """
        try:
            # Collect place recommendations
            if self.progress_callback:
                self.progress_callback(60, "Collecting place recommendations...")
            
            self.collect_best_place()
            
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
                fallback_plan = self._create_fallback_route_plan()
                return fallback_plan
            
        except Exception as e:
            print(f"Route planner failed: {e}", file=sys.stderr)
            if self.progress_callback:
                self.progress_callback(75, "Route planning failed")
            
            # Try fallback as last resort
            try:
                if self.progress_callback:
                    self.progress_callback(75, "Attempting fallback route plan...")
                fallback_plan = self._create_fallback_route_plan()
                return fallback_plan
            except Exception as fallback_error:
                print(f"Fallback route plan also failed: {fallback_error}", file=sys.stderr)
                return None
    
    def _create_fallback_route_plan(self) -> str:
        """
        Create a fallback route plan when the Phi model fails.
        
        This method creates a basic route plan using the collected place recommendations
        to ensure the user gets a usable itinerary even when AI generation fails.
        
        Returns:
            str: JSON string with fallback route plan
        """
        try:
            # Use the actual collected place recommendations if available
            if hasattr(self, 'best_places') and self.best_places:
                fallback_plan = []
                
                # Select up to 5 places from different categories
                selected_categories = list(self.best_places.keys())[:5]
                
                for category in selected_categories:
                    if category in self.best_places and self.best_places[category]:
                        # Take the first place from each category
                        place = self.best_places[category][0]
                        
                        fallback_place = {
                            "place_name": place.get('place_name', f"{category} Location"),
                            "road_address_name": place.get('road_address_name', 'Address not available'),
                            "place_type": category,
                            "distance": place.get('distance', 'Distance not available'),
                            "place_url": place.get('place_url', ''),
                            "latitude": place.get('latitude', 37.5665),
                            "longitude": place.get('longitude', 126.9780)
                        }
                        fallback_plan.append(fallback_place)
                
                if fallback_plan:
                    print(f"✅ Created fallback route plan with {len(fallback_plan)} locations", file=sys.stderr)
                    return json.dumps(fallback_plan, ensure_ascii=False)
            
            # If no collected places available, use the original hardcoded fallback
            print("⚠️ No collected places available, using hardcoded fallback", file=sys.stderr)
            fallback_plan = [
                {
                    "place_name": "홍대입구역",
                    "road_address_name": "서울 마포구 양화로 160",
                    "place_type": "Transportation",
                    "distance": "0km",
                    "place_url": "https://map.kakao.com/...",
                    "latitude": 37.5563,
                    "longitude": 126.9237
                },
                {
                    "place_name": "몰레꼴레 와이즈파크홍대점",
                    "road_address_name": "서울 마포구 양화로 188",
                    "place_type": "Restaurant",
                    "distance": "0.3km",
                    "place_url": "https://map.kakao.com/...",
                    "latitude": 37.5570,
                    "longitude": 126.9240
                },
                {
                    "place_name": "공미학 마포홍대점",
                    "road_address_name": "서울 마포구 양화로 200",
                    "place_type": "Cafe",
                    "distance": "0.5km",
                    "place_url": "https://map.kakao.com/...",
                    "latitude": 37.5575,
                    "longitude": 126.9245
                },
                {
                    "place_name": "트릭아이뮤지엄",
                    "road_address_name": "서울 마포구 양화로 220",
                    "place_type": "Museum",
                    "distance": "0.7km",
                    "place_url": "https://map.kakao.com/...",
                    "latitude": 37.5580,
                    "longitude": 126.9250
                }
            ]
            
            return json.dumps(fallback_plan, ensure_ascii=False)
            
        except Exception as e:
            print(f"❌ Failed to create fallback route plan: {e}", file=sys.stderr)
            return None

    def _extract_json_from_output(self, raw_output: str) -> str:
        """
        Extract JSON content from the raw model output.
        
        The model might output debug information, so we need to find
        the actual JSON content within the output.
        
        Args:
            raw_output (str): Raw output from the Phi model
            
        Returns:
            str: Cleaned JSON string, or None if no valid JSON found
        """
        if not raw_output:
            return None
            
        print(f"Raw Phi model output: {raw_output[:500]}...", file=sys.stderr)
            
        # Look for JSON content in the output
        # Try to find content between [ and ] or { and }
        import re
        
        # Look for JSON array or object patterns
        json_patterns = [
            r'\[.*\]',  # JSON array
            r'\{.*\}',  # JSON object
        ]
        
        # First, try to find JSON in the entire output
        for pattern in json_patterns:
            matches = re.findall(pattern, raw_output, re.DOTALL)
            for match in matches:
                try:
                    # Validate that it's actually valid JSON
                    json.loads(match)
                    print(f"✅ Found valid JSON: {match[:100]}...", file=sys.stderr)
                    return match
                except json.JSONDecodeError:
                    continue
        
        # If no JSON found, try to extract content after the last [PROMPT]: marker
        if '[PROMPT]:' in raw_output:
            parts = raw_output.split('[PROMPT]:')
            if len(parts) > 1:
                content_after_prompt = parts[-1].strip()
                print(f"Content after [PROMPT]: {content_after_prompt[:200]}...", file=sys.stderr)
                
                # Look for JSON in this content
                for pattern in json_patterns:
                    matches = re.findall(pattern, content_after_prompt, re.DOTALL)
                    for match in matches:
                        try:
                            json.loads(match)
                            print(f"✅ Found valid JSON after prompt: {match[:100]}...", file=sys.stderr)
                            return match
                        except json.JSONDecodeError:
                            continue
        
        # Try to find content after the last </assistant> tag
        if '</assistant>' in raw_output:
            parts = raw_output.split('</assistant>')
            if len(parts) > 1:
                content_after_assistant = parts[-1].strip()
                print(f"Content after </assistant>: {content_after_assistant[:200]}...", file=sys.stderr)
                
                # Look for JSON in this content
                for pattern in json_patterns:
                    matches = re.findall(pattern, content_after_assistant, re.DOTALL)
                    for match in matches:
                        try:
                            json.loads(match)
                            print(f"✅ Found valid JSON after assistant tag: {match[:100]}...", file=sys.stderr)
                            return match
                        except json.JSONDecodeError:
                            continue
        
        # Try to find content after the last <|assistant|> tag
        if '<|assistant|>' in raw_output:
            parts = raw_output.split('<|assistant|>')
            if len(parts) > 1:
                content_after_assistant = parts[-1].strip()
                print(f"Content after <|assistant|>: {content_after_assistant[:200]}...", file=sys.stderr)
                
                # Look for JSON in this content
                for pattern in json_patterns:
                    matches = re.findall(pattern, content_after_assistant, re.DOTALL)
                    for match in matches:
                        try:
                            json.loads(match)
                            print(f"✅ Found valid JSON after <|assistant|> tag: {match[:100]}...", file=sys.stderr)
                            return match
                        except json.JSONDecodeError:
                            continue
        
        # If still no JSON, try to find any content that looks like a response
        # Look for lines that might contain location information
        lines = raw_output.split('\n')
        for line in lines:
            line = line.strip()
            # Skip empty lines, debug info, and prompt content
            if (line and 
                not line.startswith('Using libGenie.so') and
                not line.startswith('[INFO]') and
                not line.startswith('[PROMPT]:') and
                not line.startswith('<|system|>') and
                not line.startswith('<|user|>') and
                not line.startswith('<|assistant|>') and
                not line.startswith('<|end|>') and
                not line.startswith('Starting from') and
                not line.startswith('Available places:')):
                
                # Check if this line might contain JSON-like content
                if ('[' in line and ']' in line) or ('{' in line and '}' in line):
                    try:
                        json.loads(line)
                        print(f"✅ Found JSON in line: {line[:100]}...", file=sys.stderr)
                        return line
                    except json.JSONDecodeError:
                        continue
        
        # Last resort: try to find any text that looks like it might be a response
        # Look for lines that contain location-related keywords
        location_keywords = ['place_name', 'road_address_name', 'place_type', 'distance', 'latitude', 'longitude']
        for line in lines:
            line = line.strip()
            if any(keyword in line for keyword in location_keywords):
                print(f"🔍 Found potential location data line: {line[:100]}...", file=sys.stderr)
                # Try to extract JSON from this line
                for pattern in json_patterns:
                    matches = re.findall(pattern, line, re.DOTALL)
                    for match in matches:
                        try:
                            json.loads(match)
                            print(f"✅ Found valid JSON in location line: {match[:100]}...", file=sys.stderr)
                            return match
                        except json.JSONDecodeError:
                            continue
        
        print(f"❌ No valid JSON found in Phi model output", file=sys.stderr)
        return None

    def run_qwen_story(self):
        """
        Generate an emotional, storytelling itinerary using the Qwen model.
        
        This method takes the route plan from run_route_planner and generates
        a narrative, emotional description of the day that matches the companion
        type and budget preferences.
        
        Returns:
            str: Emotional itinerary text or error message
        """
        # Get the route plan from the route planner
        route_plan_json = self.run_route_planner()
        
        if not route_plan_json:
            return "Failed to generate route plan - cannot create itinerary"
        
        try:
            # Parse the JSON route plan
            selected_locations = json.loads(route_plan_json)
        except Exception as e:
            print(f"경로 추천 결과를 JSON으로 파싱할 수 없습니다: {e}")
            return f"Failed to parse route plan: {e}"
        
        # Build the prompt for the Qwen model to generate emotional storytelling
        prompt = build_qwen_story_prompt(
            selected_locations,                         # The 4-5 locations from route planner
            self.companion_type,                    # Companion type for tone/style
            self.budget,                            # Budget level for activity suggestions
        )
        
        # Run the Qwen model to generate emotional storytelling
        try:
            if self.progress_callback:
                self.progress_callback(80, "Running Qwen model for emotional storytelling...")
            
            runner = GenieRunner(progress_callback=self.progress_callback)
            return runner.run_qwen(prompt)
        except Exception as e:
            print(f"Qwen model failed: {e}", file=sys.stderr)
            if self.progress_callback:
                self.progress_callback(95, "Qwen model failed")
            return f"Failed to generate emotional story: {e}"
    