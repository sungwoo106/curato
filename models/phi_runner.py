import subprocess

# phi_runner for when on Windows
def run_phi_runner(prompt: str) -> str:
    with open("phi_prompt.txt", "w") as f:
        f.write(prompt)

    result = subprocess.run([
        "./genie-t2t-run.exe",  # Or "genie-t2t-run" on Linux
        "--model-bundle", "genie_bundle_phi",
        "--input-text", "prompt.txt"
    ], capture_output=True, text=True)

    return result.stdout.strip()

'''
# phi_runner for mock response
def run_phi_runner(prompt: str) -> str:
    return "1. 서울숲\n2. 북서울 꿈의숲\n3. 응봉산"
'''