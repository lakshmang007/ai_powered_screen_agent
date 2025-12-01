# 🎙️ Quick Start: Voice-Powered Automation

Get started with voice-powered automation in 5 minutes!

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install openai python-dotenv
```

### 2. Set API Key
Create a `.env` file:
```bash
OPENAI_API_KEY=sk-your-api-key-here
```

Get your API key: https://platform.openai.com/api-keys

### 3. Run the Demo
```bash
python examples/voice_automation_example.py
```

---

## 💡 Basic Usage

### Simple Voice Command
```python
from src.core.enhanced_voice_processor import EnhancedVoiceProcessor

# Initialize
voice = EnhancedVoiceProcessor()

# Listen for command
command = voice.listen_once(enhance_prompt=True)
print(f"Command: {command}")

# Example:
# You say: "open that email thing"
# Returns: "open Gmail in Chrome browser"
```

### Continuous Listening
```python
def handle_command(text):
    print(f"Executing: {text}")
    # Your automation code here

# Start listening (say "computer" first)
voice.start_continuous_listening(
    callback=handle_command,
    use_wake_word=True,
    enhance_prompts=True
)
```

### With Selenium
```python
from selenium import webdriver

driver = webdriver.Chrome()
voice = EnhancedVoiceProcessor()

# Listen for command
command = voice.listen_once(enhance_prompt=True)

# Execute with Selenium
if "gmail" in command.lower():
    driver.get("https://gmail.com")
    voice.speak("Gmail opened")
```

---

## 🎯 Example Commands

### Vague Commands (Auto-Enhanced)
| You Say | Enhanced To |
|---------|-------------|
| "open that email thing" | "open Gmail in Chrome browser" |
| "search for python" | "open Chrome and search Google for python tutorials" |
| "post on social media" | "open LinkedIn and create a new post" |
| "send message to John" | "open Gmail and compose email to John" |

### Specific Commands (Work Directly)
- "open VSCode"
- "create new file in VSCode"
- "scroll down the page"
- "click on the login button"
- "type hello world"

---

## 🔧 Configuration Options

### Basic Configuration
```python
voice = EnhancedVoiceProcessor(
    use_whisper=True,           # Use OpenAI Whisper (better accuracy)
    use_gpt_enhancement=True,   # Auto-enhance vague commands
    wake_word="computer"        # Wake word for continuous listening
)
```

### Advanced Configuration
```python
# Only enhance when confidence is low
command = voice.listen_once(enhance_prompt=False)
if confidence < 0.5:
    command = voice._enhance_prompt(command)

# Custom wake word
voice = EnhancedVoiceProcessor(wake_word="jarvis")

# Disable wake word
voice.start_continuous_listening(
    callback=handle_command,
    use_wake_word=False  # Always listening
)
```

---

## 📊 API Costs

### OpenAI Pricing
- **Whisper**: $0.006 per minute (~$0.36/hour)
- **GPT-4**: $0.03 per 1K tokens (~$0.001 per command)
- **Total**: ~$0.40/hour of continuous use

### Cost Optimization
```python
# Only enhance vague commands (saves 90% on GPT-4 costs)
if confidence < 0.5:
    command = voice._enhance_prompt(command)

# Use GPT-3.5-turbo instead of GPT-4 (10x cheaper)
# Edit enhanced_voice_processor.py, line 189:
# model="gpt-3.5-turbo"  # Instead of "gpt-4"
```

---

## 🐛 Troubleshooting

### "OpenAI API key not found"
```bash
# Set in .env file
echo "OPENAI_API_KEY=sk-your-key" > .env

# Or set environment variable
export OPENAI_API_KEY=sk-your-key  # Linux/Mac
set OPENAI_API_KEY=sk-your-key     # Windows
```

### "Microphone not detected"
```bash
# Install PyAudio
pip install pyaudio

# Linux: Install PortAudio
sudo apt-get install portaudio19-dev python3-pyaudio

# Mac: Install PortAudio
brew install portaudio
```

### "Speech recognition not working"
```python
# Test microphone
import speech_recognition as sr
r = sr.Recognizer()
with sr.Microphone() as source:
    print("Say something!")
    audio = r.listen(source)
    print(r.recognize_google(audio))
```

### "Whisper transcription slow"
```python
# Use local Whisper model (faster, free)
pip install openai-whisper

# Or use Google Speech Recognition (free, fast)
voice = EnhancedVoiceProcessor(use_whisper=False)
```

---

## 🎓 Next Steps

1. **Read the full guide**: `API_INTEGRATION_GUIDE.md`
2. **Explore examples**: `examples/voice_automation_example.py`
3. **Customize handlers**: `src/automation/handlers/`
4. **Add new commands**: `src/core/nlp_processor.py`

---

## 📚 Key Files

| File | Purpose |
|------|---------|
| `src/core/enhanced_voice_processor.py` | Enhanced voice processor with OpenAI |
| `API_INTEGRATION_GUIDE.md` | Complete API integration guide |
| `examples/voice_automation_example.py` | Usage examples and demos |
| `setup_enhanced_voice.py` | Automated setup script |

---

## 💡 Pro Tips

1. **Use wake word for hands-free operation**
   ```python
   voice.start_continuous_listening(use_wake_word=True)
   ```

2. **Combine with Selenium for web automation**
   ```python
   # Voice command triggers Selenium actions
   if "gmail" in command:
       driver.get("https://gmail.com")
   ```

3. **Cache common enhancements to save API costs**
   ```python
   cache = {
       "open email": "open Gmail in Chrome",
       "search python": "search Google for python tutorials"
   }
   ```

4. **Use async speech for better UX**
   ```python
   voice.speak("Processing...", async_speech=True)
   ```

---

## 🔗 Useful Links

- **OpenAI API**: https://platform.openai.com/
- **Whisper Docs**: https://platform.openai.com/docs/guides/speech-to-text
- **GPT-4 Docs**: https://platform.openai.com/docs/guides/gpt
- **Selenium Docs**: https://selenium-python.readthedocs.io/

---

## ✅ Checklist

- [ ] Install dependencies (`pip install openai python-dotenv`)
- [ ] Set OpenAI API key in `.env` file
- [ ] Test microphone access
- [ ] Run demo (`python examples/voice_automation_example.py`)
- [ ] Try vague commands to see auto-enhancement
- [ ] Integrate with your automation code
- [ ] Read full guide (`API_INTEGRATION_GUIDE.md`)

---

**Need help?** Check `API_INTEGRATION_GUIDE.md` for detailed documentation!

