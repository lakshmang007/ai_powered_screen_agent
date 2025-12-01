"""
Test app name extraction and multiple match handling.
"""

# Test app name extraction
def extract_app_name(command):
    """Extract app name from command."""
    # Remove common words and phrases
    words_to_remove = [
        'open', 'launch', 'start', 'run', 'the', 'app', 'application', 'program',
        'in', 'my', 'windows', 'on', 'computer', 'pc', 'laptop', 'system',
        'please', 'can', 'you', 'could', 'would', 'for', 'me', 'byte'
    ]
    
    # Convert to lowercase and split
    words = command.lower().split()
    
    # Remove stop words
    app_words = [w for w in words if w not in words_to_remove]
    
    # Join remaining words
    app_name = " ".join(app_words) if app_words else None
    
    return app_name


def test_extraction():
    """Test app name extraction."""
    print("=" * 70)
    print("App Name Extraction Tests")
    print("=" * 70)
    print()
    
    test_cases = [
        ("open dolby atmos", "dolby atmos"),
        ("open dolby in my windows", "dolby"),
        ("launch microsoft", "microsoft"),
        ("start microsoft word", "microsoft word"),
        ("run spotify on my computer", "spotify"),
        ("open chrome browser", "chrome browser"),
        ("can you open notepad please", "notepad"),
        ("byte open calculator", "calculator"),
        ("open the app discord", "discord"),
    ]
    
    passed = 0
    failed = 0
    
    for command, expected in test_cases:
        result = extract_app_name(command)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status}")
        print(f"  Command:  '{command}'")
        print(f"  Expected: '{expected}'")
        print(f"  Got:      '{result}'")
        print()
    
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)


if __name__ == "__main__":
    test_extraction()

