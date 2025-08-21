"""
AI Model Management Module

This module handles the initialization, management, and execution of AI models
(Phi and Qwen) used for trip planning and itinerary generation.
"""

import sys
import time
from typing import Optional, Callable
from models.genie_runner import GenieRunner

def _log(level: str, message: str):
    """Simple logging function."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {level} - {message}", file=sys.stderr)

class ModelManager:
    """
    Manages AI model instances for better performance and resource management.
    
    This class handles:
    - Lazy initialization of model instances
    - Reusable model runners for Phi and Qwen
    - Model validation and fallback handling
    """
    
    def __init__(self, progress_callback: Optional[Callable[[int, str], None]] = None):
        """
        Initialize the model manager.
        
        Args:
            progress_callback: Optional callback for progress updates
        """
        self.progress_callback = progress_callback
        self._phi_runner = None
        self._qwen_runner = None
        self._models_initialized = False
    
    def _initialize_models(self):
        """Initialize AI model instances lazily."""
        if not self._models_initialized:
            try:
                _log("INFO", "🚀 Initializing AI model instances for better performance...")
                
                # Create reusable model instances
                self._phi_runner = GenieRunner(progress_callback=self.progress_callback)
                self._qwen_runner = GenieRunner(progress_callback=self.progress_callback)
                
                # Validate the setup
                if self._phi_runner.validate_setup() and self._qwen_runner.validate_setup():
                    self._models_initialized = True
                    _log("SUCCESS", "✅ AI model instances initialized successfully")
                    _log("INFO", f"   Phi bundle: {self._phi_runner.phi_bundle_path}")
                    _log("INFO", f"   Qwen bundle: {self._qwen_runner.qwen_bundle_path}")
                else:
                    _log("WARNING", "⚠️ Some model validation failed, but continuing...")
                    self._models_initialized = True
                    
            except Exception as e:
                _log("ERROR", f"❌ Failed to initialize AI model instances: {e}")
                self._models_initialized = True
                self._phi_runner = None
                self._qwen_runner = None
    
    def get_phi_runner(self) -> GenieRunner:
        """Get the Phi model runner instance, initializing if necessary."""
        if not self._models_initialized:
            self._initialize_models()
        
        if self._phi_runner is None:
            _log("WARNING", "⚠️ Using fallback Phi runner (new instance)")
            return GenieRunner(progress_callback=self.progress_callback)
        
        return self._phi_runner
    
    def get_qwen_runner(self) -> GenieRunner:
        """Get the Qwen model runner instance, initializing if necessary."""
        if not self._models_initialized:
            self._initialize_models()
        
        if self._qwen_runner is None:
            _log("WARNING", "⚠️ Using fallback Qwen runner (new instance)")
            return GenieRunner(progress_callback=self.progress_callback)
        
        return self._qwen_runner
    
    def get_performance_stats(self) -> dict:
        """Get performance statistics for the AI model instances."""
        return {
            "models_initialized": self._models_initialized,
            "phi_runner_available": self._phi_runner is not None,
            "qwen_runner_available": self._qwen_runner is not None,
            "optimization_enabled": self._models_initialized and self._phi_runner and self._qwen_runner
        }
