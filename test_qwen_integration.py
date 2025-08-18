#!/usr/bin/env python3
"""
Focused Qwen Model Test for Emotional Story Generation

This script tests just the Qwen model integration to ensure
it's working correctly with your qwen_bundle for generating emotional stories.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_qwen_only():
    """Test only the Qwen model integration for emotional story generation."""
    print("🧠 Testing Qwen model integration for emotional story generation...")
    
    try:
        from models.genie_runner import run_qwen_runner
        
        # Use the correct Qwen prompt format for emotional story generation
        test_prompt = """<|im_start|>system
You are a helpful AI Assistant specializing in creating emotional, engaging stories and itineraries. You excel at crafting narratives that evoke feelings and create memorable experiences.
<|im_end|>
<|im_start|>user
Create an emotional story about a romantic day in Seoul, Korea. The story should include:

Starting location: Hongdae area
Companion type: Romantic couple
Budget: Medium
Start time: 10:00 AM
Duration: Full day

The story should be warm, emotional, and describe the feelings and experiences of the couple as they explore Seoul together. Include specific details about places, emotions, and the journey they share.

Make it a beautiful, romantic narrative that captures the magic of exploring a city with someone you love.
<|im_end|>
<|im_start|>assistant"""

        print(f"📝 Sending test prompt to Qwen model...")
        print(f"📝 Prompt length: {len(test_prompt)} characters")
        print(f"📝 Using Qwen-specific prompt format with <|im_start|> tags")
        
        # Add progress monitoring
        print("🚀 Starting Qwen model inference...")
        print("⏳ This may take a few minutes depending on your NPU performance...")
        print("💡 Tip: You can monitor NPU usage in Task Manager (Performance tab)")
        
        # Run the Qwen model with progress indication
        import time
        start_time = time.time()
        
        response = run_qwen_runner(test_prompt)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Qwen model response received!")
        print(f"⏱️ Processing time: {processing_time:.2f} seconds")
        print(f"📄 Response length: {len(response)} characters")
        print(f"📄 Response preview: {response[:300]}...")
        
        # Validate the response quality
        print(f"\n🔍 Response Analysis:")
        if len(response) > 100:
            print(f"✅ Response is substantial ({len(response)} characters)")
        else:
            print(f"⚠️ Response seems short ({len(response)} characters)")
        
        if "romantic" in response.lower() or "love" in response.lower() or "beautiful" in response.lower():
            print("✅ Response contains emotional/romantic content")
        else:
            print("⚠️ Response may lack emotional content")
        
        if "Seoul" in response or "Hongdae" in response:
            print("✅ Response includes location-specific details")
        else:
            print("⚠️ Response may lack location details")
        
        print(f"\n📄 Full response:")
        print("-" * 60)
        print(response)
        print("-" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during Qwen integration test: {e}")
        import traceback
        traceback.print_exc()
        return False

from models.test_utils import test_genie_setup, test_model_runner_import

def main():
    """Run the Qwen test."""
    print("🚀 Starting Qwen model test for emotional story generation...")
    print("="*60)
    
    # First test setup validation
    print("🔍 Step 1: Testing Genie setup validation...")
    setup_success = test_genie_setup()
    
    if not setup_success:
        print("❌ Setup validation failed. Please check your configuration.")
        return False
    
    # Test QwenRunner import
    print("\n🔍 Step 2: Testing QwenRunner import...")
    import_success = test_model_runner_import("QwenRunner", "run_qwen_runner")
    
    if not import_success:
        print("❌ QwenRunner import failed. Please check the genie_runner.py file.")
        return False
    
    # Then test Qwen model
    print("\n🔍 Step 3: Testing Qwen model inference...")
    qwen_success = test_qwen_only()
    
    print("="*60)
    if qwen_success:
        print("🎉 Qwen model test completed successfully!")
        print("✅ Your Qwen integration is working correctly for emotional story generation.")
        print("✅ The model is now ready to create engaging, emotional narratives.")
    else:
        print("❌ Qwen model test failed.")
        print("🔧 Check the error messages above for troubleshooting.")
    
    return qwen_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
