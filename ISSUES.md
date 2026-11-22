# Project SREE – Issues, Bugs & Feature Backlog 📌

This document tracks all identified bugs, resolved issues, feature proposals, and architectural enhancements for **Project SREE**. Contributors are encouraged to pick up any open issue from this backlog.

---

## 🚦 Status Legend
- 🟢 **[RESOLVED]**: Resolved, verified, and tested in the active contribution branch.
- 🟡 **[OPEN / IN BACKLOG]**: Open for implementation by contributors.
- 🔵 **[PLANNED ROADMAP]**: Architectural initiative scheduled for upcoming releases.

---

## 🛠️ Resolved Issues & Fixes (Active Contribution)

### #ISSUE-01: SQLite Database Tables Auto-Bootstrap Missing on Clean Clones
- **Type**: 🐛 Bug (High Severity)
- **Status**: 🟢 [RESOLVED]
- **Component**: `backend/app/database/db.py`
- **Description**: When cloning SREE or running the test suite on a system without a pre-existing `sree.db` file, database tables (`conversations`, `memories`, `notes`, `reminders`, `user_settings`) were never created because `Base.metadata.create_all(bind=self.engine)` was omitted in `DatabaseManager.__init__`. This resulted in `sqlite3.OperationalError: no such table: memories` and caused 14 unit tests to fail.
- **Resolution**: Added `Base.metadata.create_all(bind=self.engine)` inside `DatabaseManager.__init__`. Now, any fresh installation or temporary test database automatically bootstraps the complete schema.
- **Test Added**: `test_88_fresh_db_auto_bootstrap` in `tests/test_unit_suite.py`.

---

### #ISSUE-02: Missing Core Dependencies in `requirements.txt`
- **Type**: 🐛 Bug (High Severity)
- **Status**: 🟢 [RESOLVED]
- **Component**: `requirements.txt`
- **Description**: Dependencies directly imported by core modules were missing from `requirements.txt`:
  - `pyautogui` (OS automation in `desktop_control.py`)
  - `pillow` (Screen sharing and tray icons in `screen_share.py`, `run_sree_app.py`)
  - `qrcode[pil]` (Mobile pairing in `backend/app/api/system.py`)
  - `beautifulsoup4` (Live web scraping in `backend/app/services/search.py`)
  - `numpy` & `scipy` (Acoustic voiceprint analysis in `backend/app/audio/voice_biometrics.py`)
  - `pystray` (Native Windows system tray HUD)
- **Resolution**: Updated `requirements.txt` with clear version constraints and categorized comments.

---

### #ISSUE-03: `tests/test_desktop_screen_suite.py` Direct Execution Failure
- **Type**: 🐛 Bug (Medium Severity)
- **Status**: 🟢 [RESOLVED]
- **Component**: `tests/test_desktop_screen_suite.py`
- **Description**: Running `python tests/test_desktop_screen_suite.py` directly caused `ModuleNotFoundError: No module named 'backend'` because the project root directory was not inserted into `sys.path`.
- **Resolution**: Added `sys.path.insert(0, str(PROJECT_ROOT))` and `unittest.main()` entrypoint, allowing all 19 tests to run seamlessly both directly and via unittest runners.

---

### #ISSUE-04: Unhandled `qrcode` Import Exception in `system.py`
- **Type**: 🐛 Bug (Medium Severity)
- **Status**: 🟢 [RESOLVED]
- **Component**: `backend/app/api/system.py`
- **Description**: `import qrcode` was placed at top-level in `system.py` without exception handling. If `qrcode` was uninstalled or failed to load image plugins, the entire API router and FastAPI backend failed to start.
- **Resolution**: Wrapped `qrcode` import in try-except with `QRCODE_AVAILABLE` flag. The `/api/system/qrcode` endpoint now returns a clean 503 HTTP status if the library is unavailable rather than crashing module import.

---

### #ISSUE-05: Headless & Non-GUI Server Crash in `desktop_control.py`
- **Type**: 🐛 Bug (Medium Severity)
- **Status**: 🟢 [RESOLVED]
- **Component**: `backend/app/automation/desktop_control.py`
- **Description**: Top-level `import pyautogui` crashed with display errors or module errors when running backend tests in headless servers, CI runners, or Docker containers.
- **Resolution**: Added safe try-except import guard and screen resolution fallback `(1920, 1080)`. Desktop control methods return graceful error responses if display control is unavailable.

---

