# Visual Screen Analysis - System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                             │
│                                                                      │
│  User: "Byte, what's on my screen?"                                 │
│  User: "Byte, analyze this page"                                    │
│  User: "Byte, what can I click here?"                               │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      VOICE PROCESSOR                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Speech-to-Text (STT)                                         │  │
│  │ • Captures voice command                                     │  │
│  │ • Converts to text                                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       NLP PROCESSOR                                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Command Parsing                                              │  │
│  │ • Identifies action: "analyze", "identify", "click"          │  │
│  │ • Extracts parameters                                        │  │
│  │ • Routes to appropriate handler                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
┌───────────────────────────┐  ┌──────────────────────────┐
│  VISUAL SCREEN HANDLER    │  │   SELENIUM HANDLER       │
│  (Desktop Analysis)       │  │   (Web Page Analysis)    │
└───────────┬───────────────┘  └──────────┬───────────────┘
            │                              │
            ▼                              ▼
┌───────────────────────────┐  ┌──────────────────────────┐
│  SCREEN CAPTURE           │  │  WEB DRIVER              │
│  • PyAutoGUI              │  │  • Selenium WebDriver    │
│  • MSS (screenshot)       │  │  • Chrome/Firefox        │
│  • PIL (image processing) │  │  • Page DOM access       │
└───────────┬───────────────┘  └──────────┬───────────────┘
            │                              │
            ▼                              ▼
┌───────────────────────────┐  ┌──────────────────────────┐
│  COMPONENT DETECTION      │  │  ELEMENT DETECTION       │
│  ┌─────────────────────┐  │  │  ┌────────────────────┐  │
│  │ Window Detection    │  │  │  │ Link Detection     │  │
│  │ • pygetwindow       │  │  │  │ • <a> tags         │  │
│  │ • Window titles     │  │  │  │ • href attributes  │  │
│  │ • Positions/sizes   │  │  │  └────────────────────┘  │
│  └─────────────────────┘  │  │  ┌────────────────────┐  │
│  ┌─────────────────────┐  │  │  │ Button Detection   │  │
│  │ OCR Text Detection  │  │  │  │ • <button> tags    │  │
│  │ • Tesseract OCR     │  │  │  │ • Text content     │  │
│  │ • Text extraction   │  │  │  └────────────────────┘  │
│  │ • Confidence scores │  │  │  ┌────────────────────┐  │
│  └─────────────────────┘  │  │  │ Input Detection    │  │
│  ┌─────────────────────┐  │  │  │ • <input> fields   │  │
│  │ Icon Detection      │  │  │  │ • Placeholders     │  │
│  │ • Color analysis    │  │  │  │ • Field types      │  │
│  │ • Shape detection   │  │  │  └────────────────────┘  │
│  └─────────────────────┘  │  └──────────────────────────┘
└───────────┬───────────────┘              │
            │                              │
            └────────────┬─────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPONENT ANALYSIS                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Filtering & Ranking                                          │  │
│  │ • Remove duplicates                                          │  │
│  │ • Filter by visibility                                       │  │
│  │ • Rank by importance                                         │  │
│  │ • Group by type                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Data Structuring                                             │  │
│  │ • Component type (window/link/button/input)                  │  │
│  │ • Text/title                                                 │  │
│  │ • Position/size                                              │  │
│  │ • Clickability                                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    VOICE INTERACTION                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Message Generation                                           │  │
│  │ • Build natural language description                         │  │
│  │ • List top components                                        │  │
│  │ • Ask clarifying question                                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Text-to-Speech (TTS)                                         │  │
│  │ Byte: "I can see 5 windows: Chrome, VS Code, Task Manager,   │  │
│  │       File Explorer, and Spotify. Which one would you like   │  │
│  │       me to open?"                                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      USER RESPONSE                                   │
│  User: "Open Chrome"                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ACTION EXECUTION                                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Component Matching                                           │  │
│  │ • Find component matching user's response                    │  │
│  │ • Extract position/coordinates                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Action Execution                                             │  │
│  │ • Click on component (PyAutoGUI)                             │  │
│  │ • Or navigate to link (Selenium)                             │  │
│  │ • Or type in input field                                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Confirmation                                                 │  │
│  │ Byte: "Opened Chrome"                                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Flow Diagram

