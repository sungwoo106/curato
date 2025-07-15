from core.prompts import build_phi_prompt
from models.phi_runner import run_phi_runner

# Entry point

prompt = build_phi_prompt(place_type, companion_type, rating, budget, max_distance_km)
phi_output = run_phi_runner(prompt)