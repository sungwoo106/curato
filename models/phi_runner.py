"""
Phi Language Model Runner

This module provides an interface to run the Phi language model locally for
generating optimal route plans. It handles the communication between the
Python application and the local Phi executable.

The module works by:
1. Writing the generated prompt to a temporary text file
2. Calling the local Phi executable with the prompt file
3. Capturing and returning the generated route plan output

Note: This requires a local installation of the Phi model and the genie-t2t-run
executable to function properly.

The module includes both the active Windows implementation and a commented
mock response alternative for testing purposes.
"""

import subprocess

def run_phi_runner(prompt: str) -> str:
    """
    Run the Phi LLM with the given prompt using a local executable.
    
    This function serves as a bridge between the Python application and the
    local Phi language model. It takes a carefully crafted prompt (built
    by the prompt generation functions) and returns the AI-generated
    route plan with 4 optimal locations for the day.
    
    The function works by:
    1. Writing the prompt to a temporary text file (phi_prompt.txt)
    2. Executing the local Phi runner with the prompt file
    3. Capturing the stdout output and returning it as a string
    
    Args:
        prompt (str): The complete prompt to send to the Phi model.
                     This should include:
                     - System instructions for route planning
                     - Starting location and companion type
                     - Budget and timing constraints
                     - Available place recommendations
                     - Output format requirements (JSON)
    
    Returns:
        str: The generated route plan from the Phi model.
             This should be a JSON string containing 4 locations
             with their details (name, address, type, coordinates, etc.)
    
    Raises:
        subprocess.CalledProcessError: If the Phi executable fails to run
        FileNotFoundError: If the genie-t2t-run executable is not found
        OSError: For other system-related errors during execution
    
    Example:
        >>> prompt = "Choose 4 locations for a one-day route..."
        >>> route_plan = run_phi_runner(prompt)
        >>> print(route_plan)
        '[{"place_name": "Seoul Forest", "road_address_name": "..."}]'
    
    Dependencies:
        - Local installation of Phi model
        - genie-t2t-run executable in the current directory
        - genie_bundle_phi model bundle
    """
    # Write the prompt to a temporary text file
    # This allows the Phi executable to read the prompt input
    # The file is created with default encoding (UTF-8 on most systems)
    with open("phi_prompt.txt", "w") as f:
        f.write(prompt)

    # Execute the local Phi runner using subprocess
    # This runs the genie-t2t-run executable with the appropriate parameters
    result = subprocess.run(
        [
            "./genie-t2t-run.exe",  # Windows executable (use "./genie-t2t-run" on Linux/Mac)
            "--model-bundle",        # Specify the model bundle to use
            "genie_bundle_phi",      # Phi model bundle name
            "--input-text",          # Specify input method
            "phi_prompt.txt",        # Input file containing the prompt
        ],
        capture_output=True,         # Capture both stdout and stderr
        text=True,                   # Return output as text (not bytes)
    )

    # Return the generated route plan, stripping any leading/trailing whitespace
    # The stdout contains the AI-generated route plan (expected to be JSON)
    return result.stdout.strip()

# =============================================================================
# MOCK RESPONSE ALTERNATIVE (COMMENTED OUT)
# =============================================================================
'''
# phi_runner for mock response
# This alternative implementation returns a hardcoded route plan for testing
# purposes when the actual Phi model is not available or working.
def run_phi_runner(prompt: str) -> str:
    """
    Mock implementation that returns a hardcoded route plan.
    
    This function is used for testing and development when the actual
    Phi model is not available. It returns a predefined list of
    popular Seoul locations that can be used to test the itinerary
    generation workflow.
    
    Args:
        prompt (str): The prompt (ignored in mock implementation)
    
    Returns:
        str: Hardcoded route plan with 3 popular Seoul locations
    """
    return "1. 서울숲\n2. 북서울 꿈의숲\n3. 응봉산"
'''
