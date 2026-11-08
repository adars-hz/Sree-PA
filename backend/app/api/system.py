"""
System Health, Telemetry, Diagnostics, Weather, and Daily Briefing API
"""

import os
import io
import socket
import platform
import psutil
from fastapi import APIRouter, Response, Query
import qrcode
from ..core.config import settings
from ..ai.ollama_client import ollama_client
from ..ai.universal_router import universal_router, PROVIDER_CASCADES
from ..services.weather import weather_service
from ..services.briefing import briefing_engine
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

router = APIRouter(prefix="/api/system", tags=["System"])

def get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@router.get("/status")
async def get_system_status():
    """
    Returns complete system telemetry, hardware metrics, and Ollama status.
    """
    ollama_online = await ollama_client.is_available()
    models = await ollama_client.get_available_models() if ollama_online else []
    
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=None)
    disk = psutil.disk_usage(str(settings.BASE_DIR))
    lan_ip = get_lan_ip()
    
    return {
        "assistant": {
            "name": settings.APP_NAME,
            "version": "1.0.0",
            "tagline": "Your Personal AI. Your Digital World.",
            "status": "operational" if ollama_online else "degraded",
            "environment": settings.APP_ENV,
            "lan_ip": lan_ip,
            "mobile_url": f"http://{lan_ip}:{settings.PORT}"
        },
        "ai_engine": {
            "ollama_online": ollama_online,
            "endpoint": settings.OLLAMA_BASE_URL,
            "default_model": settings.DEFAULT_MODEL,
            "installed_models": [m.get("name") for m in models]
        },
        "hardware": {
            "os": f"{platform.system()} {platform.release()}",
            "machine": platform.machine(),
            "cpu_percent": cpu_percent,
            "ram_total_gb": round(memory.total / (1024**3), 2),
            "ram_used_gb": round(memory.used / (1024**3), 2),
            "ram_free_gb": round(memory.available / (1024**3), 2),
            "ram_percent": memory.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2)
        }
    }

@router.get("/models")
async def list_models():
    """List all local AI models available in Ollama."""
    ollama_online = await ollama_client.is_available()
    if not ollama_online:
        return {"error": "Ollama service is not running", "models": []}
    models = await ollama_client.get_available_models()
    return {"models": models}

@router.get("/weather")
async def get_current_weather(city: str = Query("auto")):
    """Get live weather telemetry via free Open-Meteo."""
    return await weather_service.get_weather(city=city)

@router.get("/briefing")
async def get_daily_briefing(city: str = Query("auto")):
    """Get executive daily briefing with weather, tasks, and system telemetry."""
    return await briefing_engine.generate_briefing(city=city)

@router.get("/qrcode")
async def get_mobile_pairing_qrcode():
    """
    Generates a live QR Code image pointing to SREE's mobile URL
    so the user can point their Android camera and connect instantly.
    """
    lan_ip = get_lan_ip()
    mobile_url = f"http://{lan_ip}:{settings.PORT}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(mobile_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#00f2fe", back_color="#030712")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    
    return Response(content=buf.getvalue(), media_type="image/png")

# ==========================================
# UNIVERSAL AI BRAIN & MODEL CHIPS API
# ==========================================
class ProviderConfigRequest(BaseModel):
    provider: str
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None

@router.get("/ai/status")
async def get_ai_brain_status():
    """Returns active provider, model, cascades, and credentials status."""
    return await universal_router.get_active_status()

@router.post("/ai/select")
async def update_ai_provider(req: ProviderConfigRequest):
    """Updates active AI provider and optionally custom endpoint/key."""
    if req.api_key:
        key_var = f"{req.provider.upper()}_API_KEY"
        settings.update_runtime_setting(key_var, req.api_key)
    if req.base_url and req.provider == "custom":
        settings.update_runtime_setting("CUSTOM_OPENAI_BASE_URL", req.base_url)

    universal_router.set_provider(req.provider, req.model)
    return {
        "status": "success",
        "active_provider": universal_router.active_provider,
        "active_model": universal_router.active_model
    }

@router.get("/ai/ollama-chips")
async def get_ollama_chips():
    """
    Returns installed local models formatted as interactive chips
    for one-click activation in the Control Center.
    """
    ollama_online = await ollama_client.is_available()
    if not ollama_online:
        return {"online": False, "chips": []}

    models = await ollama_client.get_available_models()
    chips = []
    active = universal_router.active_model

    for m in models:
        name = m.get("name", "")
        size_bytes = m.get("size", 0)
        size_gb = round(size_bytes / (1024**3), 1) if size_bytes else 0
        chips.append({
            "name": name,
            "label": name,
            "size_gb": size_gb,
            "is_active": (name == active or name.split(":")[0] == active.split(":")[0])
        })

    return {"online": True, "active_model": active, "chips": chips}