### #ISSUE-06: Incomplete Data Wipe Pipeline in Chat Confirmation
- **Type**: 🐛 Bug (Low Severity)
- **Status**: 🟢 [RESOLVED]
- **Component**: `backend/app/api/chat.py`
- **Description**: When confirming a sensitive `wipe_data` action ("Permanently erase all personal memories, notes, and conversation records..."), the handler only called `db_manager.clear_conversation()`, leaving notes, reminders, and long-term memories intact.
- **Resolution**: Updated the confirmed action handler to invoke `db_manager.wipe_all_data()`.
- **Test Added**: `test_90_wipe_data_security_full_reset` in `tests/test_unit_suite.py`.

---

### #ISSUE-07: Interactive HUD Text Command Input Bar for Non-Voice Users
- **Type**: ✨ Feature (Medium Priority)
- **Status**: 🟢 [RESOLVED]
- **Component**: `frontend/index.html`, `frontend/css/style.css`, `frontend/js/app.js`
- **Description**: The holographic cockpit required microphone/speech input, with text inputs hidden (`display: none`). Users in noisy or quiet environments (libraries, offices) or without working microphones had no way to type instructions.
- **Resolution**: Created a futuristic neon HUD command bar in the footer with:
  - Input field with placeholder and autocomplete disabled.
  - Send button (`➤`) and Enter key submission.
  - Mic toggle button (`🎙️`) for one-click voice activation.
  - Global `/` keyboard shortcut to immediately focus the command input.

---

### #ISSUE-08: Hardcoded Repository Paths in `README.md` and `.env.example`
- **Type**: 📝 Documentation & Config (Low Severity)
- **Status**: 🟢 [RESOLVED]
- **Component**: `README.md`, `.env.example`
- **Description**: `README.md` referenced hardcoded paths (`d:\sri\`) and static IP addresses (`10.43.242.207:8005`). `.env.example` was missing environment variables for the multi-provider cloud AI router (`GROQ_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `OPENAI_API_KEY`).
- **Resolution**: Updated `README.md` with relative commands and dynamic IP placeholders. Enriched `.env.example` with comprehensive documentation for all supported AI engines.

---

## 📋 Open Feature Requests & Backlog (For Contributors)

### #ISSUE-09: Real-Time Bi-Directional WebSocket Voice Pipeline (Whisper & Piper TTS)
- **Type**: ✨ Feature Request
- **Priority**: High
- **Status**: 🟡 [OPEN / IN BACKLOG]
- **Component**: `backend/app/api/voice.py`, `frontend/js/app.js`
- **Description**: Currently, voice input in the web browser relies on Web Speech API (`webkitSpeechRecognition`), which requires Chrome/Edge and internet connectivity.
- **Proposed Solution**:
  - Implement a WebSocket streaming audio endpoint `/api/voice/stream`.
  - Stream raw microphone PCM audio to a local offline Faster-Whisper model.
  - Stream synthesized voice back to the frontend using a local Piper or Kokoro TTS engine for ultra-low latency, 100% offline two-way voice.
- **Acceptance Criteria**:
  - Full voice conversation functions with zero internet access in any browser (including Firefox/Brave).
  - Voice-to-text latency under 350ms on RTX 2050.

---