```
Desktop Screen Analysis:
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Capture  │───▶│  Detect  │───▶│  Filter  │───▶│  Speak   │
│ Screen   │    │ Windows  │    │  & Rank  │    │ Options  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                     │
                     ├──────────┐
                     │          │
                ┌────▼────┐ ┌──▼──────┐
                │   OCR   │ │  Icons  │
                │  Text   │ │Detection│
                └─────────┘ └─────────┘

Web Page Analysis:
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Open    │───▶│  Parse   │───▶│  Group   │───▶│  Speak   │
│  Page    │    │   DOM    │    │Elements  │    │ Options  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                     │
                     ├──────────┬──────────┐
                     │          │          │
                ┌────▼────┐ ┌──▼──────┐ ┌─▼──────┐
                │  Links  │ │ Buttons │ │ Inputs │
                │  <a>    │ │<button> │ │<input> │
                └─────────┘ └─────────┘ └────────┘
```

## Data Flow

```
Input Command
     │
     ▼
┌─────────────────────────────────────┐
│ "Byte, what's on my screen?"        │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ ParsedCommand                       │
│ • action: "analyze"                 │
│ • target: "screen"                  │
│ • parameters: {}                    │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ VisualScreenHandler.analyze_screen()│
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ Components List                     │
│ [                                   │
│   {                                 │
│     'type': 'window',               │
│     'title': 'Google Chrome',       │
│     'position': (0, 0),             │
│     'size': (1920, 1080),           │
│     'clickable': True               │
│   },                                │
│   {                                 │
│     'type': 'window',               │
│     'title': 'VS Code',             │
│     'position': (800, 0),           │
│     'size': (1120, 1080),           │
│     'clickable': True               │
│   },                                │
│   ...                               │
│ ]                                   │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ Voice Message Generation            │
│ "I can see 5 windows: Chrome,       │
│  VS Code, Task Manager, File        │
│  Explorer, and Spotify. Which one   │
│  would you like me to open?"        │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ TTS Output (Byte speaks)            │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ User Response: "Open Chrome"        │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ Component Matching                  │
│ • Find component with title         │
│   containing "Chrome"               │
│ • Extract position: (0, 0)          │
│ • Extract size: (1920, 1080)        │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ Click Execution                     │
│ • Calculate center: (960, 540)      │
│ • pyautogui.click(960, 540)         │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ Confirmation                        │
│ Byte: "Opened Chrome"               │
└─────────────────────────────────────┘
```

## Class Diagram

```
┌─────────────────────────────────────┐
│      VisualScreenHandler            │
├─────────────────────────────────────┤
│ - screen_agent: ScreenAgent         │
│ - voice_processor: VoiceProcessor   │
│ - logger: Logger                    │
├─────────────────────────────────────┤
│ + analyze_screen() → Dict           │
│ + identify_components() → Dict      │
│ + click_component(target) → Dict    │
│ - _detect_windows() → List          │
│ - _detect_text_elements() → List    │
│ - _detect_icons() → List            │
│ - _ask_user_to_select() → None      │
└─────────────────────────────────────┘
              │
              │ uses
              ▼
┌─────────────────────────────────────┐
│         ScreenAgent                 │
├─────────────────────────────────────┤
│ - screen_monitor: mss               │
│ - confidence_threshold: float       │
├─────────────────────────────────────┤
│ + capture_screen() → ndarray        │
│ + find_element_by_image() → Tuple   │
│ + find_text_on_screen() → List      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│       SeleniumHandler               │
├─────────────────────────────────────┤
│ - driver: WebDriver                 │
│ - voice_processor: VoiceProcessor   │
│ - wait_timeout: int                 │
├─────────────────────────────────────┤
│ + analyze_page() → Dict             │
│ + identify_elements() → Dict        │
│ + click_element(selector) → Dict    │
│ + open_website(params) → Dict       │
│ - _ask_user_to_select() → None      │
└─────────────────────────────────────┘
              │
              │ uses
              ▼
┌─────────────────────────────────────┐
│       VoiceProcessor                │
├─────────────────────────────────────┤
│ - engine: pyttsx3.Engine            │
│ - recognizer: sr.Recognizer         │
├─────────────────────────────────────┤
│ + speak(text) → None                │
│ + listen() → str                    │
└─────────────────────────────────────┘
```

