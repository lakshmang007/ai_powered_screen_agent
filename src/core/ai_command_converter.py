#!/usr/bin/env python3
"""
AI Command Converter - Uses free AI APIs to convert natural language to structured commands

Supports:
- Google Gemini API (free tier - 60 requests/minute)
- Groq API (free tier - very fast)
- Ollama (local, completely free)
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class AICommand:
    """Structured command from AI."""
    action: str
    application: str
    target: str
    parameters: Dict[str, Any]
    confidence: float
    raw_response: str


class AICommandConverter:
    """Convert natural language commands using AI APIs."""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "gemini"):
        """
        Initialize AI Command Converter.
        
        Args:
            api_key: API key for the provider (not needed for Ollama)
            provider: AI provider - "gemini", "groq", or "ollama"
        """
        self.logger = logging.getLogger(__name__)
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GROQ_API_KEY')
        
        # Initialize the appropriate client
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the AI client based on provider."""
        try:
            if self.provider == "gemini":
                self._init_gemini()
            elif self.provider == "groq":
                self._init_groq()
            elif self.provider == "ollama":
                self._init_ollama()
            else:
                self.logger.warning(f"Unknown provider: {self.provider}, falling back to regex")
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.provider}: {e}")
            self.logger.info("AI command conversion will be disabled")
    
    def _init_gemini(self):
        """Initialize Google Gemini."""
        try:
            import google.generativeai as genai

            if not self.api_key:
                self.logger.warning("No Gemini API key found. Set GEMINI_API_KEY environment variable")
                return

            genai.configure(api_key=self.api_key)
            # Use Gemini 2.5 Flash (stable, fast, and free)
            self.client = genai.GenerativeModel('gemini-2.5-flash')
            self.logger.info("✅ Gemini AI initialized successfully (gemini-2.5-flash)")
        except ImportError:
            self.logger.warning("google-generativeai not installed. Run: pip install google-generativeai")
        except Exception as e:
            self.logger.error(f"Gemini initialization error: {e}")
    
    def _init_groq(self):
        """Initialize Groq API."""
        try:
            # Try to import groq package
            try:
                from groq import Groq
                use_package = True
            except ImportError:
                # Fallback to direct HTTP requests (no package needed)
                import requests
                use_package = False
                self.logger.info("Using Groq via HTTP (no package needed)")

            if not self.api_key:
                self.logger.warning("No Groq API key found. Set GROQ_API_KEY environment variable")
                return

            if use_package:
                self.client = Groq(api_key=self.api_key)
                self.logger.info("✅ Groq AI initialized successfully")
            else:
                # Use HTTP client
                self.client = "http"  # Marker for HTTP mode
                self.groq_api_key = self.api_key
                self.logger.info("✅ Groq AI initialized (HTTP mode)")
        except Exception as e:
            self.logger.error(f"Groq initialization error: {e}")
    
    def _init_ollama(self):
        """Initialize Ollama (local)."""
        try:
            import ollama
            
            # Test if Ollama is running
            ollama.list()
            self.client = ollama
            self.logger.info("✅ Ollama initialized successfully")
        except ImportError:
            self.logger.warning("ollama not installed. Run: pip install ollama")
        except Exception as e:
            self.logger.error(f"Ollama initialization error: {e}")
            self.logger.info("Make sure Ollama is running: https://ollama.ai")
    
    def convert_command(self, natural_language: str) -> Optional[AICommand]:
        """
        Convert natural language to structured command using AI.
        
        Args:
            natural_language: User's natural language command
            
        Returns:
            AICommand object or None if conversion fails
        """
        if not self.client:
            self.logger.debug("AI client not available, skipping AI conversion")
            return None
        
        try:
            # Create the prompt
            prompt = self._create_prompt(natural_language)
            
            # Get AI response
            if self.provider == "gemini":
                response = self._query_gemini(prompt)
            elif self.provider == "groq":
                response = self._query_groq(prompt)
            elif self.provider == "ollama":
                response = self._query_ollama(prompt)
            else:
                return None
            
            # Parse the response
            return self._parse_ai_response(response, natural_language)

        except Exception as e:
            self.logger.error(f"AI conversion error: {e}")
            return None

    def _create_prompt(self, command: str) -> str:
        """Create the AI prompt for command conversion."""
        return f"""You are a command parser for a Windows automation assistant named Byte.
Convert the following natural language command into a structured JSON format.

Available Actions: open, click, type, press, search, navigate, send, post, create, close, scroll, wait, erase, clear, select, delete
Available Applications: vscode, gmail, linkedin, chrome, firefox, edge, notepad, explorer, terminal, calculator, unknown

Command: "{command}"

Return ONLY a JSON object with this exact structure (no markdown, no explanation):
{{
    "action": "the action to perform",
    "application": "the application to use",
    "target": "what to act on (text to type, button to click, key to press, etc.)",
    "parameters": {{}},
    "confidence": 0.95
}}

Examples:
Command: "click windows key and type ChatGPT and open it"
{{
    "action": "multi_step",
    "application": "windows",
    "target": "chatgpt",
    "parameters": {{"steps": ["press win", "type chatgpt", "press enter"]}},
    "confidence": 0.95
}}

Command: "open chrome and search for AI tutorials"
{{
    "action": "multi_step",
    "application": "chrome",
    "target": "AI tutorials",
    "parameters": {{"steps": ["open chrome", "search AI tutorials"]}},
    "confidence": 0.9
}}

Command: "erase that and type hello world"
{{
    "action": "erase_and_type",
    "application": "unknown",
    "target": "hello world",
    "parameters": {{"erase_first": true}},
    "confidence": 0.95
}}

Now convert: "{command}"
"""

    def _query_gemini(self, prompt: str) -> str:
        """Query Google Gemini API."""
        response = self.client.generate_content(prompt)
        return response.text

    def _query_groq(self, prompt: str) -> str:
        """Query Groq API."""
        if self.client == "http":
            # Use HTTP requests (no package needed)
            import requests

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama3-8b-8192",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 500
                }
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        else:
            # Use groq package
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.1,
                max_tokens=500
            )
            return chat_completion.choices[0].message.content

    def _query_ollama(self, prompt: str) -> str:
        """Query Ollama (local)."""
        response = self.client.chat(
            model='llama2',  # or 'mistral', 'phi', etc.
            messages=[{'role': 'user', 'content': prompt}]
        )
        return response['message']['content']

    def _parse_ai_response(self, response: str, original_command: str) -> Optional[AICommand]:
        """Parse AI response into AICommand object."""
        try:
            # Clean the response (remove markdown code blocks if present)
            response = response.strip()
            if response.startswith('```'):
                # Remove markdown code blocks
                lines = response.split('\n')
                response = '\n'.join(line for line in lines if not line.startswith('```'))

            # Parse JSON
            data = json.loads(response)

            return AICommand(
                action=data.get('action', 'unknown'),
                application=data.get('application', 'unknown'),
                target=data.get('target', ''),
                parameters=data.get('parameters', {}),
                confidence=data.get('confidence', 0.5),
                raw_response=response
            )
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse AI response as JSON: {e}")
            self.logger.debug(f"Response was: {response}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing AI response: {e}")
            return None

    def is_available(self) -> bool:
        """Check if AI conversion is available."""
        return self.client is not None


