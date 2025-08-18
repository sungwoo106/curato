"""
Edge Day Planner - Llama Language Model Runner

This module provides an interface to run the Llama language model locally for
generating emotional, storytelling itineraries. It handles the communication
between the Python application and the local Llama executable.

The module works by:
1. Writing the generated prompt to a temporary text file
2. Calling the local Llama executable with the prompt file
3. Capturing and returning the generated text output

Note: This requires a local installation of the Llama model and the genie-t2t-run
executable to function properly.
"""

import subprocess

def run_llama_runner(prompt: str) -> str:
    """
    Run the Llama LLM with the given prompt using a local executable.
    
    This function serves as a bridge between the Python application and the
    local Llama language model. It takes a carefully crafted prompt (built
    by the prompt generation functions) and returns the AI-generated
    emotional itinerary text.
    
    The function works by:
    1. Writing the prompt to a temporary text file (llama_prompt.txt)
    2. Executing the local Llama runner with the prompt file
    3. Capturing the stdout output and returning it as a string
    
    Args:
        prompt (str): The complete prompt to send to the Llama model.
                     This should include system instructions, user context,
                     and any specific formatting requirements.
                     
                     Example prompt structure:
                     - System instructions for tone and style
                     - Location information and companion type
                     - Budget-specific activity suggestions
                     - Style guidelines for the output
    
    Returns:
        str: The generated itinerary text from the Llama model.
             This will be a narrative, emotional description of the day
             that matches the specified companion type and budget.
    
    Raises:
        subprocess.CalledProcessError: If the Llama executable fails to run
        FileNotFoundError: If the genie-t2t-run executable is not found
        OSError: For other system-related errors during execution
    
    Example:
        >>> prompt = "Generate a romantic itinerary for a couple visiting..."
        >>> itinerary = run_llama_runner(prompt)
        >>> print(itinerary)
        "As the morning sun casts golden rays over Seoul..."
    
    Dependencies:
        - Local installation of Llama model
        - genie-t2t-run executable in the current directory
        - genie_bundle_llama model bundle
    """
    # Write the prompt to a temporary text file
    # This allows the Llama executable to read the prompt input
    # The file is created with UTF-8 encoding to handle Korean text properly
    with open("llama_prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt)

    # Execute the local Llama runner using subprocess
    # This runs the genie-t2t-run executable with the appropriate parameters
    result = subprocess.run(
        [
            "./genie-t2t-run.exe",  # Windows executable (use "./genie-t2t-run" on Linux/Mac)
            "--model-bundle",        # Specify the model bundle to use
            "genie_bundle_llama",    # Llama model bundle name
            "--input-text",          # Specify input method
            "llama_prompt.txt",      # Input file containing the prompt
        ],
        capture_output=True,         # Capture both stdout and stderr
        text=True,                   # Return output as text (not bytes)
    )

    # Return the generated text, stripping any leading/trailing whitespace
    # The stdout contains the AI-generated itinerary text
    return result.stdout.strip()
