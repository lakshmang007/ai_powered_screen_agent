# Visual Screen Analysis - Quick Start Guide

## 🎯 What's New?

Byte can now **see your screen** and **ask you what to click**! This makes Byte much smarter and more interactive.

## 🚀 Quick Demo

### 1. Install Dependencies

```bash
pip install pyautogui pygetwindow pytesseract Pillow selenium webdriver-manager
```

### 2. Run the Demo

```bash
python examples/visual_screen_demo.py
```

### 3. What You'll See

The demo will:
- ✅ Analyze your desktop and list all windows
- ✅ Open Google and identify clickable elements
- ✅ Open YouTube and demonstrate Byte asking what to do

## 💬 Example Conversation

**You:** "Byte, what's on my screen?"

**Byte:** "I can see 5 windows on your screen: 1. Google Chrome, 2. Visual Studio Code, 3. Task Manager, 4. File Explorer, 5. Spotify. Which one would you like me to open?"

**You:** "Open Chrome"

**Byte:** *Clicks on Chrome* "Opened Google Chrome"

---

**You:** "Byte, open Google"

**Byte:** *Opens Google*

**You:** "Byte, what can I click here?"

**Byte:** "I can see several elements on this page: 15 links including Gmail, Images, Sign in, 2 buttons including Google Search, I'm Feeling Lucky, and 1 input field. What would you like me to do?"

**You:** "Search for AI tutorials"

**Byte:** *Types and searches* "Searched for AI tutorials"

## 🎤 Voice Commands

### Screen Analysis
- "Byte, what's on my screen?"
- "Byte, analyze the screen"
- "Byte, what can I click?"

### Web Page Analysis
- "Byte, analyze this page"
- "Byte, what's on this page?"
- "Byte, show me the links"

### Actions
- "Byte, click on [element]"
- "Byte, open [window]"
- "Byte, search for [query]"

## 🔧 How It Works

1. **Screen Capture**: Byte takes a screenshot
2. **Component Detection**: Identifies windows, text, icons
3. **Voice Interaction**: Byte speaks the options
4. **User Selection**: You tell Byte what to do
5. **Action Execution**: Byte performs the action

## 📁 Key Files

- `src/automation/handlers/visual_screen_handler.py` - Screen analysis
- `src/automation/handlers/selenium_handler.py` - Web page analysis
- `examples/visual_screen_demo.py` - Demo script
- `docs/VISUAL_SCREEN_ANALYSIS.md` - Full documentation

## 🎨 Visual Flow

```
You: "Byte, what's on my screen?"
         ↓
    [Byte analyzes screen]
         ↓
    [Detects 5 windows]
         ↓
Byte: "I can see 5 windows: Chrome, VS Code, ..."
         ↓
You: "Open Chrome"
         ↓
    [Byte clicks Chrome]
         ↓
Byte: "Opened Chrome"
```

## 🌟 Features

### Desktop Screen Analysis
- ✅ Detects all visible windows
- ✅ Identifies window titles and positions
- ✅ OCR text detection
- ✅ Interactive selection

### Web Page Analysis
- ✅ Identifies all links
- ✅ Finds all buttons
- ✅ Detects input fields
- ✅ Interactive element selection

### Voice Interaction
- ✅ Byte speaks the available options
- ✅ Asks what you want to do
- ✅ Confirms actions
- ✅ Natural conversation flow

## 🎯 Use Cases

### 1. Desktop Navigation
"Byte, what windows are open?" → Byte lists all windows → "Open Spotify"

### 2. Web Browsing
"Byte, open YouTube" → "What can I click?" → Byte lists elements → "Search for music"

### 3. Form Filling
"Byte, analyze this form" → Byte identifies fields → "Fill in the email field"

### 4. Link Navigation
"Byte, show me the links" → Byte lists all links → "Click on About"

## 🔍 Technical Details

### Screen Analysis
```python
from src.automation.handlers.visual_screen_handler import VisualScreenHandler

handler = VisualScreenHandler(screen_agent, voice_processor)
result = handler.analyze_screen()

# Result contains:
# - components: List of detected windows/elements
# - screen_size: Screen dimensions
```

### Web Page Analysis
```python
from src.automation.handlers.selenium_handler import SeleniumHandler

handler = SeleniumHandler(voice_processor=voice_processor)
handler.open_website({'url': 'https://www.google.com'})
result = handler.analyze_page()

# Result contains:
# - elements: List of links, buttons, inputs
# - url: Current page URL
# - title: Page title
```

## 🐛 Troubleshooting

### OCR Not Working?
Install Tesseract OCR:
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- Install to: `C:\Program Files\Tesseract-OCR\`

### Window Detection Fails?
```bash
pip install pygetwindow
```

### Selenium Issues?
```bash
pip install selenium webdriver-manager
```

### Voice Not Working?
Check that `voice_processor` is initialized and TTS is enabled.

## 📚 Next Steps

1. **Try the demo**: `python examples/visual_screen_demo.py`
2. **Read full docs**: `docs/VISUAL_SCREEN_ANALYSIS.md`
3. **Integrate with Byte**: Add to main voice command loop
4. **Customize**: Add your own element detection logic

## 🎉 Example Output

```
==============================================================
Visual Screen Analysis Demo
==============================================================

1. Analyzing current screen...
--------------------------------------------------------------
✓ Found 8 components on screen

Detected Components:
  1. [WINDOW] Google Chrome - YouTube
     Position: (0, 0)
  2. [WINDOW] Visual Studio Code
     Position: (800, 0)
  3. [WINDOW] Task Manager
     Position: (100, 100)
  4. [TEXT] AI-Powered Screen Agent
     Position: (50, 30)
  5. [TEXT] Byte
     Position: (200, 50)
  ... and 3 more

==============================================================
```

## 🚀 Integration Example

```python
# In your main Byte loop
if "what's on my screen" in command:
    visual_handler = VisualScreenHandler(screen_agent, voice_processor)
    result = visual_handler.analyze_screen()
    # Byte will automatically speak the options!

elif "analyze this page" in command:
    selenium_handler = SeleniumHandler(voice_processor=voice_processor)
    result = selenium_handler.analyze_page()
    # Byte will list all clickable elements!
```

## 🎊 That's It!

You now have a **visual screen analysis system** that makes Byte much more intelligent and interactive!

**Try it now:**
```bash
python examples/visual_screen_demo.py
```

For more details, see `docs/VISUAL_SCREEN_ANALYSIS.md`

