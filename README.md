# SREE – Personal AI Assistant
> *"Your Personal AI. Your Digital World."*

An intelligent, private, zero-operating-cost personal digital assistant inspired by JARVIS. SREE runs locally on your Windows laptop with dedicated **NVIDIA GPU acceleration (RTX 2050)** and serves both your laptop and your **Android smartphone** over your local network via an installable Progressive Web App (PWA).

---

## Complete Capabilities Matrix

| Module | Feature | Implementation | Zero Cost / Privacy Guarantee |
| :--- | :--- | :--- | :--- |
| **Local AI Engine** | `llama3.2:3b` | Local Ollama with CUDA acceleration | 100% free open-weights; loaded in 4 GB VRAM; zero cloud APIs |
| **User Interface** | Futuristic JARVIS HUD | Vanilla HTML5 / CSS3 / JavaScript PWA | Cyan & electric-blue theme with reactive animated AI Orb |
| **Two-Way Voice** | Speech In / Speech Out | Web Speech STT + System Speech Synthesis | Low-latency voice interaction with wake-word detection ("Hey Sree") |
| **Personal Memory** | Contextual long-term recall | SQLite Relational Database (WAL mode) | User-approved facts injected into prompts; full inspection/deletion |
| **Encrypted Notes** | Quick notes & tagging | Local SQLite with keyword search | Notes stored entirely on your laptop drive |
| **Reminders & Tasks**| Scheduling & task tracking | SQLite with completion toggling | Track daily action items and priorities |
| **Laptop Automation**| App launching & diagnostics | Security allowlist (`subprocess`) | Controlled execution of Calculator, Notepad, Terminal, VS Code, Explorer |
| **Safe File Search** | Document exploration | Path traversal boundary checks | Searches strictly inside approved folders (Documents, Downloads, Desktop) |
| **Live Web Search** | Real-time information | DuckDuckGo search integration | Free live search without paid API keys, with clear source attribution |
| **Data Sovereignty** | Export & Erase | One-click JSON backup / wipe | Full export of all memories, notes, and chat turns |

---

## Hardware Alignment (NVIDIA GeForce RTX 2050 + 8 GB RAM)

- **AI Model:** `llama3.2:3b` (3.2 Billion Parameters, 4-bit Quantization).
- **VRAM Allocation:** 2.4 GB allocated out of 4.0 GB VRAM.
- **Inference Speed:** ~30–45 tokens per second.
- **System Memory:** Leaves 1.6 GB of VRAM free for Windows graphics, and keeps system RAM free for smooth multitasking.

---

## Quickstart Guide

### 1. Launch SREE Master Server
From the project directory (`d:\sri`), run:
```bash
python scripts/start.py
```

### 2. Access on Laptop
Open your favorite browser (Chrome, Edge, Brave):
```
http://localhost:8005
```

### 3. Connect from Android Smartphone
1. Connect your Android phone to the **same Wi-Fi network** as your laptop.
2. Open Chrome on Android and navigate to:
```
http://10.43.242.207:8005
```
3. Tap the Chrome three-dot menu (`⋮`) and tap **"Add to Home screen"** or **"Install App"**.
4. SREE will launch as a standalone fullscreen app on your phone with shared conversations, memories, notes, and voice interaction!

---

## 24/7 Background System-Wide Voice Listener & Windows Auto-Startup

SREE includes a native Windows 24/7 background listener that runs automatically when your PC boots or powers on. You can be playing a game, writing code, or browsing, and simply say **"Hey Sree"** to talk live.

### Features
- **Zero-Click Windows Boot Activation**: Automatically starts silently when Windows powers on via `shell:startup`.
- **System-Wide Wake-Word**: Listens 24/7 on your default microphone for **"Hey Sree"**, **"Hey Sri"**, or **"Hey Siri"**.
- **Live Conversational Mode**: SREE chimes, acknowledges, and talks back through your speakers.
- **Hands-Free App Control**: Say *"Open Calculator"*, *"What's the weather"*, or *"What time is it"*.
- **Desktop HUD Summon**: Say *"Open SREE"* or *"Show dashboard"* anytime to pop up the desktop app window.

### Control Scripts
- [Enable_Auto_Startup.bat](file:///d:/sri/Enable_Auto_Startup.bat): Enable SREE to start on Windows power-on.
- [Disable_Auto_Startup.bat](file:///d:/sri/Disable_Auto_Startup.bat): Disable automatic boot launch.
- [Start_Background_Listener.bat](file:///d:/sri/Start_Background_Listener.bat): Start background listening immediately.
- [Stop_Background_Listener.bat](file:///d:/sri/Stop_Background_Listener.bat): Stop the background listener.

---

## Directory Structure

```
d:\sri\
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app with LAN CORS & static file mount
│   │   ├── api/                 # REST & streaming endpoints
│   │   │   ├── chat.py          # /api/chat & /api/chat/stream with memory & automation
│   │   │   ├── system.py        # /api/system/status hardware telemetry
│   │   │   ├── memory.py        # /api/memory CRUD endpoints
│   │   │   ├── notes.py         # /api/notes CRUD & search endpoints
│   │   │   ├── reminders.py     # /api/reminders task tracking endpoints
│   │   │   ├── automation.py    # /api/automation allowlisted app & file executor
│   │   │   ├── search.py        # /api/search live web search
│   │   │   ├── data.py          # /api/data export & wipe endpoints
│   │   │   └── router.py        # Unified router
│   │   ├── core/
│   │   │   └── config.py        # Environment variables & paths
│   │   ├── ai/
│   │   │   ├── ollama_client.py # Async HTTP client for local Ollama
│   │   │   └── prompts.py       # SREE persona system prompt
│   │   ├── database/
│   │   │   └── db.py            # SQLite schema manager (conversations, memory, notes, tasks)
│   │   ├── memory/
│   │   │   └── manager.py       # Context builder & memory intent parser
│   │   ├── automation/
│   │   │   ├── allowlist.py     # Authorized app definitions & folder boundaries
│   │   │   └── executor.py      # Safe execution engine
│   │   └── services/
│   │       └── search.py        # DuckDuckGo scraper
│   └── requirements.txt
├── frontend/
│   ├── index.html               # JARVIS HUD dashboard, modals, and views
│   ├── css/style.css            # Dark Navy & Cyan responsive styling
│   ├── js/app.js                # Core frontend engine (chat, voice, memory, automation)
│   ├── manifest.json            # PWA manifest
│   └── service-worker.js        # Offline caching service worker
├── data/
│   └── database/sree.db         # Persistent SQLite database
├── scripts/
│   ├── start.py                 # Startup script with auto LAN IP discovery
│   └── setup.py                 # Automated environment installer
├── tests/
│   ├── test_phase1.py           # Phase 1 backend unit tests
│   ├── test_master.py           # Full system integration test suite (8 Modules)
│   └── test_unit_suite.py       # Master 87-Unit-Test Suite (100% Pass Rate)
├── .env
├── .env.example
├── .gitignore
└── README.md
```

---

## Automated Verification & 87 Unit Tests Suite

You can verify the entire architecture across all sub-systems at any time:

### 1. 87 Unit Tests Suite (100% Pass Rate in ~0.12s)
Covers Dynamic Windows Path Resolution, 3-Tier Security Confirmation Guard, Skill Crystallizer 0ms fast-paths, Universal Multi-Provider AI Routing with Intra-Provider Cascades, SQLite Long-term Memory, Notes, Reminders, and Telemetry:
```bash
python tests/test_unit_suite.py
```

### 2. Full Live System Integration Test
Verifies live interaction with the active running server and Ollama:
```bash
python tests/test_master.py
```
