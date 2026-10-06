#!/usr/bin/env python3
"""
AI Command Converter - Uses free AI APIs to convert natural language to structured commands

Supports:
- Google Gemini API (free tier)
- Groq API (free tier - very fast)
- Ollama (local, completely free)

Provider selection (first match wins):
1. Explicit ``provider`` argument
2. ``AI_PROVIDER`` environment variable
3. Whichever API key is present: GEMINI_API_KEY -> gemini, GROQ_API_KEY -> groq
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Model names can be overridden from .env without touching code
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"  # llama3-8b / llama-3.1-8b were retired by Groq
DEFAULT_OLLAMA_MODEL = "llama3.2"

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


@dataclass
class AICommand:
    """Structured command from AI."""
    action: str
    application: str
    target: str
    parameters: Dict[str, Any]
    confidence: float
    raw_response: str


def _real_key(value: Optional[str]) -> Optional[str]:
    """Return the key unless it is empty or the .env.example placeholder."""
    if not value or value.strip().lower().startswith("your_"):
        return None
    return value.strip()


class AICommandConverter:
    """Convert natural language commands using AI APIs."""

    def __init__(self, api_key: Optional[str] = None, provider: Optional[str] = None):
        """
        Initialize AI Command Converter.

        Args:
            api_key: API key for the provider (not needed for Ollama)
            provider: "gemini", "groq" or "ollama". Auto-detected when omitted.
        """
        self.logger = logging.getLogger(__name__)

        gemini_key = _real_key(os.getenv('GEMINI_API_KEY'))
        groq_key = _real_key(os.getenv('GROQ_API_KEY'))

        provider = (provider or os.getenv('AI_PROVIDER') or '').lower().strip()
        if not provider:
            if gemini_key:
                provider = "gemini"
            elif groq_key:
                provider = "groq"
            else:
                provider = "gemini"  # will log a "no key" warning and stay disabled
        self.provider = provider

        # Only ever use the key that belongs to the selected provider
        if api_key:
            self.api_key = api_key
        elif provider == "gemini":
            self.api_key = gemini_key
        elif provider == "groq":
            self.api_key = groq_key
        else:
            self.api_key = None

        self.client = None
        self._gemini_sdk = None  # "genai" (new SDK) or "generativeai" (legacy SDK)
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
        """Initialize Google Gemini (prefers the new google-genai SDK)."""
        if not self.api_key:
            self.logger.warning("No Gemini API key found. Set GEMINI_API_KEY in .env")
            return

        self.gemini_model = os.getenv('GEMINI_MODEL', DEFAULT_GEMINI_MODEL)

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self._gemini_sdk = "genai"
        except ImportError:
            try:
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=self.api_key)
                self.client = legacy_genai.GenerativeModel(self.gemini_model)
                self._gemini_sdk = "generativeai"
            except ImportError:
                self.logger.warning("Gemini SDK not installed. Run: pip install google-genai")
                return

        self.logger.info(f"✅ Gemini AI initialized ({self.gemini_model})")

    def _init_groq(self):
        """Initialize Groq API (uses the groq package, or plain HTTP if missing)."""
        if not self.api_key:
            self.logger.warning("No Groq API key found. Set GROQ_API_KEY in .env")
            return

        self.groq_model = os.getenv('GROQ_MODEL', DEFAULT_GROQ_MODEL)

        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            self.logger.info(f"✅ Groq AI initialized ({self.groq_model})")
        except ImportError:
            self.client = "http"  # Marker for HTTP mode
            self.logger.info(f"✅ Groq AI initialized via HTTP ({self.groq_model})")

    def _init_ollama(self):
        """Initialize Ollama (local)."""
        try:
            import ollama

            # Test if Ollama is running
            ollama.list()
            self.client = ollama
            self.ollama_model = os.getenv('OLLAMA_MODEL', DEFAULT_OLLAMA_MODEL)
            self.logger.info(f"✅ Ollama initialized ({self.ollama_model})")
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
            prompt = self._create_prompt(natural_language)

            if self.provider == "gemini":
                response = self._query_gemini(prompt)
            elif self.provider == "groq":
                response = self._query_groq(prompt)
            elif self.provider == "ollama":
                response = self._query_ollama(prompt)
            else:
                return None

            return self._parse_ai_response(response, natural_language)

        except Exception as e:
            self.logger.error(f"AI conversion error: {e}")
            return None

    def _create_prompt(self, command: str) -> str:
        """Create the AI prompt for command conversion."""
        return f"""You are a command parser for a Windows automation assistant.
