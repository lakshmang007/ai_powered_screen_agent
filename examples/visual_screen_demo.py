"""
Visual Screen Analysis Demo.
Demonstrates Byte's ability to analyze the screen and identify clickable elements.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.screen_agent import ScreenAgent
from src.core.voice_processor import VoiceProcessor
from src.automation.handlers.visual_screen_handler import VisualScreenHandler
from src.automation.handlers.selenium_handler import SeleniumHandler
from src.core.nlp_processor import ParsedCommand, ActionType
import time


def demo_visual_screen_analysis():
    """Demonstrate visual screen analysis."""
    print("=" * 60)
    print("Visual Screen Analysis Demo")
    print("=" * 60)
    
    # Initialize components
    screen_agent = ScreenAgent()
    voice_processor = VoiceProcessor()
    visual_handler = VisualScreenHandler(screen_agent, voice_processor)
    
    print("\n1. Analyzing current screen...")
    print("-" * 60)
    
    # Analyze screen
    result = visual_handler.analyze_screen()
    
    if result['status'] == 'completed':
        components = result['data']['components']
        print(f"✓ Found {len(components)} components on screen")
        
        # Display components
        print("\nDetected Components:")
        for i, comp in enumerate(components[:10], 1):  # Show first 10
            comp_type = comp['type']
            title = comp.get('title', comp.get('text', 'Unknown'))
            position = comp['position']
            print(f"  {i}. [{comp_type.upper()}] {title}")
            print(f"     Position: {position}")
        
        if len(components) > 10:
            print(f"  ... and {len(components) - 10} more")
    else:
        print(f"✗ Analysis failed: {result['message']}")
    
    print("\n" + "=" * 60)


def demo_selenium_page_analysis():
    """Demonstrate Selenium page analysis."""
    print("=" * 60)
    print("Selenium Page Analysis Demo")
    print("=" * 60)
    
    # Initialize components
    voice_processor = VoiceProcessor()
    selenium_handler = SeleniumHandler(voice_processor=voice_processor)
    
    try:
        print("\n1. Opening Google...")
        print("-" * 60)
        
        # Open Google
        result = selenium_handler.open_website({'url': 'https://www.google.com'})
        
        if result['status'] == 'completed':
            print(f"✓ {result['message']}")
            
            # Wait for page to load
            time.sleep(2)
            
            print("\n2. Analyzing page elements...")
            print("-" * 60)
            
            # Analyze page
            result = selenium_handler.analyze_page()
            
            if result['status'] == 'completed':
                elements = result['data']['elements']
                print(f"✓ Found {len(elements)} elements on page")
                print(f"  Page: {result['data']['title']}")
                print(f"  URL: {result['data']['url']}")
                
                # Display elements by type
                links = [e for e in elements if e['type'] == 'link']
                buttons = [e for e in elements if e['type'] == 'button']
                inputs = [e for e in elements if e['type'] == 'input']
                
                if links:
                    print(f"\n  Links ({len(links)}):")
                    for i, link in enumerate(links[:5], 1):
                        text = link['text']
                        if len(text) > 50:
                            text = text[:47] + "..."
                        print(f"    {i}. {text}")
                        print(f"       → {link['href']}")
                
                if buttons:
                    print(f"\n  Buttons ({len(buttons)}):")
                    for i, button in enumerate(buttons[:5], 1):
                        print(f"    {i}. {button['text']}")
                
                if inputs:
                    print(f"\n  Input Fields ({len(inputs)}):")
                    for i, inp in enumerate(inputs[:5], 1):
                        print(f"    {i}. Type: {inp['input_type']}, Name: {inp['name']}")
                        if inp['placeholder']:
                            print(f"       Placeholder: {inp['placeholder']}")
            else:
                print(f"✗ Analysis failed: {result['message']}")
        else:
            print(f"✗ Failed to open website: {result['message']}")
        
        # Keep browser open for a moment
        print("\n3. Browser will close in 5 seconds...")
        time.sleep(5)
        
        # Close browser
        selenium_handler.close_browser()
        print("✓ Browser closed")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        selenium_handler.cleanup()
    
    print("\n" + "=" * 60)


def demo_interactive_selection():
    """Demonstrate interactive element selection."""
    print("=" * 60)
    print("Interactive Element Selection Demo")
    print("=" * 60)
    
    # Initialize components
    voice_processor = VoiceProcessor()
    selenium_handler = SeleniumHandler(voice_processor=voice_processor)
    
    try:
        print("\n1. Opening YouTube...")
        print("-" * 60)
        
        # Open YouTube
        result = selenium_handler.open_website({'url': 'https://www.youtube.com'})
        
        if result['status'] == 'completed':
            print(f"✓ {result['message']}")
            
            # Wait for page to load
            time.sleep(3)
            
            print("\n2. Byte is analyzing the page and will speak...")
            print("-" * 60)
            
            # Analyze page - Byte will speak the options
            result = selenium_handler.analyze_page()
            
            if result['status'] == 'completed':
                elements = result['data']['elements']
                print(f"✓ Byte identified {len(elements)} elements")
                print("  (Byte should have spoken the available options)")
                
                # Simulate user selection
                print("\n3. Simulating user selection...")
                print("-" * 60)
                
                # Find search box
                search_input = None
                for elem in elements:
                    if elem['type'] == 'input' and elem.get('name') == 'search_query':
                        search_input = elem
                        break
                
                if search_input:
                    print("✓ Found search box")
                    print("  User could now say: 'Search for AI tutorials'")
                    print("  And Byte would type in the search box and search")
                else:
                    print("  Search box not found in analyzed elements")
            else:
                print(f"✗ Analysis failed: {result['message']}")
        else:
            print(f"✗ Failed to open website: {result['message']}")
        
        # Keep browser open for a moment
        print("\n4. Browser will close in 5 seconds...")
        time.sleep(5)
        
        # Close browser
        selenium_handler.close_browser()
        print("✓ Browser closed")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        selenium_handler.cleanup()
    
    print("\n" + "=" * 60)


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("BYTE - VISUAL SCREEN ANALYSIS SYSTEM")
    print("=" * 60)
    print("\nThis demo shows Byte's ability to:")
    print("  1. Analyze the screen and identify components")
    print("  2. Analyze web pages and identify clickable elements")
    print("  3. Ask the user which element to interact with")
    print("\n" + "=" * 60)
    
    # Demo 1: Visual screen analysis
    print("\n\nDEMO 1: Visual Screen Analysis")
    demo_visual_screen_analysis()
    
    input("\nPress Enter to continue to Demo 2...")
    
    # Demo 2: Selenium page analysis
    print("\n\nDEMO 2: Selenium Page Analysis")
    demo_selenium_page_analysis()
    
    input("\nPress Enter to continue to Demo 3...")
    
    # Demo 3: Interactive selection
    print("\n\nDEMO 3: Interactive Element Selection")
    demo_interactive_selection()
    
    print("\n\n" + "=" * 60)
    print("All demos completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

