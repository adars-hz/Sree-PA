# Project SREE - Personal AI Assistant

## 🛠 Architecture
SREE is a local-first AI assistant designed for maximum privacy and zero operating cost.
- **Backend**: FastAPI (Python 3.13)
- **AI Engine**: Ollama (Local LLMs)
- **Database**: SQLite (Managed via SQLAlchemy & Alembic)
- **Frontend**: PWA (HTML/JS/CSS) served via FastAPI static files.

## 🚀 Quick Start
### Development
1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env` (see `.env.example`)
3. Start backend: `python backend/app/main.py`
4. Access UI: `http://localhost:8005`

### Production (Windows)
- Run `scripts/service_installer.py` to register SREE as a background service.
- Use `Launch_SREE.bat` to start the service.

## 📖 Coding Standards
- **Logging**: Use `from backend.app.core.logger import logger`. Replace all `print` statements.
- **Database**: All DB interactions must use `db_manager` in `backend/app/database/db.py`.
- **Security**: remote LAN access is protected by the `SREEAuthMiddleware`.
- **Automation**: All system commands must pass through `SecurityGuard` in `backend/app/automation/security_guard.py`.

## ⚙️ Critical Commands
- **DB Migrations**: `cd backend && alembic revision --autogenerate -m "desc" && alembic upgrade head`
- **Config Update**: Use `update_runtime_setting(key, value)` to persist settings to `.env`.
