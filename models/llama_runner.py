import subprocess

def run_llama_runner(prompt: str) -> str:
    """
    Runs the Llama LLM with the given prompt using a local executable.
    Writes the prompt to a file and calls the Llama runner.
    Returns the output as a string.
    @param prompt: The prompt to send to the Llama model.
    @return: The output from the Llama model as a string.
    """
    with open("llama_prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt)

    result = subprocess.run([
        "./genie-t2t-run.exe",  # Or "genie-t2t-run" on Linux
        "--model-bundle", "genie_bundle_llama",
        "--input-text", "prompt.txt"
    ], capture_output=True, text=True)

    return result.stdout.strip()

