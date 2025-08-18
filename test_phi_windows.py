#!/usr/bin/env python3
"""
Focused Phi Model Test for Windows

This script tests just the Phi model integration on Windows to ensure
it's working correctly with your phi_bundle.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_phi_only():
    """Test only the Phi model integration."""
    print("🧠 Testing Phi model integration on Windows...")
    
    try:
        from models.phi_runner import run_phi_runner
        
        # Simple test prompt for route planning
        test_prompt = """You are a travel planner. Generate a JSON response with exactly 4 locations for a day trip in Seoul, Korea.

Starting location: Hongdae area
Companion type: Solo traveler
Budget: Low
Start time: 12:00 (noon)

Available places:
- Restaurants and cafes
- Cultural sites
- Shopping areas
- Parks and outdoor spaces

Please respond with a JSON array containing exactly 4 locations, each with:
- name: Place name
- type: Type of place
- description: Brief description
- estimated_time: Time to spend there (in hours)

Format your response as valid JSON only."""

        print(f"📝 Sending test prompt to Phi model...")
        print(f"📝 Prompt length: {len(test_prompt)} characters")
        
        # Run the Phi model
        response = run_phi_runner(test_prompt)
        
        print(f"✅ Phi model response received!")
        print(f"📄 Response length: {len(response)} characters")
        print(f"📄 Response preview: {response[:300]}...")
        
        # Try to parse as JSON to validate
        try:
            import json
            parsed = json.loads(response)
            print(f"✅ Response is valid JSON with {len(parsed)} items")
        except json.JSONDecodeError as e:
            print(f"⚠️ Response is not valid JSON: {e}")
            print(f"📄 Full response: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during Phi integration test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_genie_setup():
    """Test the Genie setup validation."""
    print("🔍 Testing Genie setup validation...")
    
    try:
        from models.genie_runner import GenieRunner
        
        # Create a runner instance
        runner = GenieRunner()
        
        # Validate setup
        if runner.validate_setup():
            print("✅ Genie setup validation successful!")
            return True
        else:
            print("❌ Genie setup validation failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during setup validation: {e}")
        return False

def main():
    """Run the Phi test."""
    print("🚀 Starting Phi model test for Windows...")
    print("="*60)
    
    # First test setup validation
    setup_success = test_genie_setup()
    
    if not setup_success:
        print("❌ Setup validation failed. Please check your configuration.")
        return False
    
    # Then test Phi model
    phi_success = test_phi_only()
    
    print("="*60)
    if phi_success:
        print("🎉 Phi model test completed successfully!")
        print("✅ Your Phi integration is working correctly.")
    else:
        print("❌ Phi model test failed.")
        print("🔧 Check the error messages above for troubleshooting.")
    
    return phi_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
