"""
Phi Language Model Runner (Updated for Genie Integration)

This module now uses the unified Genie runner for better integration
with your phi_bundle and qwen_bundle. It maintains backward compatibility
while leveraging the improved Genie SDK integration.

The module works by:
1. Using the unified GenieRunner class
2. Calling the local genie-t2t-run executable with your phi_bundle
3. Capturing and returning the generated route plan output

Note: This requires your pre-configured phi_bundle and genie-t2t-run
executable to function properly.
"""

from .genie_runner import GenieRunner

# Create a global GenieRunner instance for efficiency
# The GenieRunner will auto-detect paths or use environment variables
_genie_runner = GenieRunner()

def run_phi_runner(prompt: str) -> str:
    """
    Run the Phi LLM with the given prompt using the Genie runner.
    
    This function serves as a bridge between the Python application and the
    local Phi language model. It takes a carefully crafted prompt (built
    by the prompt generation functions) and returns the AI-generated
    route plan with 4 optimal locations for the day.
    
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
        RuntimeError: If the Phi model fails to run
        FileNotFoundError: If the phi_bundle is not found
    
    Example:
        >>> prompt = "Choose 4 locations for a one-day route..."
        >>> route_plan = run_phi_runner(prompt)
        >>> print(route_plan)
        '[{"place_name": "Seoul Forest", "road_address_name": "..."}]'
    
    Dependencies:
        - Your pre-configured phi_bundle
        - genie-t2t-run executable
        - genie_config.json configuration file
    """
    return _genie_runner.run_phi(prompt)
