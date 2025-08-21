"""
Configuration file for Edge Day Planner

This file contains all the configurable paths and settings for the application.
You can modify these values to match your system setup without changing the main code.

Environment Variables (recommended for portability):
- PHI_BUNDLE_PATH: Path to your phi_bundle directory
- QWEN_BUNDLE_PATH: Path to your qwen_bundle directory  
- PHI_GENIE_EXECUTABLE_PATH: Path to genie-t2t-run.exe for Phi model
- QWEN_GENIE_EXECUTABLE_PATH: Path to genie-t2t-run.exe for Qwen model

If environment variables are not set, the application will use the fallback paths below.

IMPORTANT: When deploying to different devices, you have 3 options:
1. Set environment variables (best for production/teams)
2. Modify the paths below (best for single-device setup)
3. Let the system auto-detect (best for development/testing)

See CONFIGURATION.md for detailed setup instructions.
"""

import os
from pathlib import Path

# =============================================================================
# FALLBACK PATHS (used if environment variables are not set)
# =============================================================================
# 
# MODIFY THESE PATHS TO MATCH YOUR SYSTEM SETUP
# 
# When deploying to different devices, update these paths:
# - Windows: Use r"C:\path\to\your\bundles" format
# - macOS/Linux: Use "/path/to/your/bundles" format
# - Use forward slashes (/) for cross-platform compatibility
# =============================================================================

# Windows paths (most common setup)
# CHANGE THESE PATHS FOR YOUR WINDOWS DEVICE:
WINDOWS_PATHS = {
    "phi_bundle": r"C:\curato\phi_bundle",           # ← CHANGE THIS for your Windows device
    "qwen_bundle": r"C:\curato\qwen_bundle",         # ← CHANGE THIS for your Windows device
    "genie_executables": {
        "phi": r"C:\curato\phi_bundle\genie-t2t-run.exe",    # ← CHANGE THIS for your Windows device
        "qwen": r"C:\curato\qwen_bundle\genie-t2t-run.exe"   # ← CHANGE THIS for your Windows device
    }
}

# macOS/Linux paths (alternative setup)
# CHANGE THESE PATHS FOR YOUR MAC/LINUX DEVICE:
UNIX_PATHS = {
    "phi_bundle": "~/curato/phi_bundle",             # ← CHANGE THIS for your Mac/Linux device
    "qwen_bundle": "~/curato/qwen_bundle",            # ← CHANGE THIS for your Mac/Linux device
    "genie_executables": {
        "phi": "~/curato/phi_bundle/genie-t2t-run",          # ← CHANGE THIS for your Mac/Linux device
        "qwen": "~/curato/qwen_bundle/genie-t2t-run"         # ← CHANGE THIS for your Mac/Linux device
    }
}

# =============================================================================
# PLATFORM DETECTION
# =============================================================================
# This automatically detects your operating system
# No changes needed here - it's automatic!
import platform
IS_WINDOWS = platform.system().lower() == "windows"

# =============================================================================
# PATH GETTER FUNCTIONS
# =============================================================================
# These functions get paths from environment variables OR fallbacks
# Priority order: Environment Variables > config.py > Auto-detection
# =============================================================================

def get_phi_bundle_path():
    """
    Get the Phi bundle path from environment or fallback.
    
    Priority:
    1. PHI_BUNDLE_PATH environment variable (highest)
    2. config.py fallback paths (medium)
    3. Auto-detection in common locations (lowest)
    
    To customize for different devices:
    - Set PHI_BUNDLE_PATH environment variable, OR
    - Modify WINDOWS_PATHS/UNIX_PATHS above
    """
    return os.environ.get('PHI_BUNDLE_PATH') or (
        WINDOWS_PATHS["phi_bundle"] if IS_WINDOWS else UNIX_PATHS["phi_bundle"]
    )

def get_qwen_bundle_path():
    """
    Get the Qwen bundle path from environment or fallback.
    
    Priority:
    1. QWEN_BUNDLE_PATH environment variable (highest)
    2. config.py fallback paths (medium)
    3. Auto-detection in common locations (lowest)
    
    To customize for different devices:
    - Set QWEN_BUNDLE_PATH environment variable, OR
    - Modify WINDOWS_PATHS/UNIX_PATHS above
    """
    return os.environ.get('QWEN_BUNDLE_PATH') or (
        WINDOWS_PATHS["qwen_bundle"] if IS_WINDOWS else UNIX_PATHS["qwen_bundle"]
    )

