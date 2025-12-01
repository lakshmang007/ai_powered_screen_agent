"""
Test multiple match handling for system search.
"""

import os
import winreg


def search_start_menu_all(app_name):
    """Search in Start Menu shortcuts and return ALL matches."""
    matches = []
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
                            # Extract clean name
                            clean_name = file.replace('.lnk', '').replace('.exe', '')
                            matches.append({
                                'name': clean_name,
                                'path': os.path.join(root, file),
                                'method': 'start_menu'
                            })
        
        return matches
    
    except Exception as e:
        print(f"Start menu search failed: {e}")
        return []


def search_in_paths_all(app_name):
    """Search in common installation paths and return ALL matches."""
    matches = []
    try:
        search_paths = [
            r'C:\Program Files',
            r'C:\Program Files (x86)',
            os.path.expanduser(r'~\AppData\Local'),
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
                            # Extract clean name
                            clean_name = file.replace('.exe', '')
                            matches.append({
                                'name': clean_name,
                                'path': os.path.join(root, file),
                                'method': 'file_search'
                            })
        
        return matches
    
    except Exception as e:
        print(f"Path search failed: {e}")
        return []


def test_search_microsoft():
    """Test searching for 'microsoft' - should find multiple apps."""
    print("=" * 70)
    print("Test: Searching for 'microsoft'")
    print("=" * 70)
    print()
    
    app_name = "microsoft"
    
    print("Searching in Start Menu...")
    start_menu_matches = search_start_menu_all(app_name)
    print(f"Found {len(start_menu_matches)} matches in Start Menu:")
    for match in start_menu_matches[:5]:  # Show first 5
        print(f"  - {match['name']}")
    if len(start_menu_matches) > 5:
        print(f"  ... and {len(start_menu_matches) - 5} more")
    print()
    
    print("Searching in common paths...")
    path_matches = search_in_paths_all(app_name)
    print(f"Found {len(path_matches)} matches in paths:")
    for match in path_matches[:5]:  # Show first 5
        print(f"  - {match['name']}")
    if len(path_matches) > 5:
        print(f"  ... and {len(path_matches) - 5} more")
    print()
    
    # Combine and remove duplicates
    all_matches = start_menu_matches + path_matches
    unique_matches = []
    seen_paths = set()
    for match in all_matches:
        path_lower = match['path'].lower()
        if path_lower not in seen_paths:
            seen_paths.add(path_lower)
            unique_matches.append(match)
    
    print(f"Total unique matches: {len(unique_matches)}")
    print()
    print("Top matches:")
    for i, match in enumerate(unique_matches[:10], 1):
        print(f"  {i}. {match['name']}")
        print(f"     Path: {match['path']}")
    
    print()
    print("=" * 70)


def test_search_dolby():
    """Test searching for 'dolby'."""
    print()
    print("=" * 70)
    print("Test: Searching for 'dolby'")
    print("=" * 70)
    print()
    
    app_name = "dolby"
    
    print("Searching in Start Menu...")
    start_menu_matches = search_start_menu_all(app_name)
    print(f"Found {len(start_menu_matches)} matches in Start Menu:")
    for match in start_menu_matches:
        print(f"  - {match['name']}")
        print(f"    Path: {match['path']}")
    print()
    
    print("Searching in common paths...")
    path_matches = search_in_paths_all(app_name)
    print(f"Found {len(path_matches)} matches in paths:")
    for match in path_matches:
        print(f"  - {match['name']}")
        print(f"    Path: {match['path']}")
    print()
    
    # Combine and remove duplicates
    all_matches = start_menu_matches + path_matches
    unique_matches = []
    seen_paths = set()
    for match in all_matches:
        path_lower = match['path'].lower()
        if path_lower not in seen_paths:
            seen_paths.add(path_lower)
            unique_matches.append(match)
    
    print(f"Total unique matches: {len(unique_matches)}")
    if unique_matches:
        print()
        print("Matches:")
        for i, match in enumerate(unique_matches, 1):
            print(f"  {i}. {match['name']}")
            print(f"     Path: {match['path']}")
    else:
        print("❌ No matches found for 'dolby'")
    
    print()
    print("=" * 70)


def test_search_chrome():
    """Test searching for 'chrome'."""
    print()
    print("=" * 70)
    print("Test: Searching for 'chrome'")
    print("=" * 70)
    print()
    
    app_name = "chrome"
    
    print("Searching in Start Menu...")
    start_menu_matches = search_start_menu_all(app_name)
    print(f"Found {len(start_menu_matches)} matches in Start Menu:")
    for match in start_menu_matches:
        print(f"  - {match['name']}")
    print()
    
    print("Searching in common paths...")
    path_matches = search_in_paths_all(app_name)
    print(f"Found {len(path_matches)} matches in paths:")
    for match in path_matches:
        print(f"  - {match['name']}")
    print()
    
    # Combine and remove duplicates
    all_matches = start_menu_matches + path_matches
    unique_matches = []
    seen_paths = set()
    for match in all_matches:
        path_lower = match['path'].lower()
        if path_lower not in seen_paths:
            seen_paths.add(path_lower)
            unique_matches.append(match)
    
    print(f"Total unique matches: {len(unique_matches)}")
    if unique_matches:
        print()
        print("Matches:")
        for i, match in enumerate(unique_matches, 1):
            print(f"  {i}. {match['name']}")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    print()
    print("🔍 Multiple Match Detection Test Suite")
    print()
    
    try:
        test_search_microsoft()
        test_search_dolby()
        test_search_chrome()
        
        print()
        print("✅ All tests completed!")
        print()
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print()

