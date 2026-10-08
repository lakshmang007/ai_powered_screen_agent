"""
JARVIS's conversational brain: answers questions and small talk in character,
with short-term memory and live system status (time, battery, CPU, memory).

Uses Groq (GROQ_API_KEY) or Gemini (GEMINI_API_KEY). Without either it falls
back to canned replies, so voice control still works offline.
"""

import os
import re
import time
import logging
import datetime
from collections import deque
from typing import Dict, Optional

from . import jarvis_persona as persona

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are J.A.R.V.I.S., the AI assistant from the Iron Man films, running on the user's Windows PC.
Speak exactly like JARVIS in the films: British, impeccably polite, calm, quietly witty, understated.
Address the user as "{sir}".

Your replies are SPOKEN ALOUD, so:
- 1 or 2 short sentences, at most about 35 words. No lists, markdown, emoji or URLs.
- Never say you are a language model; you are JARVIS.

Answer general-knowledge, maths and conversational questions directly and confidently.
Desktop actions (opening apps, clicking, typing, web searches, sending WhatsApp messages,
playing macros) are carried out by your other systems; if asked what you can do, mention them.
If answering needs live or current information you cannot know (news, weather, sports scores,
prices, today's events), reply with exactly one line: SEARCH: <search query>

For a "status report", summarise like JARVIS would ("All systems nominal, {sir}. Power at 99 percent
and charging."), mentioning only what matters; never recite every figure.

Live system status: {status}
Recent actions: {actions}"""


def system_status() -> str:
    """One line of live facts JARVIS can quote ("status report")."""
    now = datetime.datetime.now()
    parts = [now.strftime("%A %d %B %Y, %I:%M %p").replace(" 0", " ")]
    try:
        import psutil
        battery = psutil.sensors_battery()
        if battery:
            parts.append(f"battery {battery.percent:.0f}%{' and charging' if battery.power_plugged else ' on battery power'}")
        parts.append(f"CPU {psutil.cpu_percent(interval=0.2):.0f}%")
        mem = psutil.virtual_memory()
        parts.append(f"memory {mem.percent:.0f}% used")
    except Exception:
        pass
    # (No window titles: they can contain private chat/document names)
    return "; ".join(parts)


class JarvisBrain:
    def __init__(self, max_turns: int = 8):
        self.history = deque(maxlen=max_turns * 2)
        self.provider = None
        self.client = None
        self.model = None
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        try:
            if groq_key and not groq_key.startswith("your_"):
                from groq import Groq
                self.client = Groq(api_key=groq_key, timeout=12, max_retries=1)
                self.provider = "groq"
                self.model = os.getenv("JARVIS_BRAIN_MODEL", "openai/gpt-oss-20b")
            elif gemini_key and not gemini_key.startswith("your_"):
                from google import genai
                self.client = genai.Client(api_key=gemini_key)
                self.provider = "gemini"
                self.model = os.getenv("JARVIS_BRAIN_MODEL", "gemini-2.5-flash")
        except Exception as e:
            logger.warning(f"JARVIS brain unavailable: {e}")
            self.client = None

    @property
    def available(self) -> bool:
        return self.client is not None

    def remember_action(self, description: str):
        """Note something JARVIS did, so follow-ups like 'did it work?' have context."""
        self.history.append({"role": "assistant", "content": f"(action) {description}"})

    def respond(self, user_text: str, recent_actions: str = "none") -> Dict[str, str]:
        """Return {'reply': text} or {'search': query}."""
        if not self.available:
            return {"reply": persona.didnt_catch()}

        system = SYSTEM_PROMPT.format(sir=persona.address(), status=system_status(), actions=recent_actions or "none")
        messages = [{"role": "system", "content": system}, *self.history, {"role": "user", "content": user_text}]
        try:
            start = time.time()
            text = self._complete(messages)
            logger.info(f"Brain replied in {time.time() - start:.2f}s")
        except Exception as e:
            logger.warning(f"Brain request failed: {e}")
            return {"reply": persona.failed("my connection to the server seems to be down")}

        text = (text or "").strip()
        search = re.match(r"^\s*SEARCH:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
        self.history.append({"role": "user", "content": user_text})
        if search:
            query = search.group(1).strip().strip('"')
            self.history.append({"role": "assistant", "content": f"(searched the web for: {query})"})
            return {"search": query}

        reply = self._clean_for_speech(text) or persona.didnt_catch()
        self.history.append({"role": "assistant", "content": reply})
        return {"reply": reply}

    def _complete(self, messages) -> str:
        if self.provider == "groq":
            request = dict(model=self.model, messages=messages, temperature=0.6, max_tokens=600)
            if "gpt-oss" in self.model:
                request["reasoning_effort"] = "low"
            return self.client.chat.completions.create(**request).choices[0].message.content
        # Gemini: fold the conversation into one prompt
        prompt = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages) + "\nASSISTANT:"
        return self.client.models.generate_content(model=self.model, contents=prompt).text

    @staticmethod
    def _clean_for_speech(text: str) -> str:
        text = re.sub(r"[*_#`>]+", "", text)                 # markdown
        text = re.sub(r"https?://\S+", "", text)              # URLs
        text = re.sub(r"\s*\n+\s*", " ", text)                # newlines
        text = re.sub(r"[\U0001F300-\U0001FAFF☀-➿]", "", text)  # emoji
        # Typographic spaces/dashes/quotes -> ASCII (TTS and Windows consoles trip on them)
        text = re.sub(r"[  -​  ]", " ", text)
        text = re.sub(r"[‐-―]", "-", text)
        text = text.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
        return re.sub(r" {2,}", " ", text).strip()
