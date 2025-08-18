"""
Qwen Language Model Runner (Updated for Genie Integration)

This module now uses the unified Genie runner for better integration
with your phi_bundle and qwen_bundle. It maintains backward compatibility
while leveraging the improved Genie SDK integration.

The module works by:
1. Using the unified GenieRunner class
2. Calling the local genie-t2t-run executable with your qwen_bundle
3. Capturing and returning the generated emotional itinerary output

Note: This requires your pre-configured qwen_bundle and genie-t2t-run
executable to function properly.
"""

from .genie_runner import GenieRunner

# Create a global GenieRunner instance for efficiency
# The GenieRunner will auto-detect paths or use environment variables
_genie_runner = GenieRunner()

def run_qwen_runner(prompt: str) -> str:
    """
    Run the Qwen LLM with the given prompt using the Genie runner.
    
    This function serves as a bridge between the Python application and the
    local Qwen language model. It takes a carefully crafted prompt (built
    by the prompt generation functions) and returns the AI-generated
    emotional itinerary with detailed descriptions and recommendations.
    
    Args:
        prompt (str): The complete prompt to send to the Qwen model.
                     This should include:
                     - System instructions for emotional itinerary generation
                     - Starting location and companion type
                     - Budget and timing constraints
                     - Available place recommendations
                     - Output format requirements (detailed text)
    
    Returns:
        str: The generated emotional itinerary from the Qwen model.
             This should be detailed text describing the day's experience
             with emotional context and recommendations.
    
    Raises:
        RuntimeError: If the Qwen model fails to run
        FileNotFoundError: If the qwen_bundle is not found
    
    Example:
        >>> prompt = "Generate an emotional itinerary for a romantic day..."
        >>> itinerary = run_qwen_runner(prompt)
        >>> print(itinerary)
        'Start your romantic day at Seoul Forest...'
    
    Dependencies:
        - Your pre-configured qwen_bundle
        - genie-t2t-run executable
        - genie_config.json configuration file
    """
    return _genie_runner.run_qwen(prompt)
