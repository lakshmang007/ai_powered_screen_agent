#!/usr/bin/env python3
"""
AI Setup Helper - Automatically detects and installs the best AI provider
"""

import subprocess
import sys
import os

def install_package(package_name):
    """Install a package using pip."""
    print(f"📦 Installing {package_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name, "--prefer-binary"])
        print(f"✅ {package_name} installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package_name}")
        return False

def test_import(module_name):
    """Test if a module can be imported."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def setup_ai():
    """Setup AI provider for Byte Smart."""
    print("=" * 70)
    print("🤖 Byte Smart - AI Setup Helper")
    print("=" * 70)
    print("\nThis will help you set up FREE AI-powered command understanding.\n")
    
    # Check what's already installed
    print("🔍 Checking installed packages...\n")
    
    has_gemini = test_import("google.generativeai")
    has_groq = test_import("groq")
    has_ollama = test_import("ollama")
    
    if has_gemini:
        print("✅ Google Gemini SDK already installed")
    if has_groq:
        print("✅ Groq SDK already installed")
    if has_ollama:
        print("✅ Ollama SDK already installed")
    
    if has_gemini or has_groq or has_ollama:
        print("\n✨ You already have at least one AI provider installed!")
        print("\nNext steps:")
        if has_gemini:
            print("  1. Get Gemini API key: https://makersuite.google.com/app/apikey")
            print("  2. Add to .env: GEMINI_API_KEY=your_key_here")
        if has_groq:
            print("  1. Get Groq API key: https://console.groq.com")
            print("  2. Add to .env: GROQ_API_KEY=your_key_here")
        if has_ollama:
            print("  1. Download Ollama: https://ollama.ai")
            print("  2. Run: ollama pull llama2")
        return
    
    # Nothing installed, let's install
    print("\n📦 No AI providers found. Let's install one!\n")
    print("Choose an option:")
    print("  1. Groq (Recommended - easiest, no Rust required)")
    print("  2. Google Gemini (Most accurate, may need Rust)")
    print("  3. Ollama (Local, completely free, no API key)")
    print("  4. Skip for now")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        print("\n🚀 Installing Groq...")
        if install_package("groq"):
            print("\n✅ Groq installed successfully!")
            print("\n📝 Next steps:")
            print("  1. Get FREE API key: https://console.groq.com")
            print("  2. Create .env file with: GROQ_API_KEY=your_key_here")
            print("  3. Run: C:/Python313/python.exe byte_smart.py")
            
            # Create .env template
            if not os.path.exists(".env"):
                with open(".env", "w") as f:
                    f.write("# Groq API Key (get from https://console.groq.com)\n")
                    f.write("GROQ_API_KEY=your_groq_api_key_here\n")
                print("\n✅ Created .env file - add your API key there!")
    
    elif choice == "2":
        print("\n🚀 Installing Google Gemini...")
        print("⚠️  This may require Rust compiler. If it fails, choose Groq instead.\n")
        if install_package("google-generativeai"):
            print("\n✅ Gemini installed successfully!")
            print("\n📝 Next steps:")
            print("  1. Get FREE API key: https://makersuite.google.com/app/apikey")
            print("  2. Create .env file with: GEMINI_API_KEY=your_key_here")
            print("  3. Run: C:/Python313/python.exe byte_smart.py")
            
            # Create .env template
            if not os.path.exists(".env"):
                with open(".env", "w") as f:
                    f.write("# Gemini API Key (get from https://makersuite.google.com/app/apikey)\n")
                    f.write("GEMINI_API_KEY=your_gemini_api_key_here\n")
                print("\n✅ Created .env file - add your API key there!")
    
    elif choice == "3":
        print("\n🚀 Installing Ollama SDK...")
        if install_package("ollama"):
            print("\n✅ Ollama SDK installed!")
            print("\n📝 Next steps:")
            print("  1. Download Ollama: https://ollama.ai")
            print("  2. Install and run Ollama")
            print("  3. Run: ollama pull llama2")
            print("  4. Run: C:/Python313/python.exe byte_smart.py")
            print("\n💡 No API key needed - runs locally!")
    
    else:
        print("\n⏭️  Skipped AI setup.")
        print("   Byte will use regex-based parsing (70% accuracy)")
        print("   You can set up AI later for 95% accuracy!")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    setup_ai()

