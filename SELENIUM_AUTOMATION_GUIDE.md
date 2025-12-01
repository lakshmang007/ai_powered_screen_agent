# 🤖 Selenium Automation with Byte

## Yes! Selenium Can Be Used for Automation Tasks

Selenium is **already integrated** into your project and is perfect for web automation tasks!

---

## ✅ What Selenium Can Do

### 1. **Web Browser Automation**
- Open websites
- Click buttons
- Fill forms
- Navigate pages
- Extract data
- Take screenshots

### 2. **Already Integrated in Your Project**
Your project already has Selenium handlers:
- `src/automation/handlers/browser_handler.py`
- `src/automation/handlers/gmail_handler.py`
- `src/automation/handlers/linkedin_handler.py`

### 3. **Works with Byte**
Byte can control Selenium automation through voice commands!

---

## 🎯 How Selenium is Used in Your Project

### Current Selenium Handlers

#### 1. **BrowserHandler** (`src/automation/handlers/browser_handler.py`)
```python
# Opens websites
# Navigates to URLs
# Searches Google
# Controls browser
```

#### 2. **GmailHandler** (`src/automation/handlers/gmail_handler.py`)
```python
# Opens Gmail
# Composes emails
# Reads emails
# Sends emails
```

#### 3. **LinkedInHandler** (`src/automation/handlers/linkedin_handler.py`)
```python
# Opens LinkedIn
# Views profiles
# Sends messages
# Posts updates
```

---

## 🚀 Using Selenium with Byte

### Example 1: Open Website

**You:** "Byte, open GitHub"

**Byte:** "Got it!"
- Checks if GitHub app is installed
- If not, asks: "Should I open it in a browser?"
- Uses Selenium to open GitHub in browser

### Example 2: Search Google

**You:** "Byte, search for Python tutorials"

**Byte:** "On it!"
- Uses Selenium to open Chrome
- Navigates to Google
- Performs search

### Example 3: Open Gmail

**You:** "Byte, open Gmail"

**Byte:** "Working on it!"
- Uses GmailHandler (Selenium-based)
- Opens Gmail in browser
- Logs in if needed

---

## 💻 Selenium Code Examples

### Example 1: Basic Web Automation

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Initialize driver
driver = webdriver.Chrome()

# Open website
driver.get("https://www.google.com")

# Find search box
search_box = driver.find_element(By.NAME, "q")

# Type and search
search_box.send_keys("Python tutorials")
search_box.send_keys(Keys.RETURN)

# Wait and close
time.sleep(5)
driver.quit()
```

### Example 2: Fill Form

```python
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://example.com/form")

# Fill form fields
driver.find_element(By.ID, "name").send_keys("John Doe")
driver.find_element(By.ID, "email").send_keys("john@example.com")

# Click submit
driver.find_element(By.ID, "submit").click()

driver.quit()
```

### Example 3: Extract Data

```python
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://example.com")

# Extract text
title = driver.find_element(By.TAG_NAME, "h1").text
print(f"Title: {title}")

# Extract multiple elements
links = driver.find_elements(By.TAG_NAME, "a")
for link in links:
    print(link.get_attribute("href"))

