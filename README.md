# AI-Powered Screen Agent
start from .
An intelligent automation tool that takes text or voice commands and performs automated tasks by interacting with your screen and applications.

## Features

- **Voice & Text Input**: Accept commands through both voice recognition and text input
- **Screen Interaction**: Automatically interact with any application on your screen
- **Smart Task Understanding**: Uses NLP to understand and execute complex multi-step tasks
- **Application-Specific Handlers**: Specialized handlers for popular applications like VSCode, Gmail, LinkedIn
- **Visual Element Detection**: Advanced computer vision to identify and interact with UI elements

## Example Use Cases

1. **File Management**: "Create a new folder named 'auto_work' in VSCode"
2. **Email Automation**: "Send reply email to john@gmail.com"
3. **Social Media**: "Post this image to my LinkedIn account with an interesting caption"
4. **Development Tasks**: "Open terminal and run npm install"

## Installation

1. Clone the repository:
```bash
git clone https://github.com/lakshmang007/ai_powered_screen_agent.git
cd ai_powered_screen_agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install additional requirements:
   - Install Tesseract OCR for text recognition
   - Download spaCy language model: `python -m spacy download en_core_web_sm`

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

AI parsing is optional. With `GEMINI_API_KEY` or `GROQ_API_KEY` set, the matching provider is
picked automatically (override with `AI_PROVIDER`). Without a key, the built-in regex parser is used.

## Usage

Run the main application:
```bash
python main.py            # GUI
python main.py --cli      # text commands in the terminal
python main.py --voice    # JARVIS voice mode (say "JARVIS")
```

Run the tests (no network, microphone or screen access needed):
```bash
python -m pytest tests
```

Example commands: `open notepad and type Hello World`, `go to github.com`,
`search for python tutorials on youtube`, `select all`, `erase that and type hi`,
`press enter`, `minimize all windows`, `play macro todo`.
Shutting down the computer always asks for a spoken "yes" first.

## Project Structure

```
ai_powered_screen_agent/
├── src/
│   ├── core/
│   │   ├── screen_agent.py      # Main screen interaction logic
│   │   ├── voice_processor.py   # Voice input processing
│   │   └── nlp_processor.py     # Natural language understanding
│   ├── automation/
│   │   ├── task_engine.py       # Core automation engine
│   │   └── handlers/            # Application-specific handlers
│   ├── gui/
│   │   └── main_window.py       # Main GUI interface
│   └── utils/
│       └── helpers.py           # Utility functions
├── tests/
├── config/
├── main.py
└── requirements.txt
```

## License

MIT License
