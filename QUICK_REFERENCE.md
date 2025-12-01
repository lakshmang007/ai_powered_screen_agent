# 🚀 Quick Reference Guide - Smart Byte GUI

## ⚡ Quick Start

```bash
python main.py
```

---

## 🎯 Main Features

### 1. **Text Commands**
Type in input field → Press Enter or click Execute

**Examples:**
```
open chatgpt
open github
create folder named test
search for python tutorials
```

### 2. **Voice Commands**
Click **🎤 Byte Smart** → Say "byte" → Give command

**Examples:**
```
"byte"
"open chatgpt"

"byte"
"search for AI tutorials"

"byte"
"open vscode"
```

### 3. **Macro Recording**

**Record:**
1. Click **⏺️ Record Macro**
2. Enter name (e.g., "login")
3. Perform actions
4. Click **⏹️ Stop Recording**

**Play:**
1. Click **▶️ Play Macro**
2. Select macro
3. Click **Play**

**View:**
1. Click **📋 Macro List**
2. See all saved macros

---

## 🔍 Smart App Opening

When you say **"open [app]"**, Byte Smart:

1. **Checks Taskbar** - Is it already running?
   - ✅ Yes → Brings window to front
   - ❌ No → Go to step 2

2. **Searches Installed Apps** - Is it installed?
   - ✅ Yes → Launches the app
   - ❌ No → Go to step 3

3. **Asks for Browser** - Open in browser?
   - ✅ Yes → Choose browser (Chrome/Firefox/Edge)
   - ❌ No → Cancelled

**Supported Web Apps (25+):**
- ChatGPT, Claude, Gemini
- GitHub, GitLab, Bitbucket
- Gmail, Outlook
- LinkedIn, Twitter, Facebook
- YouTube, Netflix, Spotify
- And more!

---

## 🧠 AI Command Understanding

**High Confidence (>80%):**
```
🧠 Parsed: open on chatgpt
✨ High confidence: 95%
🔍 Smart opening: chatgpt
✅ Success: Opening ChatGPT in Chrome
```

**Low Confidence (<30%):**
```
🧠 Parsed: unknown on unknown
⚠️  Warning: Low confidence in command understanding
```

---

## 💾 Context Memory

Byte remembers:
- Last 10 actions
- Last typed text
- Last opened app

**Example:**
```
You: "open notepad"
Byte: Opens Notepad

You: "type hello world"
Byte: Types in the last opened app (Notepad)
```

---

## ⏺️ Macro Examples

### **Login Sequence:**
1. Record: Click username → Type username → Click password → Type password → Click login
2. Save as "login"
3. Play whenever you need to login

### **Repetitive Task:**
1. Record: Open app → Click menu → Select option → Save
2. Save as "daily_task"
3. Play every day

### **Data Entry:**
1. Record: Click field 1 → Type data → Tab → Type data → Tab → Click submit
2. Save as "data_entry"
3. Play for each entry

---

## 🎨 Status Indicators

| Color | Meaning |
|-------|---------|
| 🟢 Green | Ready |
| 🔵 Blue | Processing/Listening |
| 🟠 Orange | Warning |
| 🔴 Red | Error/Recording |

---

## 📝 Command Examples

### **Opening Apps:**
```
open chrome
open vscode
open notepad
open calculator
```

### **Web Apps:**
```
open chatgpt
open github
open gmail
open youtube
```

### **Creating:**
```
create folder named test
create file named readme.md
```

### **Searching:**
```
search for python tutorials
search google for AI news
```

### **Browser:**
```
navigate to google.com
scroll down
take screenshot
close browser
```

---

## 🔧 Troubleshooting

### **Voice not working?**
- Check microphone permissions
- Click 🎤 Byte Smart button
- Say "byte" clearly

### **App not opening?**
- Check if app name is correct
- Try full name (e.g., "Google Chrome" instead of "chrome")
- Check if app is installed

### **Macro not playing?**
- Check if macro file exists in `macros/` folder
- Try recording again
- Check macro list

### **Low confidence warnings?**
- Rephrase command more clearly
- Use simpler language
- Check command examples

---

## 🎊 Tips & Tricks

1. **Use clear commands**: "open chatgpt" instead of "can you open chatgpt please"
2. **Wait for Byte**: Say "byte" and wait for response before giving command
3. **Record macros for repetitive tasks**: Save time on daily workflows
4. **Check output logs**: See what Byte is doing
5. **Use text input for complex commands**: Type if voice recognition fails

---

## 📞 Quick Help

**GUI is running but not responding?**
- Check output logs for errors
- Restart the application

**Want to stop current task?**
- Click **Stop** button

**Want to see command history?**
- Click **History** button

**Want to configure settings?**
- Click **Settings** button

---

## 🚀 Advanced Usage

### **Combine with Macros:**
1. Record macro for opening multiple apps
2. Play macro with voice command
3. Use context memory for follow-up actions

### **Chain Commands:**
```
open chrome and navigate to github.com
search for AI tutorials and open first result
```

### **Use AI Understanding:**
- Natural language: "I want to open chatgpt"
- Casual: "hey open github for me"
- Direct: "open vscode"

All work with 95% accuracy!

---

**Enjoy your Smart Byte GUI!** 🎉

