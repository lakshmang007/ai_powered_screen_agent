# API Integration Guide for Voice-Powered Automation

This guide explains how to integrate powerful APIs to make your screen agent automatic, efficient, and work seamlessly with Selenium for voice-based automation.

## 🎯 Recommended APIs

### 1. **OpenAI API** (Primary Recommendation)
**Best for**: Voice recognition (Whisper) + Prompt Enhancement (GPT-4)

#### Features:
- **Whisper**: State-of-the-art speech-to-text
  - 99% accuracy in multiple languages
  - Automatic punctuation and capitalization
  - Works with background noise
  
- **GPT-4**: Intelligent prompt enhancement
  - Converts vague commands → specific instructions
  - Example: "open that thing" → "open Google Chrome and navigate to Gmail"
  - Context-aware understanding

#### Setup:
```bash
pip install openai
```

```python
# Set environment variable
export OPENAI_API_KEY="sk-your-api-key-here"

# Or in code
import openai
openai.api_key = "sk-your-api-key-here"
```

#### Pricing:
- Whisper: $0.006 per minute (~$0.36/hour)
- GPT-4: $0.03 per 1K tokens (~$0.001 per command)
- **Total**: ~$0.40/hour of continuous use

---

### 2. **AssemblyAI** (Alternative for Real-time)
**Best for**: Real-time voice transcription with advanced features

#### Features:
- Real-time streaming transcription
- Automatic punctuation
- Speaker diarization (multiple speakers)
- Entity detection (names, dates, etc.)
- Sentiment analysis
- Custom vocabulary

#### Setup:
```bash
pip install assemblyai
```

```python
import assemblyai as aai
aai.settings.api_key = "your-api-key"

# Real-time transcription
transcriber = aai.RealtimeTranscriber(
    on_data=lambda transcript: print(transcript.text)
)
transcriber.connect()
```

#### Pricing:
- Real-time: $0.015 per minute (~$0.90/hour)
- Async: $0.00025 per second (~$0.90/hour)

---

### 3. **ElevenLabs** (For Better Text-to-Speech)
**Best for**: Natural-sounding voice responses

#### Features:
- Ultra-realistic voices
- Multiple voice options
- Emotional tone control
- Low latency

#### Setup:
```bash
pip install elevenlabs
```

```python
from elevenlabs import generate, play, set_api_key

set_api_key("your-api-key")
audio = generate(text="Command completed successfully", voice="Bella")
play(audio)
```

#### Pricing:
- Free tier: 10,000 characters/month
- Paid: $5/month for 30,000 characters

---

### 4. **Anthropic Claude API** (Alternative to GPT-4)
**Best for**: Complex reasoning and prompt enhancement

#### Features:
- Excellent at understanding context
- Better for multi-step automation
- Longer context window (100K tokens)
- More reliable for complex tasks

#### Setup:
```bash
pip install anthropic
```

```python
import anthropic

client = anthropic.Anthropic(api_key="your-api-key")
message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Enhance this command: open that email thing"}
    ]
)
```

#### Pricing:
- Claude 3 Opus: $15 per 1M input tokens
- Claude 3 Sonnet: $3 per 1M input tokens

---

## 🚀 Integration Architecture

### Complete Flow:
```
Voice Input → Whisper (Transcription) → GPT-4 (Enhancement) → 
NLP Processor → Task Engine → Selenium/PyAutoGUI → Action Execution
```

### Example Integration:

```python
from src.core.enhanced_voice_processor import EnhancedVoiceProcessor
from src.core.nlp_processor import NLPProcessor
from src.automation.task_engine import TaskEngine

# Initialize with OpenAI
voice_processor = EnhancedVoiceProcessor(
    openai_api_key="sk-your-key",
    use_whisper=True,
    use_gpt_enhancement=True,
    wake_word="computer"
)

nlp_processor = NLPProcessor()
task_engine = TaskEngine()

# Continuous listening with automatic enhancement
def handle_command(text):
    # Text is already enhanced by GPT-4
    parsed = nlp_processor.parse_command(text)
    result = task_engine.execute_command(parsed)
    
    if result.status == "completed":
        voice_processor.speak("Done!", async_speech=True)

# Start listening
voice_processor.start_continuous_listening(
    callback=handle_command,
    use_wake_word=True,
    enhance_prompts=True
)
```

---

## 🔧 Selenium Integration

The enhanced voice processor works seamlessly with Selenium:

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

class SeleniumVoiceAutomation:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.voice = EnhancedVoiceProcessor(use_gpt_enhancement=True)
    
    def execute_voice_command(self):
        # Listen for command
        command = self.voice.listen_once(enhance_prompt=True)
        
        # Example: "send email to john@example.com"
        if "send email" in command.lower():
            email = self._extract_email(command)
            self._send_email_via_selenium(email)
    
    def _send_email_via_selenium(self, to_email):
        self.driver.get("https://gmail.com")
        # ... Selenium automation code
        self.voice.speak("Email sent successfully")
