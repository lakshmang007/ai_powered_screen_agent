# Visual Screen Analysis Feature

## Overview

Byte now has the ability to **analyze your screen**, **identify clickable components**, and **ask you which one to interact with**. This makes Byte much more intelligent and interactive!

## Features

### 1. **Screen Component Detection**
Byte can analyze your entire screen and identify:
- **Windows**: All visible application windows
- **Text Elements**: Using OCR (Optical Character Recognition)
- **Icons**: Desktop and taskbar icons
- **Clickable Areas**: Interactive elements

### 2. **Web Page Analysis**
When browsing the web, Byte can identify:
- **Links**: All clickable links on the page
- **Buttons**: Interactive buttons
- **Input Fields**: Text boxes, search bars, etc.
- **Forms**: Login forms, search forms, etc.

### 3. **Interactive Selection**
Byte will:
1. Analyze the screen/page
2. Identify all interactive elements
3. **Speak to you** listing the available options
4. **Ask which one you want to interact with**
5. Perform the action based on your response

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Byte Voice Command                       │
│              "Byte, what can I click here?"                  │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Visual Screen Handler                       │
│  • Captures screen using PyAutoGUI                          │
│  • Detects windows using pygetwindow                        │
│  • Performs OCR using Tesseract                             │
│  • Identifies clickable components                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Component Analysis                         │
│  • Groups components by type                                │
│  • Filters relevant elements                                │
│  • Ranks by importance                                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Voice Interaction                           │
│  Byte: "I can see 5 windows: Chrome, VS Code, Task          │
│         Manager, File Explorer, and Spotify. Which one      │
│         would you like me to open?"                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    User Response                             │
│              "Open Chrome"                                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Action Execution                           │
│  • Clicks on Chrome window                                  │
│  • Brings it to foreground                                  │
└─────────────────────────────────────────────────────────────┘
```

### For Web Pages (Selenium)

```
┌─────────────────────────────────────────────────────────────┐
│                     Byte Voice Command                       │
│              "Byte, analyze this page"                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Selenium Handler                            │
│  • Uses Selenium WebDriver                                  │
│  • Finds all <a> tags (links)                               │
│  • Finds all <button> tags                                  │
│  • Finds all <input> fields                                 │
│  • Extracts text and attributes                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Element Analysis                           │
│  • Groups by type (links, buttons, inputs)                  │
│  • Limits to most relevant (top 20)                         │
│  • Extracts meaningful text                                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Voice Interaction                           │
│  Byte: "I can see 15 links including Home, About,           │
│         Contact, 3 buttons including Search, Login,          │
│         and 2 input fields. What would you like me to do?"  │
└─────────────────────────────────────────────────────────────┘
```

## Usage Examples

### Example 1: Analyzing Desktop Screen

**You:** "Byte, what's on my screen?"

**Byte:** *Analyzes screen*

**Byte:** "I can see 5 windows on your screen: 1. Google Chrome - YouTube, 2. Visual Studio Code, 3. Task Manager, 4. File Explorer, 5. Spotify. Which one would you like me to open?"

**You:** "Open Chrome"

**Byte:** *Clicks on Chrome window* "Opened Google Chrome"

### Example 2: Analyzing Web Page

**You:** "Byte, open Google"

**Byte:** *Opens Google in browser*

**You:** "Byte, what can I click here?"

**Byte:** "I can see several elements on this page: 15 links including Gmail, Images, Sign in, 2 buttons including Google Search, I'm Feeling Lucky, and 1 input field. What would you like me to do?"

**You:** "Click on Images"

**Byte:** *Clicks on Images link* "Clicked on Images"

### Example 3: Interactive Search

**You:** "Byte, open YouTube"

**Byte:** *Opens YouTube*

**You:** "Byte, analyze the page"

**Byte:** "I can see 20 links including Home, Trending, Subscriptions, 5 buttons including Search, Upload, Notifications, and 1 input field for search. What would you like me to do?"

**You:** "Search for AI tutorials"

**Byte:** *Types in search box and searches* "Searched for AI tutorials"

## Voice Commands

### Screen Analysis Commands
- "Byte, what's on my screen?"
- "Byte, analyze the screen"
- "Byte, what can I click?"
- "Byte, show me what's available"
- "Byte, identify components"

### Web Page Analysis Commands
- "Byte, analyze this page"
- "Byte, what's on this page?"
- "Byte, show me the links"
- "Byte, what can I click here?"
- "Byte, identify elements"

### Interaction Commands
- "Byte, click on [element name]"
- "Byte, open [window name]"
- "Byte, search for [query]"
- "Byte, type [text]"

## Technical Details

### Dependencies

```python
# Screen Analysis
pyautogui          # Screen capture and mouse control
pygetwindow        # Window detection
pytesseract        # OCR for text detection
Pillow             # Image processing

