from core.prompts import build_phi_prompt, build_phi_four_loc
from models.phi_runner import run_phi_runner
from data.api_clients.kakao_api import search_places, format_kakao_places_for_prompt
from constants import USER_SELECTABLE_PLACE_TYPES, COMPANION_PLACE_TYPES, COMPANION_TYPES, BUDGET, LOCATION, MAX_DISTANCE_KM, STARTING_TIME
import random
import json

class Preferences:
    def __init__(self,
                 companion_type=COMPANION_TYPES[0],
                 budget=BUDGET,
                 starting_time=STARTING_TIME,
                 max_distance_km=MAX_DISTANCE_KM,
                 start_location=LOCATION):
        self.companion_type = companion_type
        self.budget = budget
        self.starting_time = starting_time
        self.max_distance_km = max_distance_km
        self.start_location = start_location
        self.selected_types = []
        self.phi_outputs = {}
        self.recommendations_json = []

    def set_start_location(self, start_location: tuple):
        self.start_location = start_location

    def set_companion_type(self, companion_type: str):
        self.companion_type = companion_type

    def set_budget(self, budget: int):
        self.budget = budget

    def set_starting_time(self, starting_time: int):
        self.starting_time = starting_time

    def set_max_distance_km(self, max_distance_km: int):
        self.max_distance_km = max_distance_km

    def select_place_types(self, user_selected_types=None):
        companion_places = COMPANION_PLACE_TYPES.get(self.companion_type, [])
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

    def collect_phi_outputs(self):
        self.phi_outputs = {}
        for pt in self.selected_types:
            prompt = build_phi_prompt(
                self.start_location,
                pt,
                self.companion_type,
                self.starting_time,
                self.max_distance_km,
                search_places(pt, self.start_location, 0, 1000, 10)
            )
            phi_output = run_phi_runner(prompt)
            try:
                phi_json = json.loads(phi_output)
                self.phi_outputs[pt] = phi_json.get('documents', [])
            except Exception as e:
                print(f"{pt} 결과를 JSON으로 파싱할 수 없습니다: {e}")

    def format_recommendations(self):
        self.recommendations_json = format_kakao_places_for_prompt(self.phi_outputs)
        return self.recommendations_json

    def run_route_planner(self):
        # Build and run the route planner prompt for 4 locations
        recommendations_json = self.format_recommendations()
        prompt = build_phi_four_loc(
            self.start_location,
            self.companion_type,
            self.starting_time,
            self.budget,
            recommendations_json
        )
        return run_phi_runner(prompt)