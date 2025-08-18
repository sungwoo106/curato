"""
Configuration file for Edge Day Planner

This file contains all the configurable paths and settings for the application.
You can modify these values to match your system setup without changing the main code.

Environment Variables (recommended):
- PHI_BUNDLE_PATH: Path to your phi_bundle directory
- QWEN_BUNDLE_PATH: Path to your qwen_bundle directory  
- GENIE_EXECUTABLE_PATH: Path to genie-t2t-run.exe

If environment variables are not set, the application will use the fallback paths below.
"""

import os
from pathlib import Path

# Fallback paths (used if environment variables are not set)
# Modify these to match your system setup

# Windows paths (most common)
WINDOWS_PATHS = {
    "phi_bundle": r"C:\curato\phi_bundle",
    "qwen_bundle": r"C:\curato\qwen_bundle",
    "genie_executable": r"C:\curato\phi_bundle\genie-t2t-run.exe"
}

# macOS/Linux paths (alternative)
UNIX_PATHS = {
    "phi_bundle": "~/curato/phi_bundle",
    "qwen_bundle": "~/curato/qwen_bundle", 
    "genie_executable": "~/curato/phi_bundle/genie-t2t-run"
}

# Current platform detection
import platform
IS_WINDOWS = platform.system().lower() == "windows"

# Get paths from environment variables or use fallbacks
def get_phi_bundle_path():
    """Get the Phi bundle path from environment or fallback."""
    return os.environ.get('PHI_BUNDLE_PATH') or (
        WINDOWS_PATHS["phi_bundle"] if IS_WINDOWS else UNIX_PATHS["phi_bundle"]
    )

def get_qwen_bundle_path():
    """Get the Qwen bundle path from environment or fallback."""
    return os.environ.get('QWEN_BUNDLE_PATH') or (
        WINDOWS_PATHS["qwen_bundle"] if IS_WINDOWS else UNIX_PATHS["qwen_bundle"]
    )

def get_genie_executable_path():
    """Get the genie executable path from environment or fallback."""
    return os.environ.get('GENIE_EXECUTABLE_PATH') or (
        WINDOWS_PATHS["genie_executable"] if IS_WINDOWS else UNIX_PATHS["genie_executable"]
    )

# Export the functions for use in other modules
__all__ = [
    'get_phi_bundle_path',
    'get_qwen_bundle_path', 
    'get_genie_executable_path',
    'IS_WINDOWS'
]
