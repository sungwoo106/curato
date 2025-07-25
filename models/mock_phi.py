"""Generate mock Phi model output using a working Llama model.

This script builds the Phi route planner prompt using canned Kakao API
responses and sends it to the ``llama_v3_2_3b_instruct`` model.  The result
is written to ``mock_phi_output.txt`` so other parts of the application can
consume it without running the heavy models at runtime.
"""

import json
import os
import sys

# Allow imports when run as a script
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, REPO_ROOT)

from core.prompts import build_phi_four_loc
from constants import LOCATION
from data.api_clients.kakao_api import format_kakao_places_for_prompt
import subprocess

MODEL_ID = "meta-llama/Llama-3.2-3B-Instruct"


def run_cli(prompt: str) -> str:
    """Send the prompt to the QAI Hub model using the CLI."""
    cmd = [
        "qai-hub",
        "submit-profile-job",
        "--model",
        MODEL_ID,
        "--inputs",
        json.dumps({"prompt": [prompt]}),
        "--device",
        "Snapdragon X Elite CRD",
        "--wait",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"qai-hub CLI failed: {result.stderr.strip()}"
        )
    return result.stdout.strip()

def main() -> None:
    """Create a mock route using preset user preferences."""

    # Preset user selections
    companion_type = "Couple"
    budget_level = "medium"  # represents "$$"
    start_time = 12
    selected_types = ["Cafe", "Restaurant"]

    # Load cached Kakao API results and filter to the selected categories
    with open("mock_kakao_output.json", "r", encoding="utf-8") as f:
        kakao_results = json.load(f)

    filtered = {t: kakao_results.get(t, []) for t in selected_types}
    recommendations = format_kakao_places_for_prompt(filtered)

    prompt = build_phi_four_loc(
        LOCATION,
        companion_type,
        start_time,
        budget_level,
        json.dumps(recommendations, ensure_ascii=False),
    )

    response = run_cli(prompt)

    with open("mock_phi_output.txt", "w", encoding="utf-8") as f:
        f.write(response)

    print("Mock output saved to mock_phi_output.txt")

if __name__ == "__main__":
    main()
