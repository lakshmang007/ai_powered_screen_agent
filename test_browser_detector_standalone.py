"""
Standalone test for browser detection.
Tests browser_detector.py without importing other modules.
"""

import os
import winreg
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleBrowserDetector:
    """Simplified browser detector for testing."""
    
    def __init__(self):
        """Initialize browser detector."""
        self.browser_info = {
            'chrome': {
                'name': 'Google Chrome',
                'executable': 'chrome.exe',
                'paths': [
                    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                    os.path.expanduser(r'~\AppData\Local\Google\Chrome\Application\chrome.exe')
                ],
                'registry_key': r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe',
                'command': 'chrome'
            },
            'firefox': {
                'name': 'Mozilla Firefox',
                'executable': 'firefox.exe',
                'paths': [
                    r'C:\Program Files\Mozilla Firefox\firefox.exe',
                    r'C:\Program Files (x86)\Mozilla Firefox\firefox.exe'
                ],
                'registry_key': r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe',
                'command': 'firefox'
            },
            'edge': {
                'name': 'Microsoft Edge',
                'executable': 'msedge.exe',
                'paths': [
                    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe'
                ],
                'registry_key': r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe',
                'command': 'msedge'
            },
            'opera': {
                'name': 'Opera',
                'executable': 'opera.exe',
                'paths': [
                    r'C:\Program Files\Opera\launcher.exe',
                    r'C:\Program Files (x86)\Opera\launcher.exe',
                    os.path.expanduser(r'~\AppData\Local\Programs\Opera\launcher.exe'),
                    os.path.expanduser(r'~\AppData\Local\Programs\Opera GX\opera.exe')
                ],
                'registry_key': r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\opera.exe',
                'command': 'opera'
            },
            'brave': {
                'name': 'Brave',
                'executable': 'brave.exe',
                'paths': [
                    r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
                    r'C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe',
                    os.path.expanduser(r'~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe')
                ],
                'registry_key': r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\brave.exe',
                'command': 'brave'
            }
        }
    
    def detect_installed_browsers(self):
        """Detect all installed browsers."""
        installed = []
        
        for browser_id, info in self.browser_info.items():
            if self._is_browser_installed(browser_id):
                path = self._get_browser_path(browser_id)
                installed.append({
                    'id': browser_id,
                    'name': info['name'],
                    'command': info['command'],
                    'path': path
                })
                logger.info(f"✅ Detected: {info['name']}")
        
        return installed
    
    def _is_browser_installed(self, browser_id):
        """Check if browser is installed."""
        info = self.browser_info.get(browser_id)
        if not info:
            return False
        
        # Check common paths
        for path in info['paths']:
            if os.path.exists(path):
                return True
        
        # Check registry
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, info['registry_key'])
            winreg.CloseKey(key)
            return True
        except (WindowsError, OSError):
            pass
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, info['registry_key'])
            winreg.CloseKey(key)
            return True
        except (WindowsError, OSError):
            pass
        
        return False
    
    def _get_browser_path(self, browser_id):
        """Get browser installation path."""
        info = self.browser_info.get(browser_id)
        if not info:
            return None
        
        # Check common paths
        for path in info['paths']:
            if os.path.exists(path):
                return path
        
        # Check registry - HKEY_LOCAL_MACHINE
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, info['registry_key'])
            path = winreg.QueryValue(key, None)
            winreg.CloseKey(key)
            if path:
                # Remove quotes if present
                path = path.strip('"').strip("'")
                if os.path.exists(path):
                    return path
        except (WindowsError, OSError):
            pass

        # Check registry - HKEY_CURRENT_USER
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, info['registry_key'])
            path = winreg.QueryValue(key, None)
            winreg.CloseKey(key)
            if path:
                # Remove quotes if present
                path = path.strip('"').strip("'")
                if os.path.exists(path):
                    return path
        except (WindowsError, OSError):
            pass
        
        return None


def test_browser_detection():
    """Test browser detection."""
    print("=" * 70)
    print("Browser Detection Test")
    print("=" * 70)
    print()
    
    detector = SimpleBrowserDetector()
    
    print("Detecting installed browsers...")
    print()
    
    installed_browsers = detector.detect_installed_browsers()
    
    if not installed_browsers:
        print("❌ No browsers detected!")
        print()
        print("Checking individual browsers:")
        for browser_id in ['chrome', 'firefox', 'edge', 'opera', 'brave']:
            is_installed = detector._is_browser_installed(browser_id)
            print(f"  {browser_id.capitalize()}: {'✅ Installed' if is_installed else '❌ Not installed'}")
        return
    
    print(f"✅ Found {len(installed_browsers)} browser(s):")
    print()
    
    for i, browser in enumerate(installed_browsers, 1):
        print(f"  {i}. {browser['name']}")
        print(f"     ID: {browser['id']}")
        print(f"     Command: {browser['command']}")
        print(f"     Path: {browser['path']}")
        print()
    
    print("=" * 70)


def test_path_checking():
    """Test path checking."""
    print()
    print("=" * 70)
    print("Path Checking Test")
    print("=" * 70)
    print()
    
    detector = SimpleBrowserDetector()
    
    for browser_id, info in detector.browser_info.items():
        print(f"{info['name']}:")
        print(f"  Checking paths:")
        
        found = False
        for path in info['paths']:
            exists = os.path.exists(path)
            if exists:
                print(f"    ✅ {path}")
                found = True
            else:
                print(f"    ❌ {path}")
        
        if not found:
            print(f"    ⚠️  No paths found")
        
        print()
    
    print("=" * 70)


def test_registry_checking():
    """Test registry checking."""
    print()
    print("=" * 70)
    print("Registry Checking Test")
    print("=" * 70)
    print()
    
    detector = SimpleBrowserDetector()
    
    for browser_id, info in detector.browser_info.items():
        print(f"{info['name']}:")
        print(f"  Registry key: {info['registry_key']}")
        
        # Check HKEY_LOCAL_MACHINE
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, info['registry_key'])
            path = winreg.QueryValue(key, None)
            winreg.CloseKey(key)
            print(f"    ✅ HKLM: {path}")
        except (WindowsError, OSError) as e:
            print(f"    ❌ HKLM: Not found")
        
        # Check HKEY_CURRENT_USER
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, info['registry_key'])
            path = winreg.QueryValue(key, None)
            winreg.CloseKey(key)
            print(f"    ✅ HKCU: {path}")
        except (WindowsError, OSError) as e:
            print(f"    ❌ HKCU: Not found")
        
        print()
    
    print("=" * 70)


if __name__ == "__main__":
    print()
    print("🔍 Browser Detection Test Suite (Standalone)")
    print()
    
    try:
        # Run tests
        test_browser_detection()
        test_path_checking()
        test_registry_checking()
        
        print()
        print("✅ All tests completed!")
        print()
        
    except Exception as e:
        print()
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        print()