## Sequence Diagram

```
User          Voice         NLP        Visual        Screen      Voice
             Processor    Processor   Handler       Agent       Output
  │              │            │           │            │           │
  │─"What's on──▶│            │           │            │           │
  │ my screen?"  │            │           │            │           │
  │              │            │           │            │           │
  │              │─Parse─────▶│           │            │           │
  │              │            │           │            │           │
  │              │            │─Analyze──▶│            │           │
  │              │            │           │            │           │
  │              │            │           │─Capture───▶│           │
  │              │            │           │            │           │
  │              │            │           │◀─Screenshot│           │
  │              │            │           │            │           │
  │              │            │           │─Detect─────▶           │
  │              │            │           │  Windows   │           │
  │              │            │           │            │           │
  │              │            │           │─OCR Text───▶           │
  │              │            │           │            │           │
  │              │            │           │◀─Components│           │
  │              │            │           │            │           │
  │              │            │◀─Result───│            │           │
  │              │            │           │            │           │
  │              │◀─Response──│           │            │           │
  │              │            │           │            │           │
  │              │─────────────────────────────────────▶Speak──────▶│
  │              │  "I can see 5 windows..."           │           │
  │              │            │           │            │           │
  │◀─────────────────────────────────────────────────────────Byte  │
  │  Hears Byte speaking                               │  speaks  │
  │              │            │           │            │           │
  │─"Open Chrome"▶           │           │            │           │
  │              │            │           │            │           │
  │              │─Parse─────▶│           │            │           │
  │              │            │           │            │           │
  │              │            │─Click─────▶            │           │
  │              │            │  Chrome   │            │           │
  │              │            │           │            │           │
  │              │            │           │─Click──────▶           │
  │              │            │           │  (960,540) │           │
  │              │            │           │            │           │
  │              │            │◀─Success───            │           │
  │              │            │           │            │           │
  │              │◀─Response──│           │            │           │
  │              │            │           │            │           │
  │              │─────────────────────────────────────▶Speak──────▶│
  │              │  "Opened Chrome"                    │           │
  │              │            │           │            │           │
  │◀─────────────────────────────────────────────────────────Byte  │
  │  Chrome window opens                               │  speaks  │
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  • Voice Commands                                           │
│  • Natural Language Processing                              │
│  • User Interaction                                         │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    Handler Layer                             │
│  • VisualScreenHandler                                      │
│  • SeleniumHandler                                          │
│  • Other automation handlers                                │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    Core Layer                                │
│  • ScreenAgent (screen capture)                             │
│  • VoiceProcessor (TTS/STT)                                 │
│  • NLPProcessor (command parsing)                           │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    Library Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PyAutoGUI   │  │   Selenium   │  │  Tesseract   │      │
│  │  (GUI auto)  │  │  (Web auto)  │  │    (OCR)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ pygetwindow  │  │     MSS      │  │    pyttsx3   │      │
│  │(Window mgmt) │  │(Screenshot)  │  │    (TTS)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    Operating System                          │
│  • Windows API                                              │
│  • Screen capture                                           │
│  • Mouse/keyboard control                                   │
└─────────────────────────────────────────────────────────────┘
```

