# Installation Guide

This guide will help you install and set up the AI-Powered Screen Agent on your system.

## Prerequisites

- Python 3.7 or higher
- Windows 10/11 (primary support), macOS, or Linux
- At least 4GB RAM
- Internet connection for initial setup

## Step 1: Clone the Repository

```bash
git clone https://github.com/lakshmang007/ai_powered_screen_agent.git
cd ai_powered_screen_agent
```

## Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

## Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Install System Dependencies

### Windows

1. **Install Tesseract OCR**:
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Install to default location: `C:\Program Files\Tesseract-OCR\`
   - Add to PATH if not automatically added

2. **Install Chrome/Chromium** (for web automation):
   - Download from: https://www.google.com/chrome/

### macOS

```bash
# Install Tesseract using Homebrew
brew install tesseract

# Install Chrome if not already installed
# Download from: https://www.google.com/chrome/
```

### Linux (Ubuntu/Debian)

```bash
# Install Tesseract
sudo apt-get update
sudo apt-get install tesseract-ocr

# Install Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update
sudo apt-get install google-chrome-stable
```

## Step 5: Install spaCy Language Model

```bash
python -m spacy download en_core_web_sm
```

## Step 6: Configure Audio (for Voice Input)

### Windows
- Ensure microphone is connected and working
- Check Windows Sound settings

### macOS
- Grant microphone permissions when prompted
- Check System Preferences > Security & Privacy > Microphone

### Linux
```bash
# Install additional audio dependencies
sudo apt-get install portaudio19-dev python3-pyaudio
```

## Step 7: Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` file with your API keys (optional):
```
# OpenAI API Key (for advanced NLP processing)
OPENAI_API_KEY=your_openai_api_key_here

# Google Gemini API Key (alternative to OpenAI)
GOOGLE_API_KEY=your_google_api_key_here
```

## Step 8: Test Installation

Run the test suite to verify everything is working:

```bash
python tests/run_tests.py
```

## Step 9: Run the Application

### GUI Mode (Default)
```bash
python main.py
```

### CLI Mode
```bash
python main.py --cli
```

## Troubleshooting

### Common Issues

1. **"No module named 'cv2'"**
   ```bash
   pip install opencv-python
   ```

2. **"Tesseract not found"**
   - Ensure Tesseract is installed and in PATH
   - On Windows, check if installed in `C:\Program Files\Tesseract-OCR\`

3. **"PyAudio installation failed"**
   - Windows: Install Microsoft Visual C++ Build Tools
   - macOS: `brew install portaudio`
   - Linux: `sudo apt-get install portaudio19-dev`

4. **"Permission denied" for microphone**
   - Grant microphone permissions in system settings
   - Restart the application after granting permissions

5. **Chrome driver issues**
   - The application automatically downloads ChromeDriver
   - Ensure Chrome/Chromium is installed and up to date

### Performance Issues

1. **Slow OCR performance**
   - OCR can be CPU-intensive
   - Consider using a dedicated GPU if available
   - Reduce screenshot frequency in settings

2. **High memory usage**
   - Close unused browser tabs/windows
   - Restart the application periodically for long sessions

### Voice Recognition Issues

1. **Voice not recognized**
   - Check microphone settings
   - Speak clearly and at normal volume
   - Ensure quiet environment
   - Try adjusting energy threshold in settings

2. **Wrong language detected**
   - Currently supports English only
   - Ensure clear pronunciation

## Advanced Configuration

### Custom Configuration File

Create `config/config.ini`:

```ini
[screen_agent]
screenshot_interval = 0.5
confidence_threshold = 0.8
max_retries = 3

[voice]
timeout = 5
phrase_timeout = 1.0
energy_threshold = 300

[logging]
level = INFO
file = logs/screen_agent.log
```

### Environment Variables

You can also use environment variables:

```bash
export SCREENSHOT_INTERVAL=0.5
export CONFIDENCE_THRESHOLD=0.8
export VOICE_TIMEOUT=5
export LOG_LEVEL=INFO
```

## Security Considerations

1. **API Keys**: Keep your API keys secure and never commit them to version control
2. **Screen Access**: The application requires screen capture permissions
3. **Microphone Access**: Grant microphone access only when needed
4. **Web Automation**: Be cautious with automated web interactions

## Getting Help

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the logs in `logs/screen_agent.log`
3. Run tests to identify specific issues
4. Create an issue on GitHub with detailed error information

## Next Steps

After successful installation:

1. Read the [User Guide](USER_GUIDE.md) for usage instructions
2. Check out [Examples](EXAMPLES.md) for common use cases
3. Review [API Documentation](API.md) for advanced usage
