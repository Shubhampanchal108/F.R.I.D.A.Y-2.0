# ⚡ F.R.I.D.A.Y 4.0 — Autonomous Cyberpunk AI Agent

<p align="center">
  <img src="https://img.shields.io/badge/Version-4.0%20Super--Agent-00f2fe?style=for-the-badge&logo=robot&logoColor=white" alt="Version 4.0" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/UI-Rich%20Cyberpunk%20HUD-ff007f?style=for-the-badge&logo=terminal&logoColor=white" alt="Rich Terminal HUD" />
  <img src="https://img.shields.io/badge/Architecture-Async%20Daemon%20%2B%20Sub--Agents-00ff87?style=for-the-badge&logo=cpu&logoColor=white" alt="Async Daemon" />
</p>

> **F.R.I.D.A.Y** (*Friendly Reliable Intelligent Digital Assistant for Youth*) is a **JARVIS-class Autonomous Desktop AI Agent** built in Python. Designed to run as a continuous background daemon and a rich cyberpunk terminal interface, F.R.I.D.A.Y features **Screen Perception**, **Python Code Execution Sandbox**, **Proactive Morning Briefings**, **Deep Web Research Sub-Agents**, **ChromaDB Vector RAG Memory**, and **Hands-Free Wake-Word Activation**.

---

```
╔════════════════════════════════════════════════════════════════════════╗
║   ███████╗██████╗ ██╗██████╗  █████╗ ██╗   ██╗                         ║
║   ██╔════╝██╔══██╗██║██╔══██╗██╔══██╗╚██╗ ██╔╝                         ║
║   █████╗  ██████╔╝██║██║  ██║███████║ ╚████╔╝                          ║
║   ██╔══╝  ██╔══██╗██║██║  ██║██╔══██║  ╚██╔╝                           ║
║   ██║     ██║  ██║██║██████╔╝██║  ██║   ██║                            ║
║   ╚═╝     ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝   ╚═╝                            ║
║                                                                        ║
║   ⚡ Friendly Reliable Intelligent Digital Assistant — v4.0 HUD ⚡     ║
╚════════════════════════════════════════════════════════════════════════╝
```

---

## 🔥 Key Super-Agent Capabilities

### 📸 1. Screen Vision Perception (`JARVIS Vision`)
Give F.R.I.D.A.Y eyes to see your desktop screen:
- **`analyze_screen(prompt)`**: Takes an instant desktop screenshot and sends it to Vision LLMs.
- **Capabilities**: Debug code errors visible on screen, summarize documents open in apps, or analyze UI charts.

### 🐍 2. Python Code Execution Sandbox
- **`run_python_code(code)`**: Safely executes Python snippets in an isolated subprocess with stdout/stderr capture and 15s timeout safeguards.
- **Capabilities**: Solve math problems, process Excel/CSV files, generate charts, or write automation scripts on the fly.

### 🌅 3. Proactive Morning Briefing Daemon
- **Continuous Watchdog**: Runs as a background daemon thread (`daemon.py`).
- **`trigger_morning_briefing()`**: Synthesizes weather forecast, pending reminders, battery health, and top news into a voice announcement and native **Windows Desktop Notification**.

### 🤖 4. Specialized Autonomous Sub-Agents
- 🌐 **Deep Researcher Sub-Agent (`deep_research_agent`)**: Performs multi-query web searches, scrapes dynamic web pages, and synthesizes structured research reports.
- 💻 **Code Reviewer Sub-Agent (`code_reviewer_agent`)**: Analyzes codebase files for bugs, security risks, efficiency, and refactoring tips.

### 🌐 5. Web Autopilot Scraper
- **`extract_webpage_content(url)`**: Scrapes readable main text content from dynamic websites and technical documentation.

### 🎙️ 6. Hands-Free Wake-Word Listener
- **`WakeWordListener`**: Background listener checking for keywords (`"Friday"`, `"Hey Friday"`) to trigger voice listening without touching the keyboard.

### ⚙️ 7. First-Time Setup Wizard & Dynamic Config Manager
- **`run_first_time_setup()`**: Interactive setup wizard that launches automatically on new machines to set up LLM API keys, provider URLs, security passwords, and user profile details.
- **`interactive_config_editor()` (`/config`)**: On-the-fly terminal menu to view or update any configuration setting with masked API key privacy.

---

## 🏛️ System Architecture

