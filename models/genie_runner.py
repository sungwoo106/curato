"""
Unified Genie Model Runner

This module provides a unified interface to run both Phi and Qwen models using
the Genie SDK and genie-t2t-run executable. It handles the communication between
the Python application and the local model bundles.

The module works by:
1. Writing the generated prompt to a temporary text file
2. Calling the local genie-t2t-run executable with the correct command syntax
3. Capturing and returning the generated output

This replaces the separate phi_runner.py and llama_runner.py modules with a
single, more maintainable solution.
"""

import subprocess
import tempfile
import os
from pathlib import Path
from typing import Literal

# Model types supported by this runner
ModelType = Literal["phi", "qwen"]

class GenieRunner:
    """
    Unified runner for Genie-based models (Phi and Qwen).
    
    This class provides a clean interface to run different model types
    using the genie-t2t-run executable and your pre-configured model bundles.
    """
    
    def __init__(self, 
                 genie_executable: str = "genie-t2t-run.exe",
                 phi_bundle_path: str = "./phi_bundle",
                 qwen_bundle_path: str = "./qwen_bundle",
                 working_dir: str = None):
        """
        Initialize the Genie runner with model bundle paths.
        
        Args:
            genie_executable (str): Path to the genie-t2t-run executable
            phi_bundle_path (str): Path to the Phi model bundle directory
            qwen_bundle_path (str): Path to the Qwen model bundle directory
            working_dir (str): Working directory for temporary files (optional)
        """
        self.genie_executable = genie_executable
        self.phi_bundle_path = Path(phi_bundle_path)
        self.qwen_bundle_path = Path(qwen_bundle_path)
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        
        # For Windows, try to find the executable in common locations
        if not os.path.exists(self.genie_executable):
            # Try to find it in the current directory or PATH
            possible_paths = [
                self.genie_executable,  # Current directory
                f"./{self.genie_executable}",  # Current directory with ./
                f"{self.working_dir}/{self.genie_executable}",  # Working directory
                "genie-t2t-run.exe",  # Just the filename
                "./genie-t2t-run.exe"  # Current directory
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    self.genie_executable = path
                    print(f"✅ Found genie executable at: {path}")
                    break
            else:
                print(f"⚠️ Warning: Genie executable not found at: {self.genie_executable}")
                print("   Make sure genie-t2t-run.exe is in your current directory or PATH")
    
    def run_phi(self, prompt: str) -> str:
        """
        Run the Phi model with the given prompt.
        
        Args:
            prompt (str): The complete prompt to send to the Phi model
            
        Returns:
            str: The generated route plan from the Phi model
            
        Raises:
            RuntimeError: If the Phi model fails to run
            FileNotFoundError: If the Phi bundle is not found
        """
        return self._run_model("phi", prompt)
    
    def run_qwen(self, prompt: str) -> str:
        """
        Run the Qwen model with the given prompt.
        
        Args:
            prompt (str): The complete prompt to send to the Qwen model
            
        Returns:
            str: The generated emotional itinerary text from the Qwen model
            
        Raises:
            RuntimeError: If the Qwen model fails to run
            FileNotFoundError: If the Qwen bundle is not found
        """
        return self._run_model("qwen", prompt)
    
    def _run_model(self, model_type: ModelType, prompt: str) -> str:
        """
        Internal method to run a specific model type.
        
        Args:
            model_type (ModelType): Type of model to run ("phi" or "qwen")
            prompt (str): The prompt to send to the model
            
        Returns:
            str: The generated output from the model
        """
        # Determine which bundle to use
        if model_type == "phi":
            bundle_path = self.phi_bundle_path
            prompt_file = "phi_prompt.txt"
        elif model_type == "qwen":
            bundle_path = self.qwen_bundle_path
            prompt_file = "qwen_prompt.txt"
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        # Create the full path to the prompt file
        prompt_path = self.working_dir / prompt_file
        
        try:
            # Write the prompt to a temporary text file with UTF-8 encoding
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(prompt)
            
            print(f"📝 Running {model_type} model...")
            print(f"📁 Bundle path: {bundle_path}")
            print(f"📁 Working directory: {self.working_dir}")
            print(f"🔧 Executable: {self.genie_executable}")
            
            # Execute the genie-t2t-run executable with the correct parameters
            # Format: genie-t2t-run.exe -c genie_config.json --prompt_file prompt.txt
            # Note: We run from the bundle directory so it can find its config and model files
            cmd = [
                self.genie_executable,
                "-c", "genie_config.json",
                "--prompt_file", str(prompt_path)
            ]
            
            print(f"🚀 Running command: {' '.join(cmd)}")
            print(f"🚀 From directory: {bundle_path}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=bundle_path,  # Run from the bundle directory
                encoding="utf-8"
            )
            
            # Print command output for debugging
            if result.stdout:
                print(f"✅ Model output: {result.stdout[:200]}...")
            if result.stderr:
                print(f"⚠️ Model stderr: {result.stderr}")
            
            # Check if the command was successful
            result.check_returncode()
            
            # Return the generated output, stripping whitespace
            return result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Model {model_type} failed to run (exit code {e.returncode}): {e.stderr}"
            print(f"❌ Error: {error_msg}")
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error running {model_type} model: {e}"
            print(f"❌ Error: {error_msg}")
            raise RuntimeError(error_msg) from e
        finally:
            # Clean up the temporary prompt file
            try:
                if prompt_path.exists():
                    prompt_path.unlink()
            except Exception:
                pass  # Ignore cleanup errors
    
    def validate_setup(self) -> bool:
        """
        Validate that all required components are available.
        
        Returns:
            bool: True if setup is valid, False otherwise
        """
        try:
            # Check genie executable
            if not os.path.exists(self.genie_executable):
                print(f"❌ Genie executable not found: {self.genie_executable}")
                return False
            
            # Check Phi bundle
            if not self.phi_bundle_path.exists():
                print(f"❌ Phi bundle not found: {self.phi_bundle_path}")
                return False
            
            # Check Qwen bundle (optional for now)
            if not self.qwen_bundle_path.exists():
                print(f"⚠️ Qwen bundle not found: {self.qwen_bundle_path} (optional for now)")
            
            # Check genie config in Phi bundle
            phi_config_path = self.phi_bundle_path / "genie_config.json"
            if not phi_config_path.exists():
                print(f"❌ Genie config not found in Phi bundle: {phi_config_path}")
                return False
            
            print("✅ Genie setup validation successful!")
            print(f"   Executable: {self.genie_executable}")
            print(f"   Phi bundle: {self.phi_bundle_path}")
            if self.qwen_bundle_path.exists():
                print(f"   Qwen bundle: {self.qwen_bundle_path}")
            return True
            
        except Exception as e:
            print(f"❌ Setup validation failed: {e}")
            return False


# Convenience functions for backward compatibility
def run_phi_runner(prompt: str) -> str:
    """
    Convenience function to run Phi model (maintains backward compatibility).
    
    Args:
        prompt (str): The prompt to send to the Phi model
        
    Returns:
        str: The generated output from the Phi model
    """
    runner = GenieRunner()
    return runner.run_phi(prompt)


def run_llama_runner(prompt: str) -> str:
    """
    Convenience function to run Qwen model (maintains backward compatibility).
    
    Note: This function is named 'llama_runner' for backward compatibility,
    but it actually runs the Qwen model as per your current setup.
    
    Args:
        prompt (str): The prompt to send to the Qwen model
        
    Returns:
        str: The generated output from the Qwen model
    """
    runner = GenieRunner()
    return runner.run_qwen(prompt)
