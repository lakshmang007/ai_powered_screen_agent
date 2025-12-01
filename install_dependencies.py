#!/usr/bin/env python3
"""
Dependency Installation Script for Byte Smart
Installs packages one by one and reports success/failure
"""

import subprocess
import sys

def print_header(text):
    print("\n" + "=" * 70)
    print(text.center(70))
    print("=" * 70 + "\n")

def install_package(package_name, description=""):
    """Install a single package and report status."""
    print(f"\n📦 Installing {package_name}...")
    if description:
        print(f"   Purpose: {description}")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ {package_name} installation failed (optional - continuing...)")
        return False

def main():
    print_header("🤖 Byte Smart Dependency Installer")
    
    print("This script will install dependencies for Byte Smart.")
    print("Some packages are optional - the system will work without them.")
    print()
    
    # Check if in virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if in_venv:
        print("⚠️  WARNING: You are in a virtual environment!")
        print("   Some packages may fail to build.")
        print("   Consider deactivating and using global Python.")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Exiting...")
            return
    
    # Core dependencies (required)
    print_header("Installing Core Dependencies (Required)")
    
    core_packages = [
        ("python-dotenv", "Environment variable management"),
        ("SpeechRecognition", "Voice input"),
        ("pyttsx3", "Text-to-speech"),
    ]
    
    core_success = 0
    for package, desc in core_packages:
        if install_package(package, desc):
            core_success += 1
    
    print(f"\n✅ Core packages: {core_success}/{len(core_packages)} installed")
    
    # Optional dependencies
    print_header("Installing Optional Dependencies")
    
    optional_packages = [
        ("opencv-python", "Screen analysis and image processing"),
        ("numpy", "Numerical operations"),
        ("pillow", "Image handling"),
        ("pyautogui", "Mouse and keyboard control"),
        ("pynput", "Input monitoring"),
        ("mss", "Screen capture"),
        ("pytesseract", "OCR text recognition"),
        ("selenium", "Web automation"),
        ("webdriver-manager", "Browser driver management"),
        ("requests", "HTTP requests"),
        ("psutil", "Process management"),
        ("pygetwindow", "Window management"),
    ]
    
    optional_success = 0
    for package, desc in optional_packages:
        if install_package(package, desc):
            optional_success += 1
    
    print(f"\n✅ Optional packages: {optional_success}/{len(optional_packages)} installed")
    
    # Summary
    print_header("Installation Summary")
    
    total_success = core_success + optional_success
    total_packages = len(core_packages) + len(optional_packages)
    
    print(f"Total packages installed: {total_success}/{total_packages}")
    print()
    
    if core_success == len(core_packages):
        print("✅ All core dependencies installed!")
        print("   Byte Smart should work with basic features.")
    else:
        print("⚠️  Some core dependencies failed to install.")
        print("   Byte Smart may not work properly.")
    
    print()
    print("Next steps:")
    print("1. Run: python byte_smart.py")
    print("2. Or run: python demo_indian_english.py")
    print("3. Check RESTORATION_PLAN.md for troubleshooting")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