```
                               ┌────────────────────────────────────────────────────────┐
                               │             F.R.I.D.A.Y  CLI  Agent  (v4.0)            │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                      ┌────────────────────────────────────┴────────────────────────────────────┐
                      ▼                                                                         ▼
       ┌──────────────────────────────┐                                          ┌──────────────────────────────┐
       │   Cyberpunk Console HUD      │                                          │   Background Event Daemon    │
       │   (Rich UI, Slash Commands,  │                                          │   - Due Reminder Watchdog    │
       │    Voice / Typing Modes)     │                                          │   - Morning Voice Briefing   │
       └──────────────┬───────────────┘                                          │   - Windows Desktop Alerts   │
                      │                                                          └──────────────┬───────────────┘
                      │                                                                         │
                      └────────────────────────────────────┬────────────────────────────────────┘
                                                           │
                                                           ▼
                                            ┌──────────────────────────────┐
                                            │      Agent Brain Loop        │
                                            │  - Structured Multi-Tool     │
                                            │  - ChromaDB Vector RAG       │
                                            │  - Sub-Agents Router         │
                                            └──────────────┬───────────────┘
                                                           │
                                                           ▼
                                            ┌──────────────────────────────┐
                                            │     40+ Native Tools & ACL   │
                                            │  - Screen Vision Perception  │
                                            │  - Python Code Interpreter   │
                                            │  - Web Scraping Autopilot    │
                                            │  - System / Mobile Automation│
                                            └──────────────────────────────┘
```

---

## 💻 Installation & Quick Start

### 1. Prerequisites
- **Python 3.10+** installed.
- Recommended OS: **Windows 10/11** (Supports Linux/macOS).

### 2. Clone & Setup Virtual Environment
```bash
git clone https://github.com/Shubhampanchal108/F.R.I.D.A.Y.git
cd F.R.I.D.A.Y

python -m venv .venv
.venv\Scripts\activate   # On Windows
# source .venv/bin/activate  # On Linux/macOS
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run F.R.I.D.A.Y
```bash
python index.py
```

> 💡 **First-Time Setup**: If running for the first time, F.R.I.D.A.Y will automatically launch the **Interactive Setup Wizard** to prompt for your LLM Provider URL, API Key, and Security Password!

---

## 🎮 Command Palette & Slash Commands

| Command | Description |
| :--- | :--- |
| `/voice` | Switch to Voice Recognition Mode (`SpeechRecognition`) |
| `/type` | Switch to Typing Mode |
| `/audio` | Toggle Speech Audio Drive ON/OFF (`gTTS` + `pygame`) |
| `/briefing` | Trigger Proactive Voice & Desktop Morning Briefing |
| `/wakeword` | Toggle Hands-Free Background Wake-Word Activation (`"Friday"`) |
| `/status` | Display System Health HUD (CPU %, Battery, Vector Memory, Daemon Logs) |
| `/reminders` | Display Pending & Active Reminders |
| `/config` | Open Dynamic Configuration Editor Wizard |
| `/clear` | Clear Terminal Dashboard |
| `/exit` | Shutdown F.R.I.D.A.Y Agent & Background Daemon cleanly |

---

## 🛠️ Complete Tool Arsenal (40+ Tools)

- 📸 **Vision**: `analyze_screen`
- 🐍 **Execution**: `run_python_code`
- 🌐 **Web**: `google_search`, `extract_webpage_content`, `summrize_url`, `open_website`, `search_wikipedia`
- 🤖 **Sub-Agents**: `deep_research_agent`, `code_reviewer_agent`
- 🧠 **Memory**: `save_longterm_memory` (ChromaDB RAG)
- 💻 **System**: `check_battery`, `check_cpu`, `find_my_ip`, `open_app`, `close_app`, `volume_up/down`, `brightness_up/down`, `capture_screenshot`
- 📱 **Mobile Automation**: `connect_mobile_with_bat`, `unlock_device`, `send_whatsapp_message`, `phone_call_with_mobile`
- ✉️ **Communication**: `read_latest_emails`, `readmail_Full_body`, `send_email`, `check_new_mail`
- ⏰ **Tasks & Reminders**: `add_reminder`, `list_reminders`, `get_due_reminders`, `add_task`, `list_tasks`, `complete_task`
- 📁 **Files**: `create_and_open_file`, `read_file`, `update_file`, `delete_file`, `list_files`, `search_file_in_folder`

---

## 🧑‍💻 Developer & Credits

**Shubham** — *Computer Science Engineering Student, Full-Stack & AI/ML Developer*
- 🌐 **Portfolio**: [shubhamportfolio3.netlify.app](https://shubhamportfolio3.netlify.app/)
- 💻 **GitHub**: [@Shubhampanchal108](https://github.com/Shubhampanchal108)
- 🔗 **LinkedIn**: [Shubham Panchal](https://www.linkedin.com/in/shubham-panchal-a80053306)

---

## ❤️ Vision

> *"One day, F.R.I.D.A.Y will not just assist — she will collaborate."* 🚀🤖