```

---

## 📊 Comparison Table

| API | Voice Recognition | Prompt Enhancement | Real-time | Price/Hour | Best For |
|-----|------------------|-------------------|-----------|------------|----------|
| **OpenAI** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | $0.40 | General use, best accuracy |
| **AssemblyAI** | ⭐⭐⭐⭐ | ❌ | ✅ | $0.90 | Real-time streaming |
| **Google Speech** | ⭐⭐⭐ | ❌ | ✅ | Free | Budget option |
| **Claude** | ❌ | ⭐⭐⭐⭐⭐ | ❌ | $0.003 | Complex reasoning |

---

## 🎯 Recommended Setup for Your Use Case

Based on your requirements (automatic, efficient, works with Selenium):

### **Option 1: Best Quality (Recommended)**
```bash
pip install openai elevenlabs
```

- **Voice Input**: OpenAI Whisper
- **Prompt Enhancement**: GPT-4
- **Voice Output**: ElevenLabs
- **Cost**: ~$0.50/hour

### **Option 2: Budget-Friendly**
```bash
pip install speech_recognition pyttsx3
```

- **Voice Input**: Google Speech Recognition (free)
- **Prompt Enhancement**: GPT-4 (only when needed)
- **Voice Output**: pyttsx3 (free)
- **Cost**: ~$0.10/hour

### **Option 3: Real-time Streaming**
```bash
pip install assemblyai openai elevenlabs
```

- **Voice Input**: AssemblyAI (real-time)
- **Prompt Enhancement**: GPT-4
- **Voice Output**: ElevenLabs
- **Cost**: ~$1.00/hour

---

## 🔐 Environment Setup

Create a `.env` file:
```bash
# OpenAI (for Whisper + GPT-4)
OPENAI_API_KEY=sk-your-key-here

# AssemblyAI (optional)
ASSEMBLYAI_API_KEY=your-key-here

# ElevenLabs (optional)
ELEVENLABS_API_KEY=your-key-here

# Anthropic Claude (optional)
ANTHROPIC_API_KEY=your-key-here
```

Load in your code:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 📝 Usage Examples

### Example 1: Simple Voice Command
```python
voice = EnhancedVoiceProcessor()

# User says: "open that email thing"
command = voice.listen_once(enhance_prompt=True)
# Returns: "open Gmail in Chrome browser"
```

### Example 2: Continuous Listening
```python
def on_command(text):
    print(f"Executing: {text}")
    # Your automation code here

voice.start_continuous_listening(
    callback=on_command,
    use_wake_word=True,  # Say "computer" first
    enhance_prompts=True  # Auto-enhance vague commands
)
```

### Example 3: Selenium Integration
```python
# User says: "search for python tutorials"
# Enhanced to: "open Chrome and search Google for python tutorials"

driver = webdriver.Chrome()
driver.get("https://google.com")
search_box = driver.find_element(By.NAME, "q")
search_box.send_keys("python tutorials")
search_box.submit()
```

---

## 🎓 Next Steps

1. **Install dependencies**:
   ```bash
   pip install openai elevenlabs python-dotenv
   ```

2. **Get API keys**:
   - OpenAI: https://platform.openai.com/api-keys
   - ElevenLabs: https://elevenlabs.io/
   - AssemblyAI: https://www.assemblyai.com/

3. **Update your code**:
   - Replace `VoiceProcessor` with `EnhancedVoiceProcessor`
   - Add API keys to `.env` file
   - Test with simple commands

4. **Test the integration**:
   ```bash
   python main.py --cli
   ```

---

## 💡 Pro Tips

1. **Use GPT-4 for enhancement only when confidence is low**
   - Saves API costs
   - Faster for clear commands

2. **Cache common command enhancements**
   - Store frequently used patterns
   - Reduce API calls

3. **Combine with local models**
   - Use Whisper locally (free) via `whisper` package
   - Only use API for enhancement

4. **Implement retry logic**
   - Handle API failures gracefully
   - Fallback to Google Speech Recognition

---

## 🐛 Troubleshooting

### Issue: "OpenAI API key not found"
**Solution**: Set environment variable or pass to constructor

### Issue: "Whisper transcription slow"
**Solution**: Use local Whisper model or AssemblyAI for real-time

### Issue: "GPT-4 enhancement too expensive"
**Solution**: Use GPT-3.5-turbo or only enhance low-confidence commands

---

## 📚 Additional Resources

- [OpenAI Whisper Docs](https://platform.openai.com/docs/guides/speech-to-text)
- [GPT-4 API Reference](https://platform.openai.com/docs/api-reference/chat)
- [AssemblyAI Real-time](https://www.assemblyai.com/docs/walkthroughs#realtime-streaming-transcription)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)