driver.quit()
```

---

## 🎤 Voice Commands for Selenium Automation

### Current Voice Commands (Already Working)

**Browser Commands:**
- "Open Chrome"
- "Open Firefox"
- "Open Edge"
- "Navigate to [URL]"

**Search Commands:**
- "Search for [query]"
- "Google [query]"

**Website Commands:**
- "Open Gmail"
- "Open LinkedIn"
- "Open GitHub"
- "Open YouTube"

---

## 🔧 Adding Custom Selenium Automation

### Step 1: Create Custom Handler

Create a new file: `src/automation/handlers/custom_handler.py`

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

class CustomHandler:
    def __init__(self, screen_agent):
        self.screen_agent = screen_agent
        self.driver = None
    
    def handle_command(self, command):
        """Handle custom automation command."""
        action = command.action
        params = command.parameters
        
        if action == "fill_form":
            return self.fill_form(params)
        elif action == "extract_data":
            return self.extract_data(params)
        
        return {"status": "error", "message": "Unknown action"}
    
    def fill_form(self, params):
        """Fill a web form."""
        try:
            self.driver = webdriver.Chrome()
            self.driver.get(params.get("url"))
            
            # Fill fields
            for field_id, value in params.get("fields", {}).items():
                element = self.driver.find_element(By.ID, field_id)
                element.send_keys(value)
            
            # Submit
            submit_btn = self.driver.find_element(By.ID, "submit")
            submit_btn.click()
            
            time.sleep(2)
            self.driver.quit()
            
            return {"status": "success", "message": "Form filled!"}
        except Exception as e:
            if self.driver:
                self.driver.quit()
            return {"status": "error", "message": str(e)}
    
    def extract_data(self, params):
        """Extract data from website."""
        try:
            self.driver = webdriver.Chrome()
            self.driver.get(params.get("url"))
            
            # Extract data
            selector = params.get("selector")
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            
            data = [elem.text for elem in elements]
            
            self.driver.quit()
            
            return {"status": "success", "data": data}
        except Exception as e:
            if self.driver:
                self.driver.quit()
            return {"status": "error", "message": str(e)}
```

### Step 2: Register Handler in Byte

In `byte_conversational.py`, add:

```python
from src.automation.handlers.custom_handler import CustomHandler

# In init_components():
custom_handler = CustomHandler(self.screen_agent)
self.engine.register_app_handler(ApplicationType.CUSTOM, custom_handler.handle_command)
```

### Step 3: Use with Voice Commands

**You:** "Byte, fill the registration form"

**Byte:** "Got it!"
- Uses CustomHandler
- Opens browser
- Fills form
- Submits

---

## 🎯 Advanced Selenium Features

### 1. **Headless Mode** (No visible browser)
```python
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)
```

### 2. **Wait for Elements**
```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

wait = WebDriverWait(driver, 10)
element = wait.until(EC.presence_of_element_located((By.ID, "myElement")))
```

### 3. **Handle Alerts**
```python
alert = driver.switch_to.alert
alert.accept()  # Click OK
# or
alert.dismiss()  # Click Cancel
```

### 4. **Switch Tabs**
```python
# Open new tab
driver.execute_script("window.open('');")
driver.switch_to.window(driver.window_handles[1])

# Switch back
driver.switch_to.window(driver.window_handles[0])
```

### 5. **Take Screenshots**
```python
driver.save_screenshot("screenshot.png")
```

---

## 📊 Selenium vs Other Automation

| Feature | Selenium | PyAutoGUI | Advantages |
|---------|----------|-----------|------------|
| **Web Automation** | ✅ Best | ❌ Limited | Selenium is designed for web |
| **Desktop Apps** | ❌ No | ✅ Yes | PyAutoGUI for desktop |
| **Speed** | ✅ Fast | ⚠️ Slower | Selenium is faster |
| **Reliability** | ✅ High | ⚠️ Medium | Selenium more reliable |
| **Cross-browser** | ✅ Yes | ❌ No | Selenium supports all browsers |

**Recommendation:** Use Selenium for web automation, PyAutoGUI for desktop apps

---

## 🎉 Summary

### ✅ Selenium is Already Integrated!

Your project already uses Selenium for:
- Browser automation
- Gmail automation
- LinkedIn automation
- Web searches

### ✅ Works with Byte!

Byte can control Selenium through voice:
- "Open Gmail" → Uses Selenium
- "Search for Python" → Uses Selenium
- "Open LinkedIn" → Uses Selenium

### ✅ Easy to Extend!

You can add custom Selenium automation:
1. Create custom handler
2. Register with Byte
3. Use voice commands

---

## 🚀 Next Steps

### 1. **Test Current Selenium Features**
```bash
python byte_conversational.py
```

Say:
- "Byte, open Gmail"
- "Byte, search for Python tutorials"
- "Byte, open LinkedIn"

### 2. **Add Custom Automation**
- Create custom handlers
- Add new voice commands
- Extend functionality

### 3. **Explore Advanced Features**
- Headless browsing
- Data extraction
- Form automation
- Multi-tab handling

---

**Selenium is ready to use with Byte! Start automating! 🤖✨**

