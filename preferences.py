from core.prompts import build_phi_four_loc, build_llama_emotional_prompt
from models.phi_runner import run_phi_runner
from models.llama_runner import run_llama_runner
from data.api_clients.kakao_api import get_closest_place, format_kakao_places_for_prompt
from constants import USER_SELECTABLE_PLACE_TYPES, COMPANION_PLACE_TYPES, COMPANION_TYPES, BUDGET, LOCATION, MAX_DISTANCE_KM, STARTING_TIME
import random
import json

class Preferences:
    def __init__(self,
                 companion_type=COMPANION_TYPES[0],
                 budget=BUDGET[0],
                 starting_time=STARTING_TIME,
                 max_distance_km=MAX_DISTANCE_KM,
                 start_location=LOCATION):
        self.companion_type = companion_type
        self.budget = budget
        self.starting_time = starting_time
        self.max_distance_km = max_distance_km
        self.start_location = start_location
        self.selected_types = []
        self.best_places = {}
        self.recommendations_json = []

    def set_start_location(self, start_location: tuple):
        self.start_location = start_location

    def set_companion_type(self, companion_type: str):
        self.companion_type = companion_type

    def set_budget(self, budget: str):
        self.budget = budget

    def set_starting_time(self, starting_time: int):
        self.starting_time = starting_time

    def set_max_distance_km(self, max_distance_km: int):
        self.max_distance_km = max_distance_km

    def select_place_types(self, user_selected_types=None):
        companion_places = COMPANION_PLACE_TYPES.get(self.companion_type.lower(), [])
        num_to_select = random.choice([4, 5])
        random_types = []
        if len(companion_places) >= num_to_select:
            random_types = random.sample(companion_places, num_to_select)
        else:
            random_types = companion_places.copy()
        # Combine user selected types and random companion types, ensuring uniqueness
        combined_types = set(random_types)
        if user_selected_types:
            combined_types.update(user_selected_types)
        self.selected_types = list(combined_types)
        if not self.selected_types:
            self.selected_types = [USER_SELECTABLE_PLACE_TYPES[0]]

    def collect_best_place(self):
        # returns in a dictionary format where keys are place types and values are lists of places
        self.best_places = {}
        for pt in self.selected_types:
            best_place = get_closest_place(
                pt,
                self.start_location[0],
                self.start_location[1],
                int(self.max_distance_km * 1000),
                10,
            )
            self.best_places[pt] = [best_place] if best_place else []

    def format_recommendations(self):
        self.recommendations_json = format_kakao_places_for_prompt(self.best_places)
        return self.recommendations_json

    def run_route_planner(self):
        # Build and run the route planner prompt for 4 locations
        """Run the Phi model to generate a one day route."""
        self.collect_best_place()
        recommendations = self.format_recommendations()
        prompt = build_phi_four_loc(
            self.start_location,
            self.companion_type,
            self.starting_time,
            self.budget,
            json.dumps(recommendations, ensure_ascii=False),
        )
        # return run_phi_runner(prompt)
        return "[]"

    def run_llama_story(self):
        """
        Runs the llama prompt using the output from run_route_planner (expected to be a JSON array of 4 locations).
        """
        route_plan_json = self.run_route_planner()
        try:
            four_locations = json.loads(route_plan_json)
        except Exception as e:
            print(f"경로 추천 결과를 JSON으로 파싱할 수 없습니다: {e}")
            return None
        prompt = build_llama_emotional_prompt(
            four_locations,
            self.companion_type,
            self.budget,
        )
        # return run_llama_runner(prompt)
        return "Generated itinerary would appear here"
    