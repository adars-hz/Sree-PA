import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env file from project root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

class Settings(BaseModel):
    APP_NAME: str = os.getenv("APP_NAME", "SREE")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8005"))
    
    # Active AI Provider: "ollama", "groq", "gemini", "openrouter", "openai", "custom"
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "ollama")
    
    # Ollama settings (Local 100% Offline)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
    FALLBACK_MODEL: str = os.getenv("FALLBACK_MODEL", "llama3.2:1b")
    
    # Cloud AI Keys & Endpoints (Optional Free & Premium)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    CUSTOM_OPENAI_BASE_URL: str = os.getenv("CUSTOM_OPENAI_BASE_URL", "http://localhost:1234/v1")
    CUSTOM_OPENAI_API_KEY: str = os.getenv("CUSTOM_OPENAI_API_KEY", "not-needed")
    CUSTOM_MODEL: str = os.getenv("CUSTOM_MODEL", "default")
    
    # Security
    AUTH_TOKEN: str = os.getenv("AUTH_TOKEN", "sree-local-secure-key-2026")
    ALLOW_LAN_ACCESS: bool = os.getenv("ALLOW_LAN_ACCESS", "true").lower() == "true"
    
    # Paths
    BASE_DIR: Path = ROOT_DIR
    DATA_DIR: Path = ROOT_DIR / "data"
    DB_PATH: Path = ROOT_DIR / os.getenv("DATABASE_PATH", "data/database/sree.db")
    FRONTEND_DIR: Path = ROOT_DIR / "frontend"

    def update_runtime_setting(self, key: str, value: str):
        """
        Autonomous Configuration Healing:
        Updates in-memory settings and persists the changed key/value to runtime .env.
        """
        setattr(self, key, value)
        env_file = ROOT_DIR / ".env"
        if not env_file.exists():
            with open(env_file, "w", encoding="utf-8") as f:
                f.write(f"{key}={value}\n")
            return
            
        with open(env_file, "r", encoding="utf-8") as f:
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
            
        with open(env_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

settings = Settings()

def update_runtime_setting(key: str, value: str):
    """Module-level autonomous configuration healing helper."""
    settings.update_runtime_setting(key, value)

# Ensure necessary data directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

