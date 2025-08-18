"""
Qwen Language Model Runner (Updated for Genie Integration)

This module now uses the unified Genie runner for better integration
with your phi_bundle and qwen_bundle. It maintains backward compatibility
while leveraging the improved Genie SDK integration.

Note: This module is named 'llama_runner' for backward compatibility,
but it actually runs the Qwen model as per your current setup.

The module works by:
1. Using the unified GenieRunner class
2. Calling the local genie-t2t-run executable with your qwen_bundle
3. Capturing and returning the generated emotional itinerary text

Note: This requires your pre-configured qwen_bundle and genie-t2t-run
executable to function properly.
"""

from .genie_runner import GenieRunner

# Create a global GenieRunner instance for efficiency
# The GenieRunner will auto-detect paths or use environment variables
_genie_runner = GenieRunner()

def run_llama_runner(prompt: str) -> str:
    """
    Run the Qwen LLM with the given prompt using the Genie runner.
    
    This function serves as a bridge between the Python application and the
    local Qwen language model. It takes a carefully crafted prompt (built
    by the prompt generation functions) and returns the AI-generated
    emotional itinerary text.
    
    Args:
        prompt (str): The complete prompt to send to the Qwen model.
                     This should include:
                     - System instructions for tone and style
                     - Location information and companion type
                     - Budget-specific activity suggestions
                     - Style guidelines for the output
    
    Returns:
        str: The generated itinerary text from the Qwen model.
             This will be a narrative, emotional description of the day
             that matches the specified companion type and budget.
    
    Raises:
        RuntimeError: If the Qwen model fails to run
        FileNotFoundError: If the qwen_bundle is not found
    
    Example:
        >>> prompt = "Generate a romantic itinerary for a couple visiting..."
        >>> itinerary = run_llama_runner(prompt)
        >>> print(itinerary)
        "As the morning sun casts golden rays over Seoul..."
    
    Dependencies:
        - Your pre-configured qwen_bundle
        - genie-t2t-run executable
        - genie_config.json configuration file
    """
    return _genie_runner.run_qwen(prompt)