### #ISSUE-10: Offline Semantic Memory Search using Local Vector Embeddings
- **Type**: ✨ Feature Request (Closes GitHub Issue #3)
- **Priority**: High
- **Status**: 🟢 [RESOLVED]
- **Component**: `backend/app/memory/semantic_engine.py`, `backend/app/memory/manager.py`, `backend/app/database/db.py`, `backend/app/api/memory.py`, `backend/app/api/chat.py`
- **Description**: Memory retrieval previously relied on keyword matching. When a user accumulated memories, conceptually related queries (e.g., asking "what are my coding tools" when the stored memory is "favorite editor is VS Code") failed to retrieve relevant context.
- **Resolution**:
  - **Local Semantic Vector Engine (`semantic_engine.py`)**: Built a 128-dimensional deterministic semantic cluster and subword n-gram embedding engine running in $<1$ms with 100% offline privacy and zero external costs. Integrates with Ollama embedding models (`/api/embeddings`, `/api/embed`) when present with seamless fallback.
  - **Database Persistence (`db.py`)**: Added `embedding` column to `Memory` model with automatic SQLite schema migration on startup.
  - **Contextual Ranking & Injection (`manager.py`, `chat.py`)**: Added `search_semantic_memories` and `get_relevant_memory_context` using NumPy cosine similarity, ranking top-$k$ relevant memories and injecting them into the LLM system prompt with relevance scores.
  - **REST Endpoints (`memory.py`)**: Added `GET /api/memory/search` and `POST /api/memory/reindex`.
- **Tests Added**: 9 new unit tests (`test_91` to `test_99`) in `tests/test_unit_suite.py` verifying vector norms, cosine math, conceptual ranking (Editor/Python vs. Pet), DB persistence, reindexing, and API endpoints. All 99 unit tests and 25 desktop automation tests pass (124 total, 100% pass rate).

---

### #ISSUE-11: Multi-Monitor Desktop Control & Screen Coordinate Normalization
- **Type**: ✨ Feature Request (Closes GitHub Issue #5)
- **Priority**: Medium
- **Status**: 🟢 [RESOLVED]
- **Component**: `backend/app/automation/desktop_control.py`, `backend/app/api/desktop.py`, `frontend/`
- **Description**: When multiple monitors are connected, PyAutoGUI actions defaulted to the primary monitor and failed to map coordinates on secondary displays with different DPI scaling.
- **Resolution**:
  - Implemented Win32 `EnumDisplayMonitors` monitor enumeration via `ctypes`.
  - Added endpoints `/api/desktop/monitors` and `/api/desktop/monitors/select`.
  - Implemented DPI-aware coordinate normalization supporting `x_ratio` and `y_ratio` (0.0 to 1.0) and monitor index offsets.
  - Added Monitor selector in the frontend HUD desktop viewer with responsive click coordinate normalization.
- **Tests Added**: 6 new unit tests in `tests/test_desktop_screen_suite.py` (`test_20` to `test_25`). All 25 desktop tests pass.

---

### #ISSUE-12: Media Player & Spotify Native Desktop Integration
- **Type**: ✨ Feature Request
- **Priority**: Medium
- **Status**: 🟡 [OPEN / IN BACKLOG]
- **Component**: `backend/app/automation/crystallizer.py`
- **Description**: Add 0ms fast-path voice commands for media playback:
  - "play next track", "pause music", "previous song", "what's playing".
  - Integrate with Windows System Media Transport Controls (SMTC) or Spotify Local Web API.
- **Acceptance Criteria**:
  - Saying "Hey Sree, play next song" sends media key press or API call in $<10$ms.

---

### #ISSUE-13: Calendar & Proactive Daily Schedule Reminders
- **Type**: ✨ Feature Request
- **Priority**: Medium
- **Status**: 🟡 [OPEN / IN BACKLOG]
- **Component**: `backend/app/services/briefing.py`, `backend/app/api/reminders.py`
- **Description**: Enhance the Daily Briefing engine to parse local `.ics` iCalendar files or Google/Outlook calendar events and alert the user 10 minutes prior to meetings via desktop notification / audio chime.

---

### #ISSUE-14: Automated CI/CD GitHub Actions Workflow
- **Type**: ⚙️ Infrastructure / DevOps
- **Priority**: Medium
- **Status**: 🟡 [OPEN / IN BACKLOG]
- **Component**: `.github/workflows/ci.yml`
- **Description**: Set up automated continuous integration:
  - Run linting (`flake8` / `black --check`).
  - Execute test suite (`python tests/test_unit_suite.py` and `test_desktop_screen_suite.py`).
  - Build standalone Windows executable (`Build_EXE.bat` / PyInstaller) and attach artifacts on release tags.

---

### #ISSUE-15: At-Rest Encryption for SQLite Database (SQLCipher)
- **Type**: 🔒 Security Enhancement
- **Priority**: Medium
- **Status**: 🟡 [OPEN / IN BACKLOG]
- **Component**: `backend/app/database/db.py`
- **Description**: Enable transparent database encryption using `sqlcipher` or AES-GCM row-level encryption for sensitive user notes and biometric voiceprints stored in `data/database/sree.db`.

---

### #ISSUE-16: Customizable HUD Accent Colors & Sound Effects
- **Type**: 🎨 UI / UX Enhancement
- **Priority**: Low
- **Status**: 🟡 [OPEN / IN BACKLOG]
- **Component**: `frontend/css/style.css`, `frontend/js/app.js`
- **Description**: Allow users to switch between Cyber Cyan, Crimson Alert, Matrix Green, and Royal Purple HUD themes directly from the Settings modal, persisting preferences in `localStorage` or `user_settings`.

---

## 🤝 How to Claim an Issue
1. Check that the issue is marked 🟡 **[OPEN / IN BACKLOG]**.
2. Comment on the issue or create a feature branch `feature/<issue-name>`.
3. Follow the guidelines in [CONTRIBUTING.md](CONTRIBUTING.md).
4. Submit a Pull Request referencing the Issue ID!
