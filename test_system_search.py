"""
Test script for System Search Handler.
Tests application search functionality.
"""

import logging
from src.automation.handlers.system_search_handler import SystemSearchHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_search_installed_apps():
    """Test searching for installed applications."""
    print()
    print("=" * 70)
    print("Test 1: Search for Installed Applications")
    print("=" * 70)
    print()
    
    handler = SystemSearchHandler()
    
    # Test with common applications
    test_apps = [
        'chrome',
        'notepad',
        'calculator',
        'paint',
        'vscode',
        'spotify',
        'discord'
    ]
    
    for app_name in test_apps:
        print(f"Searching for: {app_name}")
        result = handler.search_application(app_name)
        
        if result['status'] == 'found':
            print(f"  ✅ FOUND!")
            print(f"     Method: {result['method']}")
            print(f"     Path: {result.get('path', 'N/A')}")
        elif result['status'] == 'not_found':
            print(f"  ❌ NOT FOUND")
            print(f"     Action: {result.get('action', 'none')}")
        else:
            print(f"  ⚠️  ERROR: {result.get('message', 'Unknown error')}")
        
        print()
    
    print("=" * 70)


def test_search_methods():
    """Test individual search methods."""
    print()
    print("=" * 70)
    print("Test 2: Individual Search Methods")
    print("=" * 70)
    print()
    
    handler = SystemSearchHandler()
    app_name = "chrome"
    
    print(f"Testing search methods for: {app_name}")
    print()
    
    # Test Start Menu search
    print("1. Start Menu Search:")
    result = handler._search_start_menu(app_name)
    if result:
        print(f"   ✅ Found: {result}")
    else:
        print(f"   ❌ Not found")
    print()
    
    # Test path search
    print("2. Path Search:")
    result = handler._search_in_paths(app_name)
    if result:
        print(f"   ✅ Found: {result}")
    else:
        print(f"   ❌ Not found")
    print()
    
    # Test registry search
    print("3. Registry Search:")
    result = handler._search_registry(app_name)
    if result:
        print(f"   ✅ Found: {result}")
    else:
        print(f"   ❌ Not found")
    print()
    
    print("=" * 70)


def test_download_urls():
    """Test download URL retrieval."""
    print()
    print("=" * 70)
    print("Test 3: Download URL Retrieval")
    print("=" * 70)
    print()
    
    handler = SystemSearchHandler()
    
    test_apps = [
        'spotify',
        'discord',
        'slack',
        'zoom',
        'vscode',
        'notepad++',
        'vlc',
        'unknown_app'
    ]
    
    for app_name in test_apps:
        url = handler._get_download_url(app_name)
        if url:
            print(f"✅ {app_name:20} -> {url}")
        else:
            print(f"❌ {app_name:20} -> No URL found")
    
    print()
    print("=" * 70)


def test_not_found_handling():
    """Test handling of applications not found."""
    print()
    print("=" * 70)
    print("Test 4: Not Found Handling (No Voice)")
    print("=" * 70)
    print()
    
    handler = SystemSearchHandler()  # No voice processor
    
    # Test with app that doesn't exist
    app_name = "nonexistent_app_12345"
    print(f"Searching for non-existent app: {app_name}")
    result = handler.search_application(app_name)
    
    print(f"Status: {result['status']}")
    print(f"Action: {result.get('action', 'none')}")
    print(f"Message: {result.get('message', 'N/A')}")
    
    print()
    print("=" * 70)


def test_comprehensive_search():
    """Comprehensive search test."""
    print()
    print("=" * 70)
    print("Test 5: Comprehensive Search Results")
    print("=" * 70)
    print()
    
    handler = SystemSearchHandler()
    
    # Apps that should be found on most Windows systems
    common_apps = [
        ('notepad', 'Should be found'),
        ('calc', 'Calculator - should be found'),
        ('mspaint', 'Paint - should be found'),
        ('chrome', 'May or may not be installed'),
        ('spotify', 'Probably not installed'),
    ]
    
    found_count = 0
    not_found_count = 0
    
    for app_name, description in common_apps:
        print(f"Testing: {app_name} ({description})")
        result = handler.search_application(app_name)
        
        if result['status'] == 'found':
            found_count += 1
            print(f"  ✅ FOUND via {result['method']}")
            if result.get('path'):
                print(f"     Path: {result['path']}")
        else:
            not_found_count += 1
            print(f"  ❌ NOT FOUND")
        
        print()
    
    print("-" * 70)
    print(f"Summary: {found_count} found, {not_found_count} not found")
    print("=" * 70)


if __name__ == "__main__":
    print()
    print("🔍 System Search Handler Test Suite")
    print()
    
    try:
        # Run all tests
        test_search_installed_apps()
        test_search_methods()
        test_download_urls()
        test_not_found_handling()
        test_comprehensive_search()
        
        print()
        print("✅ All tests completed!")
        print()
        
    except Exception as e:
        print()
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        print()

