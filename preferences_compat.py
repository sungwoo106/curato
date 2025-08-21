"""
Compatibility Layer for Preferences

This module provides backward compatibility for existing code while using
the new modular architecture internally. It maintains the exact same
public API as the original preferences.py.
"""

# Import the refactored version
from preferences_refactored import Preferences

# Re-export the main class for backward compatibility
__all__ = ['Preferences']

# This ensures that existing imports like "from preferences import Preferences"
# will continue to work without any changes to the calling code.
