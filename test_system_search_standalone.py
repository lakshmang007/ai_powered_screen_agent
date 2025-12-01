"""
Standalone test for System Search Handler.
Tests application search without importing other modules.
"""

import logging
import os
import winreg

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)


def search_start_menu(app_name):
    """Search in Start Menu shortcuts."""
    try:
        start_menu_paths = [
            os.path.expanduser(r'~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs'),
            r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs'
        ]
        
        for base_path in start_menu_paths:
            if not os.path.exists(base_path):
                continue
            
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    if file.lower().endswith('.lnk') or file.lower().endswith('.exe'):
                        if app_name.lower() in file.lower():
                            return os.path.join(root, file)
        
        return None
    
    except Exception as e:
        logger.warning(f"Start menu search failed: {e}")
        return None


def search_in_paths(app_name):
    """Search in common installation paths."""
    try:
        search_paths = [
            r'C:\Program Files',
            r'C:\Program Files (x86)',
            os.path.expanduser(r'~\AppData\Local'),
            os.path.expanduser(r'~\AppData\Roaming'),
        ]
        
        for base_path in search_paths:
            if not os.path.exists(base_path):
                continue
            
            # Search only top 2 levels to avoid deep recursion
            for root, dirs, files in os.walk(base_path):
                # Limit depth
                depth = root[len(base_path):].count(os.sep)
                if depth > 2:
                    continue
                
                for file in files:
                    if file.lower().endswith('.exe'):
                        if app_name.lower() in file.lower():
                            return os.path.join(root, file)
        
        return None
    
    except Exception as e:
        logger.warning(f"Path search failed: {e}")
        return None


def search_registry(app_name):
    """Search in Windows Registry for installed applications."""
    try:
        registry_paths = [
            r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths',
        ]
        
        for reg_path in registry_paths:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                
                # Enumerate subkeys
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        if app_name.lower() in subkey_name.lower():
                            # Try to get the path
                            subkey = winreg.OpenKey(key, subkey_name)
                            try:
                                path = winreg.QueryValue(subkey, None)
                                path = path.strip('"').strip("'")
                                winreg.CloseKey(subkey)
                                if path and os.path.exists(path):
                                    winreg.CloseKey(key)
                                    return path
                            except:
                                pass
                        i += 1
                    except OSError:
                        break
                
                winreg.CloseKey(key)
            
            except WindowsError:
                continue
        
        return None
    
    except Exception as e:
        logger.warning(f"Registry search failed: {e}")
        return None


def test_search_application(app_name):
    """Test searching for an application."""
    print(f"\n{'='*70}")
    print(f"Searching for: {app_name}")
    print(f"{'='*70}")
    
    # Method 1: Start Menu
    print("\n1. Searching in Start Menu...")
    result = search_start_menu(app_name)
    if result:
        print(f"   ✅ FOUND: {result}")
        return result
    else:
        print(f"   ❌ Not found")
    
    # Method 2: Common Paths
    print("\n2. Searching in common paths...")
    result = search_in_paths(app_name)
    if result:
        print(f"   ✅ FOUND: {result}")
        return result
    else:
        print(f"   ❌ Not found")
    
    # Method 3: Registry
    print("\n3. Searching in registry...")
    result = search_registry(app_name)
    if result:
        print(f"   ✅ FOUND: {result}")
        return result
    else:
        print(f"   ❌ Not found")
    
    print(f"\n❌ {app_name} NOT FOUND in system")
    return None


def main():
    """Main test function."""
    print("\n🔍 System Search Test Suite (Standalone)")
    print()
    
    # Test with common applications
    test_apps = [
        'chrome',
        'notepad',
        'calc',
        'mspaint',
        'vscode',
        'spotify',
        'discord',
        'nonexistent_app'
    ]
    
    results = {}
    
    for app_name in test_apps:
        result = test_search_application(app_name)
        results[app_name] = result
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}\n")
    
    found_count = 0
    not_found_count = 0
    
    for app_name, path in results.items():
        if path:
            found_count += 1
            print(f"✅ {app_name:20} -> FOUND")
        else:
            not_found_count += 1
            print(f"❌ {app_name:20} -> NOT FOUND")
    
    print(f"\n{'-'*70}")
    print(f"Total: {found_count} found, {not_found_count} not found")
    print(f"{'='*70}\n")
    
    # Test download URLs
    print(f"\n{'='*70}")
    print("DOWNLOAD URLs for Common Apps")
    print(f"{'='*70}\n")
    
    download_urls = {
        'spotify': 'https://www.spotify.com/download',
        'discord': 'https://discord.com/download',
        'slack': 'https://slack.com/downloads',
        'zoom': 'https://zoom.us/download',
        'vscode': 'https://code.visualstudio.com/download',
        'vlc': 'https://www.videolan.org/vlc/',
    }
    
    for app_name, url in download_urls.items():
        print(f"{app_name:15} -> {url}")
    
    print(f"\n{'='*70}\n")
    print("✅ All tests completed!")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

