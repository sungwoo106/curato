from core.prompts import build_phi_prompt
from models.phi_runner import run_phi_runner
from constants import PLACE_TYPES, COMPANION_TYPES, MIN_RATING, BUDGET, LOCATION, MAX_DISTANCE_KM

class Preferences:
    def __init__(self,
                 place_type=PLACE_TYPES[0],
                 companion_type=COMPANION_TYPES[0],
                 rating=MIN_RATING,
                 budget=BUDGET,
                 max_distance_km=MAX_DISTANCE_KM,
                 location=LOCATION):
        self.place_type = place_type
        self.companion_type = companion_type
        self.rating = rating
        self.budget = budget
        self.max_distance_km = max_distance_km
        self.location = location

    def set_location(self, location: str):
        self.location = location

    def set_place_type(self, place_type: str):
        self.place_type = place_type

    def set_companion_type(self, companion_type: str):
        self.companion_type = companion_type

    def set_rating(self, rating: float):
        self.rating = rating

    def set_budget(self, budget: int):
        self.budget = budget

    def set_max_distance_km(self, max_distance_km: int):
        self.max_distance_km = max_distance_km

    def run(self):
        prompt = build_phi_prompt(
            self.place_type,
            self.companion_type,
            self.rating,
            self.budget,
            self.max_distance_km
        )
        return run_phi_runner(prompt)