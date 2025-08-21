"""
Unified Genie Model Runner

This module provides a unified interface to run both Phi and Qwen models using
the Genie SDK and genie-t2t-run executable. It handles the communication between
the Python application and the local model bundles.

The module works by:
1. Writing the generated prompt to a temporary text file
2. Calling the local genie-t2t-run executable with the correct command syntax
3. Capturing and returning the generated output
4. Supporting streaming progress updates for real-time UI feedback

This replaces the separate phi_runner.py and llama_runner.py modules with a
single, more maintainable solution.
"""

import subprocess
import tempfile
import os
import json
import sys
from pathlib import Path
from typing import Literal, Optional, Callable

# Model types supported by this runner
ModelType = Literal["phi", "qwen"]

class GenieRunner:
    """
    Unified runner for Genie-based models (Phi and Qwen).
    
    This class provides a clean interface to run different model types
    using the genie-t2t-run executable and your pre-configured model bundles.
    """
    
    def __init__(self, 
                 phi_genie_executable: str = None,
                 qwen_genie_executable: str = None,
                 phi_bundle_path: str = None,
                 qwen_bundle_path: str = None,
                 working_dir: str = None,
                 progress_callback: Optional[Callable[[int, str], None]] = None):
        """
        Initialize the Genie runner with model bundle paths.
        
        Args:
            phi_genie_executable (str): Path to the genie-t2t-run executable for Phi model (auto-detected if None)
            qwen_genie_executable (str): Path to the genie-t2t-run executable for Qwen model (auto-detected if None)
            phi_bundle_path (str): Path to the Phi model bundle directory (auto-detected if None)
            qwen_bundle_path (str): Path to the Qwen model bundle directory (auto-detected if None)
            working_dir (str): Working directory for temporary files (optional)
            progress_callback (Callable): Optional callback function for progress updates (progress, message)
        
        Configuration Priority (highest to lowest):
        1. Explicit paths passed to constructor
        2. Environment variables (PHI_BUNDLE_PATH, QWEN_BUNDLE_PATH, PHI_GENIE_EXECUTABLE_PATH, QWEN_GENIE_EXECUTABLE_PATH)
        3. config.py fallback paths
        4. Auto-detection in common locations
        
        Examples for different devices:
        
        # Windows Device 1:
        runner = GenieRunner(
            phi_bundle_path=r"C:\curato\phi_bundle",
            qwen_bundle_path=r"C:\curato\qwen_bundle",
            phi_genie_executable=r"C:\curato\phi_bundle\genie-t2t-run.exe",
            qwen_genie_executable=r"C:\curato\qwen_bundle\genie-t2t-run.exe"
        )
        
        # Windows Device 2 (different paths):
        runner = GenieRunner(
            phi_bundle_path=r"D:\ai_models\phi_bundle",
            qwen_bundle_path=r"D:\ai_models\qwen_bundle",
            phi_genie_executable=r"D:\ai_models\phi_bundle\genie-t2t-run.exe",
            qwen_genie_executable=r"D:\ai_models\qwen_bundle\genie-t2t-run.exe"
        )
        
        # macOS/Linux Device:
        runner = GenieRunner(
            phi_bundle_path="/home/user/ai_models/phi_bundle",
            qwen_bundle_path="/home/user/ai_models/qwen_bundle",
            phi_genie_executable="/home/user/ai_models/phi_bundle/genie-t2t-run",
            qwen_genie_executable="/home/user/ai_models/qwen_bundle/genie-t2t-run"
        )
        
        # Auto-detection (recommended for development):
        runner = GenieRunner()  # Will auto-detect all paths
        """
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.progress_callback = progress_callback
        
        # Auto-detect paths if not provided
        if phi_bundle_path is None:
            phi_bundle_path = self._auto_detect_phi_bundle()
        if qwen_bundle_path is None:
            qwen_bundle_path = self._auto_detect_qwen_bundle()
        if phi_genie_executable is None:
            phi_genie_executable = self._auto_detect_phi_genie_executable(phi_bundle_path)
        if qwen_genie_executable is None:
            qwen_genie_executable = self._auto_detect_qwen_genie_executable(qwen_bundle_path)
        
        self.phi_genie_executable = phi_genie_executable
        self.qwen_genie_executable = qwen_genie_executable
        self.phi_bundle_path = Path(phi_bundle_path)
        self.qwen_bundle_path = Path(qwen_bundle_path)
        
        # Validate the setup
        self._validate_paths()
    
    def _auto_detect_phi_bundle(self) -> str:
        """
        Auto-detect the Phi bundle path.
        
        Detection order:
        1. Environment variable PHI_BUNDLE_PATH
        2. config.py fallback paths
        3. Common locations (./phi_bundle, ../phi_bundle, etc.)
        
        To customize for different devices:
        - Set PHI_BUNDLE_PATH environment variable, OR
        - Modify config.py with your device paths, OR
        - Place bundles in common locations (./phi_bundle)
        
        Common locations checked:
        - ./phi_bundle (current directory)
        - ../phi_bundle (parent directory)
        - ~/curato/phi_bundle (user home)
        - C:\curato\phi_bundle (Windows default)
        """
        # Check environment variable first
        env_path = os.environ.get('PHI_BUNDLE_PATH')
        if env_path and os.path.exists(env_path):
            print(f"✅ Found Phi bundle from environment: {env_path}")
            return env_path
        
        # Try to import from config file
        try:
            from config import get_phi_bundle_path
            config_path = get_phi_bundle_path()
            if os.path.exists(config_path):
                print(f"✅ Found Phi bundle from config: {config_path}")
                return config_path
        except ImportError:
            pass
        
        # Common locations to check
        possible_paths = [
            "./phi_bundle",
            "../phi_bundle",
            "phi_bundle",
            r"C:\curato\phi_bundle",  # Windows default
            r"C:\phi_bundle",
            os.path.expanduser("~/phi_bundle"),  # User home
            os.path.expanduser("~/curato/phi_bundle"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ Auto-detected Phi bundle at: {path}")
                return path
        
        # Default fallback
        default_path = "./phi_bundle"
        print(f"⚠️ Could not auto-detect Phi bundle, using default: {default_path}")
        return default_path
    
    def _auto_detect_qwen_bundle(self) -> str:
        """
        Auto-detect the Qwen bundle path.
        
        Detection order:
        1. Environment variable QWEN_BUNDLE_PATH
        2. config.py fallback paths
        3. Common locations (./qwen_bundle, ../qwen_bundle, etc.)
        
        To customize for different devices:
        - Set QWEN_BUNDLE_PATH environment variable, OR
        - Modify config.py with your device paths, OR
        - Place bundles in common locations (./qwen_bundle)
        
        Common locations checked:
        - ./qwen_bundle (current directory)
        - ../qwen_bundle (parent directory)
        - ~/curato/qwen_bundle (user home)
        - C:\curato\qwen_bundle (Windows default)
        """
        # Check environment variable first
        env_path = os.environ.get('QWEN_BUNDLE_PATH')
        if env_path and os.path.exists(env_path):
            print(f"✅ Found Qwen bundle from environment: {env_path}")
            return env_path
        
        # Try to import from config file
        try:
            from config import get_qwen_bundle_path
            config_path = get_qwen_bundle_path()
            if os.path.exists(config_path):
                print(f"✅ Found Qwen bundle from config: {config_path}")
                return config_path
        except ImportError:
            pass
        
        # Common locations to check
        possible_paths = [
            "./qwen_bundle",
            "../qwen_bundle",
            "qwen_bundle",
            r"C:\curato\qwen_bundle",  # Windows default
            r"C:\qwen_bundle",
            os.path.expanduser("~/qwen_bundle"),  # User home
            os.path.expanduser("~/curato/qwen_bundle"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ Auto-detected Qwen bundle at: {path}")
                return path
        
        # Default fallback
        default_path = "./qwen_bundle"
        print(f"⚠️ Could not auto-detect Qwen bundle, using default: {default_path}")
        return default_path
    
    def _auto_detect_phi_genie_executable(self, phi_bundle_path: str) -> str:
        """
        Auto-detect the genie-t2t-run executable for Phi model.
        
        Detection order:
        1. Environment variable PHI_GENIE_EXECUTABLE_PATH
        2. config.py fallback paths
        3. Inside phi_bundle directory (most likely location)
        4. Common locations (./genie-t2t-run.exe, etc.)
        
        To customize for different devices:
        - Set PHI_GENIE_EXECUTABLE_PATH environment variable, OR
        - Modify config.py with your device paths, OR
        - Place executable in phi_bundle directory
        
        Common locations checked:
        - Inside phi_bundle directory (recommended)
        - ./genie-t2t-run.exe (current directory)
        - C:\curato\genie-t2t-run.exe (Windows default)
        """
        # Check environment variable first
        env_path = os.environ.get('PHI_GENIE_EXECUTABLE_PATH')
        if env_path and os.path.exists(env_path):
            print(f"✅ Found Phi genie executable from environment: {env_path}")
            return env_path
        
        # Try to import from config file
        try:
            from config import get_phi_genie_executable_path
            config_path = get_phi_genie_executable_path()
            if os.path.exists(config_path):
                print(f"✅ Found Phi genie executable from config: {config_path}")
                return config_path
        except ImportError:
            pass
        
        # Check inside the phi_bundle directory first (most likely location)
        bundle_executable = os.path.join(phi_bundle_path, "genie-t2t-run.exe")
        if os.path.exists(bundle_executable):
            print(f"✅ Found genie executable in Phi bundle: {bundle_executable}")
            return bundle_executable
        
        # Common locations to check
        possible_paths = [
            "genie-t2t-run.exe",
            "./genie-t2t-run.exe",
            "../genie-t2t-run.exe",
            r"C:\curato\genie-t2t-run.exe",
            r"C:\genie-t2t-run.exe",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ Auto-detected Phi genie executable at: {path}")
                return path
        
        # Default fallback
        default_path = "genie-t2t-run.exe"
        print(f"⚠️ Could not auto-detect Phi genie executable, using default: {default_path}")
        return default_path
    
    def _auto_detect_qwen_genie_executable(self, qwen_bundle_path: str) -> str:
        """
        Auto-detect the genie-t2t-run executable for Qwen model.
        
        Detection order:
        1. Environment variable QWEN_GENIE_EXECUTABLE_PATH
        2. config.py fallback paths
        3. Inside qwen_bundle directory (most likely location)
        4. Common locations (./genie-t2t-run.exe, etc.)
        
        To customize for different devices:
        - Set QWEN_GENIE_EXECUTABLE_PATH environment variable, OR
        - Modify config.py with your device paths, OR
        - Place executable in qwen_bundle directory
        
        Common locations checked:
        - Inside qwen_bundle directory (recommended)
        - ./genie-t2t-run.exe (current directory)
        - C:\curato\genie-t2t-run.exe (Windows default)
        """
        # Check environment variable first
        env_path = os.environ.get('QWEN_GENIE_EXECUTABLE_PATH')
        if env_path and os.path.exists(env_path):
            print(f"✅ Found Qwen genie executable from environment: {env_path}")
            return env_path
        
        # Try to import from config file
        try:
            from config import get_qwen_genie_executable_path
            config_path = get_qwen_genie_executable_path()
            if os.path.exists(config_path):
                print(f"✅ Found Qwen genie executable from config: {config_path}")
                return config_path
        except ImportError:
            pass
        
        # Check inside the qwen_bundle directory first (most likely location)
        bundle_executable = os.path.join(qwen_bundle_path, "genie-t2t-run.exe")
        if os.path.exists(bundle_executable):
            print(f"✅ Found genie executable in Qwen bundle: {bundle_executable}")
            return bundle_executable
        
        # Common locations to check
        possible_paths = [
            "genie-t2t-run.exe",
            "./genie-t2t-run.exe",
            "../genie-t2t-run.exe",
            r"C:\curato\genie-t2t-run.exe",
            r"C:\genie-t2t-run.exe",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ Auto-detected Qwen genie executable at: {path}")
                return path
        
        # Default fallback
        default_path = "genie-t2t-run.exe"
        print(f"⚠️ Could not auto-detect Qwen genie executable, using default: {default_path}")
        return default_path
    
    def _validate_paths(self):
        """Validate that all required paths exist and are accessible."""
        print(f"🔍 Validating GenieRunner configuration:")
        print(f"   Phi executable: {self.phi_genie_executable}")
        print(f"   Qwen executable: {self.qwen_genie_executable}")
        print(f"   Phi bundle: {self.phi_bundle_path}")
        print(f"   Qwen bundle: {self.qwen_bundle_path}")
        print(f"   Working dir: {self.working_dir}")
        
        # Check if paths exist
        if not os.path.exists(self.phi_genie_executable):
            print(f"⚠️ Warning: Phi genie executable not found at: {self.phi_genie_executable}")
            print("   Make sure genie-t2t-run.exe is accessible in phi_bundle or set PHI_GENIE_EXECUTABLE_PATH environment variable")
        
        if not os.path.exists(self.qwen_genie_executable):
            print(f"⚠️ Warning: Qwen genie executable not found at: {self.qwen_genie_executable}")
            print("   Make sure genie-t2t-run.exe is accessible in qwen_bundle or set QWEN_GENIE_EXECUTABLE_PATH environment variable")
        
        if not self.phi_bundle_path.exists():
            print(f"⚠️ Warning: Phi bundle not found at: {self.phi_bundle_path}")
            print("   Make sure phi_bundle directory exists or set PHI_BUNDLE_PATH environment variable")
        
        if not self.qwen_bundle_path.exists():
            print(f"⚠️ Warning: Qwen bundle not found at: {self.qwen_bundle_path}")
            print("   Make sure qwen_bundle directory exists or set QWEN_BUNDLE_PATH environment variable")
    
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
    
    def run_qwen_streaming(self, prompt: str, stream_callback: Callable[[str, bool], None]) -> str:
        """
        Run the Qwen model with streaming support for real-time output.
        
        Args:
            prompt (str): The complete prompt to send to the Qwen model
            stream_callback (Callable[[str, bool], None]): Callback function for streaming tokens
                                                       First param: token text, Second param: is_final
            
        Returns:
            str: The complete generated output from the Qwen model
        """
        return self._run_model_streaming("qwen", prompt, stream_callback)
    
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
            
            # Determine which executable to use based on model type
            if model_type == "phi":
                executable = self.phi_genie_executable
            elif model_type == "qwen":
                executable = self.qwen_genie_executable
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
            
            print(f"📝 Running {model_type} model...", file=sys.stderr)
            print(f"📁 Bundle path: {bundle_path}", file=sys.stderr)
            print(f"📁 Working directory: {self.working_dir}", file=sys.stderr)
            print(f"🔧 Executable: {executable}", file=sys.stderr)
            
            # Show NPU processing information
            print("🚀 Starting NPU inference...", file=sys.stderr)
            print("⏳ Model is now processing on your NPU...", file=sys.stderr)
            print("💡 Monitor NPU usage in Task Manager > Performance tab", file=sys.stderr)
            print("🔍 You can also check GPU-Z or similar tools for detailed NPU stats", file=sys.stderr)
            
            # Send progress update if callback is available
            if self.progress_callback:
                self.progress_callback(85, f"Running {model_type} model on NPU...")
            
            # Execute the genie-t2t-run executable with the correct parameters
            # Format: genie-t2t-run.exe -c genie_config.json --prompt_file prompt.txt
            # Note: We run from the bundle directory so it can find its config and model files
            cmd = [
                executable,
                "-c", "genie_config.json",
                "--prompt_file", str(prompt_path)
            ]
            
            print(f"🚀 Running command: {' '.join(cmd)}", file=sys.stderr)
            print(f"🚀 From directory: {bundle_path}", file=sys.stderr)
            
            # Add progress indicator
            import time
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=bundle_path,  # Run from the bundle directory
                encoding="utf-8"
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"✅ NPU inference completed in {processing_time:.2f} seconds!", file=sys.stderr)
            
            # Send progress update if callback is available
            if self.progress_callback:
                self.progress_callback(90, f"{model_type} model completed successfully")
            
            # Check if the command was successful
            
            # Check if the command was successful
            result.check_returncode()
            
            # Return the generated output, stripping whitespace
            return result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Model {model_type} failed to run (exit code {e.returncode}): {e.stderr}"
            print(f"❌ Error: {error_msg}", file=sys.stderr)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error running {model_type} model: {e}"
            print(f"❌ Error: {error_msg}", file=sys.stderr)
            raise RuntimeError(error_msg) from e
        finally:
            # Clean up the temporary prompt file
            try:
                if prompt_path.exists():
                    prompt_path.unlink()
            except Exception:
                pass  # Ignore cleanup errors
    
    def _run_model_streaming(self, model_type: ModelType, prompt: str, stream_callback: Callable[[str, bool], None]) -> str:
        """
        Internal method to run a specific model type with true real-time streaming support.
        
        This method captures output from genie-t2t-run.exe in real-time as it's generated,
        providing immediate token-by-token streaming just like running the executable directly
        in the terminal or using ChatGPT.
        
        Args:
            model_type (ModelType): Type of model to run ("phi" or "qwen")
            prompt (str): The prompt to send to the model
            stream_callback (Callable[[str, bool], None]): Callback for streaming tokens
            
        Returns:
            str: The complete generated output from the model
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
            
            # Determine which executable to use based on model type
            if model_type == "phi":
                executable = self.phi_genie_executable
            elif model_type == "qwen":
                executable = self.qwen_genie_executable
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
            
            # Send progress update if callback is available
            if self.progress_callback:
                self.progress_callback(85, f"Running {model_type} model on NPU with streaming...")
            
            # Execute the genie-t2t-run executable with the correct parameters
            # Format: genie-t2t-run.exe -c genie_config.json --prompt_file prompt.txt
            # Note: We run from the bundle directory so it can find its config and model files
            cmd = [
                executable,
                "-c", "genie_config.json",
                "--prompt_file", str(prompt_path)
            ]
            
            print(f"🚀 Running {model_type} model with true real-time streaming...", file=sys.stderr)
            print(f"📁 Bundle path: {bundle_path}", file=sys.stderr)
            print(f"📁 Working directory: {self.working_dir}", file=sys.stderr)
            print(f"🔧 Executable: {executable}", file=sys.stderr)
            
            # Show NPU processing information
            print("🚀 Starting NPU inference...", file=sys.stderr)
            print("⏳ Model is now processing on your NPU...", file=sys.stderr)
            print("💡 Monitor NPU usage in Task Manager > Performance tab", file=sys.stderr)
            print("🔍 You can also check GPU-Z or similar tools for detailed NPU stats", file=sys.stderr)
            
            # Add progress indicator
            import time
            start_time = time.time()
            
            # Use Popen for true real-time streaming
            print(f"🔄 Starting true real-time streaming...", file=sys.stderr)
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=bundle_path,  # Run from the bundle directory
                encoding="utf-8",
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            # Stream output in real-time as it's generated
            full_output = ""
            buffer = ""
            
            while True:
                # Read one character at a time for immediate streaming
                char = process.stdout.read(1)
                if not char:
                    break
                
                full_output += char
                buffer += char
                
                # Stream the character immediately
                stream_callback(char, False)
                
                # Flush to ensure immediate display
                sys.stdout.flush()
                
                # Check if we have a complete word or sentence
                if char in ' \n\t.,!?;:':
                    # Send any buffered content
                    if buffer.strip():
                        print(f"📝 Streamed: '{buffer.strip()}'", file=sys.stderr)
                    buffer = ""
            
            # Wait for process to complete
            process.wait()
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"✅ NPU inference completed in {processing_time:.2f} seconds!", file=sys.stderr)
            
            # Send progress update if callback is available
            if self.progress_callback:
                self.progress_callback(90, f"{model_type} model completed successfully")
            
            # Check if the command was successful
            if process.returncode != 0:
                stderr_output = process.stderr.read()
                error_msg = f"Model {model_type} failed to run (exit code {process.returncode}): {stderr_output}"
                print(f"❌ Error: {error_msg}", file=sys.stderr)
                raise RuntimeError(error_msg)
            
            # Send final completion signal
            stream_callback("", True)
            print("✅ True real-time streaming completed successfully", file=sys.stderr)
            
            # Return the complete output
            return full_output.strip()
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Model {model_type} failed to run (exit code {e.returncode}): {e.stderr}"
            print(f"❌ Error: {error_msg}", file=sys.stderr)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error running {model_type} model with streaming: {e}"
            print(f"❌ Error: {error_msg}", file=sys.stderr)
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
            # Check Phi genie executable
            if not os.path.exists(self.phi_genie_executable):
                print(f"❌ Phi genie executable not found: {self.phi_genie_executable}")
                return False
            
            # Check Qwen genie executable
            if not os.path.exists(self.qwen_genie_executable):
                print(f"❌ Qwen genie executable not found: {self.qwen_genie_executable}")
                return False
            
            # Check Phi bundle
            if not self.phi_bundle_path.exists():
                print(f"❌ Phi bundle not found: {self.phi_bundle_path}")
                return False
            
            # Check Qwen bundle
            if not self.qwen_bundle_path.exists():
                print(f"❌ Qwen bundle not found: {self.qwen_bundle_path}")
                return False
            
            # Check genie config in Phi bundle
            phi_config_path = self.phi_bundle_path / "genie_config.json"
            if not phi_config_path.exists():
                print(f"❌ Genie config not found in Phi bundle: {phi_config_path}")
                return False
            
            # Check genie config in Qwen bundle
            qwen_config_path = self.qwen_bundle_path / "genie_config.json"
            if not qwen_config_path.exists():
                print(f"❌ Genie config not found in Qwen bundle: {qwen_config_path}")
                return False
            
            print("✅ Genie setup validation successful!")
            print(f"   Phi executable: {self.phi_genie_executable}")
            print(f"   Qwen executable: {self.qwen_genie_executable}")
            print(f"   Phi bundle: {self.phi_bundle_path}")
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
    # Try to auto-detect paths or use environment variables
    runner = GenieRunner()
    return runner.run_phi(prompt)


def run_qwen_runner(prompt: str) -> str:
    """
    Convenience function to run Qwen model.
    
    Args:
        prompt (str): The prompt to send to the Qwen model
        
    Returns:
        str: The generated output from the Qwen model
    """
    # Try to auto-detect paths or use environment variables
    runner = GenieRunner()
    return runner.run_qwen(prompt)


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
    # Try to auto-detect paths or use environment variables
    runner = GenieRunner()
    return runner.run_qwen(prompt)
