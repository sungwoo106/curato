from core.prompts import build_phi_prompt
from models.phi_runner import run_phi_runner
from data.api_clients.kakao_api import search_places
from constants import USER_SELECTABLE_PLACE_TYPES, COMPANION_TYPES, BUDGET, LOCATION, MAX_DISTANCE_KM, STARTING_TIME

class Preferences:
    def __init__(self,
                 place_type=USER_SELECTABLE_PLACE_TYPES[0],
                 companion_type=COMPANION_TYPES[0],
                 budget=BUDGET,
                 starting_time=STARTING_TIME,
                 max_distance_km=MAX_DISTANCE_KM,
                 location=LOCATION):
        self.place_type = place_type
        self.companion_type = companion_type
        self.budget = budget
        self.starting_time = starting_time
        self.max_distance_km = max_distance_km
        self.location = location

    def set_location(self, location: tuple):
        self.location = location

    def set_place_type(self, place_type: str):
        self.place_type = place_type

    def set_companion_type(self, companion_type: str):
        self.companion_type = companion_type

    def set_budget(self, budget: int):
        self.budget = budget

    def set_starting_time(self, starting_time: int):
        self.starting_time = starting_time

    def set_max_distance_km(self, max_distance_km: int):
        self.max_distance_km = max_distance_km

    def run(self):
        prompt = build_phi_prompt(
            self.location,
            self.place_type,
            self.companion_type,
            self.budget,
            self.starting_time,
            self.max_distance_km,
            search_places(self.place_type, self.location, 0, 1000, 10)  # Fetch places around the location
        )
        return run_phi_runner(prompt)