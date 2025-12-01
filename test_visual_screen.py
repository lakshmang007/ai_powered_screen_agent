#!/usr/bin/env python3
"""
Test script for Visual Screen Analysis functionality.
This script tests the basic functionality of the visual screen handler.
"""

import sys
import os
import time

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.screen_agent import ScreenAgent
from src.core.voice_processor import VoiceProcessor
from src.automation.handlers.visual_screen_handler import VisualScreenHandler

def test_visual_screen_analysis():
    """Test the visual screen analysis functionality."""
    print("=" * 60)
    print("Visual Screen Analysis Test")
    print("=" * 60)
    
    # Initialize components
    print("Initializing components...")
    screen_agent = ScreenAgent()
    voice_processor = VoiceProcessor()
    visual_handler = VisualScreenHandler(screen_agent, voice_processor)
    
    print("\nRunning screen analysis test...")
    # Analyze screen
    result = visual_handler.analyze_screen()
    
    if result['status'] == 'completed':
        components = result['data']['components']
        print(f"✓ Success: Found {len(components)} components on screen")
        
        # Display components
        print("\nDetected Components:")
        for i, comp in enumerate(components[:5], 1):  # Show first 5
            comp_type = comp['type']
            title = comp.get('title', comp.get('text', 'Unknown'))
            position = comp['position']
            print(f"  {i}. [{comp_type.upper()}] {title}")
            print(f"     Position: {position}")
        
        if len(components) > 5:
            print(f"  ... and {len(components) - 5} more")
        
        return True
    else:
        print(f"✗ Failed: {result.get('message', 'Unknown error')}")
        return False

if __name__ == "__main__":
    try:
        success = test_visual_screen_analysis()
        if success:
            print("\n✓ Visual screen analysis test completed successfully!")
        else:
            print("\n✗ Visual screen analysis test failed!")
    except Exception as e:
        print(f"\n✗ Error during test: {str(e)}")
        sys.exit(1)