def get_phi_genie_executable_path():
    """
    Get the Phi genie executable path from environment or fallback.
    
    Priority:
    1. PHI_GENIE_EXECUTABLE_PATH environment variable (highest)
    2. config.py fallback paths (medium)
    3. Auto-detection in common locations (lowest)
    
    To customize for different devices:
    - Set PHI_GENIE_EXECUTABLE_PATH environment variable, OR
    - Modify WINDOWS_PATHS/UNIX_PATHS above
    """
    return os.environ.get('PHI_GENIE_EXECUTABLE_PATH') or (
        WINDOWS_PATHS["genie_executables"]["phi"] if IS_WINDOWS else UNIX_PATHS["genie_executables"]["phi"]
    )

def get_qwen_genie_executable_path():
    """
    Get the Qwen genie executable path from environment or fallback.
    
    Priority:
    1. QWEN_GENIE_EXECUTABLE_PATH environment variable (highest)
    2. config.py fallback paths (medium)
    3. Auto-detection in common locations (lowest)
    
    To customize for different devices:
    - Set QWEN_GENIE_EXECUTABLE_PATH environment variable, OR
    - Modify WINDOWS_PATHS/UNIX_PATHS above
    """
    return os.environ.get('QWEN_GENIE_EXECUTABLE_PATH') or (
        WINDOWS_PATHS["genie_executables"]["qwen"] if IS_WINDOWS else UNIX_PATHS["genie_executables"]["qwen"]
    )



# =============================================================================
# DEPLOYMENT SCENARIOS
# =============================================================================
# 
# SCENARIO 1: Single Device Setup
# =============================================================================
# Just modify the paths above to match your system:
# 
# Windows Example:
# WINDOWS_PATHS = {
#     "phi_bundle": r"D:\my_ai_models\phi_bundle",
#     "qwen_bundle": r"D:\my_ai_models\qwen_bundle",
#     "genie_executables": {
#         "phi": r"D:\my_ai_models\phi_bundle\genie-t2t-run.exe",
#         "qwen": r"D:\my_ai_models\qwen_bundle\genie-t2t-run.exe"
#     }
# }
#
# macOS Example:
# UNIX_PATHS = {
#     "phi_bundle": "/Users/username/AI_Models/phi_bundle",
#     "qwen_bundle": "/Users/username/AI_Models/qwen_bundle",
#     "genie_executables": {
#         "phi": "/Users/username/AI_Models/phi_bundle/genie-t2t-run",
#         "qwen": "/Users/username/AI_Models/qwen_bundle/genie-t2t-run"
#     }
# }
#
# =============================================================================
# SCENARIO 2: Multiple Devices / Team Setup
# =============================================================================
# Use environment variables instead of modifying this file:
#
# Windows Command Prompt:
# set PHI_BUNDLE_PATH=D:\ai_models\phi_bundle
# set QWEN_BUNDLE_PATH=D:\ai_models\qwen_bundle
# set PHI_GENIE_EXECUTABLE_PATH=D:\ai_models\phi_bundle\genie-t2t-run.exe
# set QWEN_GENIE_EXECUTABLE_PATH=D:\ai_models\qwen_bundle\genie-t2t-run.exe
#
# macOS/Linux Terminal:
# export PHI_BUNDLE_PATH=/home/user/ai_models/phi_bundle
# export QWEN_BUNDLE_PATH=/home/user/ai_models/qwen_bundle
# export PHI_GENIE_EXECUTABLE_PATH=/home/user/ai_models/phi_bundle/genie-t2t-run
# export QWEN_GENIE_EXECUTABLE_PATH=/home/user/ai_models/qwen_bundle/genie-t2t-run
#
# =============================================================================
# SCENARIO 3: Development / Testing
# =============================================================================
# Don't modify anything - let auto-detection handle it!
# The system will automatically find bundles in common locations.
#
# =============================================================================

# Export the functions for use in other modules
__all__ = [
    'get_phi_bundle_path',
    'get_qwen_bundle_path', 
    'get_phi_genie_executable_path',
    'get_qwen_genie_executable_path',
    'IS_WINDOWS'
]
