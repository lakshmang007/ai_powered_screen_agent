#!/usr/bin/env python3
"""Check available Gemini models"""

import os
from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai

api_key = os.getenv('GEMINI_API_KEY')
print(f"API Key: {api_key[:20]}...")

genai.configure(api_key=api_key)

print("\n📋 Available Gemini Models:\n")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Description: {model.description}")
        print()