Convert the following natural language command into a structured JSON format.

Available Actions: open, click, type, press, search, navigate, send, post, create, close, scroll, wait, erase, clear, select, delete, minimize, multi_step, erase_and_type
Available Applications: vscode, gmail, linkedin, chrome, firefox, notepad, explorer, terminal, macro, unknown

Rules:
- "target" keeps the user's original casing (file names, text to type).
- For "press", target is the key name (enter, escape, tab, win, ...).
- For "navigate", target is the URL or site name.
- Use "multi_step" when the command has several actions; put each simple step in parameters.steps.

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
    "application": "unknown",
    "target": "chatgpt",
    "parameters": {{"steps": ["press win", "type chatgpt", "press enter"]}},
    "confidence": 0.95
}}

Command: "open chrome and search for AI tutorials"
{{
    "action": "multi_step",
    "application": "chrome",
    "target": "AI tutorials",
    "parameters": {{"steps": ["open chrome", "navigate https://www.google.com/search?q=AI+tutorials"]}},
    "confidence": 0.9
}}

Command: "erase that and type hello world"
{{
    "action": "erase_and_type",
    "application": "unknown",
    "target": "hello world",
    "parameters": {{}},
    "confidence": 0.95
}}

Now convert: "{command}"
"""

    def _query_gemini(self, prompt: str) -> str:
        """Query Google Gemini API."""
        if self._gemini_sdk == "genai":
            response = self.client.models.generate_content(model=self.gemini_model, contents=prompt)
        else:
            response = self.client.generate_content(prompt)
        return response.text

    def _query_groq(self, prompt: str) -> str:
        """Query Groq API."""
        request = {
            "model": self.groq_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1024,
        }
        # gpt-oss models reason before answering; keep that short so the JSON
        # answer isn't cut off by max_tokens and latency stays low
        if "gpt-oss" in self.groq_model:
            request["reasoning_effort"] = "low"

        if self.client == "http":
            import requests

            response = requests.post(
                GROQ_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request,
                timeout=15
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        chat_completion = self.client.chat.completions.create(**request)
        return chat_completion.choices[0].message.content

    def _query_ollama(self, prompt: str) -> str:
        """Query Ollama (local)."""
        response = self.client.chat(
            model=self.ollama_model,
            messages=[{'role': 'user', 'content': prompt}]
        )
        return response['message']['content']

    def _parse_ai_response(self, response: str, original_command: str) -> Optional[AICommand]:
        """Parse AI response into AICommand object."""
        if not response:
            return None
        try:
            # Models sometimes wrap JSON in markdown or add prose; grab the outer object
            match = re.search(r'\{.*\}', response, re.DOTALL)
            payload = match.group(0) if match else response.strip()
            data = json.loads(payload)

            parameters = data.get('parameters') or {}
            if not isinstance(parameters, dict):
                parameters = {}

            try:
                confidence = float(data.get('confidence', 0.5))
            except (TypeError, ValueError):
                confidence = 0.5

            return AICommand(
                action=str(data.get('action') or 'unknown'),
                application=str(data.get('application') or 'unknown'),
                target=str(data.get('target') or ''),
                parameters=parameters,
                confidence=confidence,
                raw_response=payload
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
