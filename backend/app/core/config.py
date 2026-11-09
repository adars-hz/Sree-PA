import sys
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Frozen (PyInstaller .exe) vs Development Path Resolution
if getattr(sys, "frozen", False):
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    PERSISTENT_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "SREE"
    ROOT_DIR = BUNDLE_DIR
else:
    BUNDLE_DIR = Path(__file__).resolve().parent.parent.parent.parent
    PERSISTENT_DIR = BUNDLE_DIR
    ROOT_DIR = BUNDLE_DIR

PERSISTENT_DIR.mkdir(parents=True, exist_ok=True)
env_file = PERSISTENT_DIR / ".env" if (PERSISTENT_DIR / ".env").exists() else ROOT_DIR / ".env"

class Settings(BaseSettings):
    # Pydantic Settings configuration for env file loading
    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding='utf-8',
        extra='ignore'
    )

    APP_NAME: str = "SREE"
    APP_ENV: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8005

    # Active AI Provider: "ollama", "groq", "gemini", "openrouter", "openai", "custom"
    AI_PROVIDER: str = "ollama"

    # Ollama settings (Local 100% Offline)
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    DEFAULT_MODEL: str = "llama3.2:3b"
    FALLBACK_MODEL: str = "llama3.2:1b"

    # Cloud AI Keys & Endpoints (Optional Free & Premium)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    CUSTOM_OPENAI_BASE_URL: str = "http://localhost:1234/v1"
    CUSTOM_OPENAI_API_KEY: str = "not-needed"
    CUSTOM_MODEL: str = "default"

    # Security
    AUTH_TOKEN: str = "sree-local-secure-key-2026"
    ALLOW_LAN_ACCESS: bool = True

    # Paths
    BASE_DIR: Path = BUNDLE_DIR
    DATA_DIR: Path = PERSISTENT_DIR / "data"
    DB_PATH: Path = PERSISTENT_DIR / "data" / "database" / "sree.db"
    FRONTEND_DIR: Path = BUNDLE_DIR / "frontend"

    def update_runtime_setting(self, key: str, value: str):
        """
        Autonomous Configuration Healing:
        Updates in-memory settings and persists the changed key/value to runtime .env.
        """
        setattr(self, key, value)
        target_env = PERSISTENT_DIR / ".env"

        if not target_env.exists():
            with open(target_env, "w", encoding="utf-8") as f:
                f.write(f"{key}={value}\n")
            return

        with open(target_env, "r", encoding="utf-8") as f:
            lines = f.readlines()

        found = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                found = True
            else:
                new_lines.append(line)

        if not found:
            new_lines.append(f"{key}={value}\n")

        with open(target_env, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

settings = Settings()

def update_runtime_setting(key: str, value: str):
    """Module-level autonomous configuration healing helper."""
    settings.update_runtime_setting(key, value)

# Ensure necessary data directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
