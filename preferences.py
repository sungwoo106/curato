"""
Edge Day Planner - Preferences and Itinerary Generation Engine

This module contains the core Preferences class that manages user preferences and
generates personalized itineraries. It orchestrates the entire workflow from
user input to final itinerary generation, including:
- Managing companion type, budget, timing, and location preferences
- Selecting appropriate place types based on companion type
- Collecting place recommendations from external APIs
- Generating route plans and emotional storytelling content

The class serves as the main interface between the UI layer and the backend
AI models and external services.
"""

from core.prompts import build_phi_four_loc, build_llama_emotional_prompt
from models.phi_runner import run_phi_runner
from models.llama_runner import run_llama_runner
from data.api_clients.kakao_api import get_closest_place, format_kakao_places_for_prompt
from constants import USER_SELECTABLE_PLACE_TYPES, COMPANION_PLACE_TYPES, COMPANION_TYPES, BUDGET, LOCATION, MAX_DISTANCE_KM, STARTING_TIME
import random
import json

class Preferences:
    """
    Main class for managing user preferences and generating personalized itineraries.
    
    This class encapsulates all the logic needed to create a customized day plan
    based on user preferences including companion type, budget, timing, and location.
    It coordinates between different services (Kakao API, AI models) to generate
    coherent and enjoyable itineraries.
    """
    
    def __init__(self,
                 companion_type=COMPANION_TYPES[0],
                 budget=BUDGET[0],
                 starting_time=STARTING_TIME,
                 max_distance_km=MAX_DISTANCE_KM,
                 start_location=LOCATION):
        """
        Initialize a new Preferences instance with user preferences.
        
        Args:
            companion_type (str): Type of outing (Solo, Couple, Friends, Family)
            budget (str): Budget level (low, medium, high)
            starting_time (int): Starting time in 24-hour format (0-23)
            max_distance_km (int): Maximum search radius in kilometers
            start_location (tuple): Starting coordinates (latitude, longitude)
        """
        # Core user preferences
        self.companion_type = companion_type
        self.budget = budget
        self.starting_time = starting_time
        self.max_distance_km = max_distance_km
        self.start_location = start_location
        
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
        Generate an optimal one-day route using the Phi model.
        
        This method:
        1. Collects place recommendations
        2. Builds a prompt for the Phi model
        3. Generates a route plan with 4 optimal locations
        
        Note: Currently returns a placeholder as the Phi model integration is pending.
        
        Returns:
            str: JSON string containing the route plan (currently placeholder)
        """
        # Collect and format place recommendations
        self.collect_best_place()
        recommendations = self.format_recommendations()
        
        # Build the prompt for the Phi model to generate a 4-location route
        prompt = build_phi_four_loc(
            self.start_location,                    # Starting coordinates
            self.companion_type,                    # Companion type for context
            self.starting_time,                     # Starting time for timing
            self.budget,                            # Budget level for cost considerations
            json.dumps(recommendations, ensure_ascii=False),  # Place recommendations
        )
        
        # TODO: Uncomment when Phi model integration is complete
        # return run_phi_runner(prompt)
        return "[]"

    def run_llama_story(self):
        """
        Generate an emotional, storytelling itinerary using the Llama model.
        
        This method takes the route plan from run_route_planner and generates
        a narrative, emotional description of the day that matches the companion
        type and budget preferences.
        
        Returns:
            str: Emotional itinerary text or error message
        """
        # Get the route plan from the route planner
        route_plan_json = self.run_route_planner()
        
        try:
            # Parse the JSON route plan
            four_locations = json.loads(route_plan_json)
        except Exception as e:
            print(f"경로 추천 결과를 JSON으로 파싱할 수 없습니다: {e}")
            return None
        
        # Build the prompt for the Llama model to generate emotional storytelling
        prompt = build_llama_emotional_prompt(
            four_locations,                         # The 4 locations from route planner
            self.companion_type,                    # Companion type for tone/style
            self.budget,                            # Budget level for activity suggestions
        )
        
        # TODO: Uncomment when Llama model integration is complete
        # return run_llama_runner(prompt)
        return "Generated itinerary would appear here"
    