# Web Analysis
selenium           # Web browser automation
webdriver-manager  # Automatic WebDriver management
```

### Installation

```bash
# Install Python dependencies
pip install pyautogui pygetwindow pytesseract Pillow selenium webdriver-manager

# Install Tesseract OCR (Windows)
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Install to: C:\Program Files\Tesseract-OCR\
```

### File Structure

```
src/
├── automation/
│   └── handlers/
│       ├── visual_screen_handler.py    # Screen analysis
│       └── selenium_handler.py         # Web page analysis (enhanced)
├── core/
│   ├── screen_agent.py                 # Screen capture
│   └── voice_processor.py              # Voice interaction
└── voice/
    └── voice_processor.py              # TTS/STT

examples/
└── visual_screen_demo.py               # Demo script

docs/
└── VISUAL_SCREEN_ANALYSIS.md          # This file
```

## Running the Demo

```bash
# Run the visual screen analysis demo
python examples/visual_screen_demo.py
```

The demo will:
1. Analyze your current desktop screen
2. Open Google and analyze the page
3. Open YouTube and demonstrate interactive selection

## API Reference

### VisualScreenHandler

```python
from src.automation.handlers.visual_screen_handler import VisualScreenHandler

handler = VisualScreenHandler(screen_agent, voice_processor)

# Analyze screen
result = handler.analyze_screen()
# Returns: {'status': 'completed', 'data': {'components': [...]}}

# Click on component
result = handler.click_component('Chrome')
# Returns: {'status': 'completed', 'message': 'Clicked on Chrome'}
```

### SeleniumHandler (Enhanced)

```python
from src.automation.handlers.selenium_handler import SeleniumHandler

handler = SeleniumHandler(voice_processor=voice_processor)

# Open website
handler.open_website({'url': 'https://www.google.com'})

# Analyze page
result = handler.analyze_page()
# Returns: {'status': 'completed', 'data': {'elements': [...]}}
```

## Future Enhancements

1. **Advanced Icon Detection**: Use computer vision to detect icons
2. **Context Awareness**: Remember previous interactions
3. **Smart Suggestions**: Suggest most likely actions
4. **Multi-Monitor Support**: Analyze multiple screens
5. **Accessibility Features**: Better support for screen readers
6. **Custom Element Training**: Learn new UI patterns

## Troubleshooting

### Issue: OCR not working
**Solution**: Install Tesseract OCR and set the path in `screen_agent.py`

### Issue: Window detection fails
**Solution**: Install pygetwindow: `pip install pygetwindow`

### Issue: Selenium can't find elements
**Solution**: Wait for page to load completely before analyzing

### Issue: Voice feedback not working
**Solution**: Check that voice_processor is initialized and TTS is working

## Contributing

To add new screen analysis features:
1. Add detection method to `VisualScreenHandler`
2. Update `_ask_user_to_select()` to include new element types
3. Add voice commands to NLP processor
4. Update this documentation

## License

Part of the AI-Powered Screen Agent project.

