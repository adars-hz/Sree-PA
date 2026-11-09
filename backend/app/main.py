"""
SREE - Personal Digital AI Assistant
Main FastAPI Application Entrypoint
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .core.config import settings
from .core.logger import logger
from .api.router import api_router
from .ai.ollama_client import ollama_client
from .security.auth import SREEAuthMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("=======================================================")
    logger.info("  [+] Starting SREE Personal AI Assistant")
    logger.info(f"  [+] Engine Host: {settings.HOST}:{settings.PORT}")
    logger.info(f"  [+] Ollama Endpoint: {settings.OLLAMA_BASE_URL}")
    logger.info(f"  [+] Default Model: {settings.DEFAULT_MODEL}")
    logger.info("=======================================================")
    yield
    # Shutdown actions
    await ollama_client.close()
    logger.info("  [-] SREE Backend stopped.")

app = FastAPI(
    title=settings.APP_NAME,
    description="Your Personal AI. Your Digital World.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for local laptop browser and Android PWA access over LAN
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows access from LAN IPs (phone) and localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add SREE Authentication Middleware for LAN Security
app.add_middleware(SREEAuthMiddleware)

# Health check route
@app.get("/health")
async def health_check():
    """Simple ping health-check."""
    ollama_ready = await ollama_client.is_available()
    return {
        "status": "healthy" if ollama_ready else "degraded",
        "app": settings.APP_NAME,
        "ollama": "connected" if ollama_ready else "disconnected"
    }

# Register API routes
app.include_router(api_router)

# Mount frontend directory for PWA / UI after all API routes
if settings.FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(settings.FRONTEND_DIR), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

