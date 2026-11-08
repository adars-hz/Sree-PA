"""
Voice Biometrics & Speaker Verification API Endpoints
Provides voiceprint enrollment, verification, and authentication settings.
Accepts Base64 audio, WAV file paths, or direct binary audio payloads.
"""

import base64
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..audio.voice_biometrics import voice_biometrics

router = APIRouter(prefix="/api/voice", tags=["Voice Biometrics"])

class VoiceToggleRequest(BaseModel):
    enabled: bool

class VoiceThresholdRequest(BaseModel):
    threshold: float

class VoiceEnrollRequest(BaseModel):
    speaker_name: Optional[str] = "Boss"
    audio_base64: Optional[str] = None
    audio_file_path: Optional[str] = None

class VoiceVerifyRequest(BaseModel):
    audio_base64: Optional[str] = None
    audio_file_path: Optional[str] = None

@router.get("/status")
def get_voice_status() -> Dict[str, Any]:
    """Returns speaker profile status and verification requirement."""
    return voice_biometrics.get_status()

@router.post("/toggle")
def toggle_voice_verification(req: VoiceToggleRequest) -> Dict[str, Any]:
    """Enables or disables speaker verification enforcement."""
    voice_biometrics.set_enabled(req.enabled)
    return {
        "success": True,
        "enabled": voice_biometrics.enabled,
        "message": "Voice verification enabled." if voice_biometrics.enabled else "Voice verification disabled."
    }

@router.post("/threshold")
def set_voice_threshold(req: VoiceThresholdRequest) -> Dict[str, Any]:
    """Sets the cosine similarity threshold (0.50 - 0.95)."""
    voice_biometrics.set_threshold(req.threshold)
    return {
        "success": True,
        "threshold": voice_biometrics.similarity_threshold
    }

@router.post("/enroll")
async def enroll_voice_sample(
    payload: VoiceEnrollRequest
) -> Dict[str, Any]:
    """Enrolls an utterance into the owner voice profile."""
    audio_bytes = None

    if payload.audio_base64:
        # Strip data URL header if present (e.g. data:audio/wav;base64,...)
        b64_str = payload.audio_base64
        if "," in b64_str:
            b64_str = b64_str.split(",", 1)[1]
        audio_bytes = base64.b64decode(b64_str)
    elif payload.audio_file_path:
        path = Path(payload.audio_file_path)
        if path.exists():
            with open(path, "rb") as f:
                audio_bytes = f.read()

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="No audio data provided for enrollment.")

    result = voice_biometrics.enroll_sample(audio_bytes, speaker_name=payload.speaker_name or "Boss")
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Enrollment failed."))
    return result

@router.post("/verify")
async def verify_voice_sample(
    payload: VoiceVerifyRequest
) -> Dict[str, Any]:
    """Verifies candidate audio against the enrolled voiceprint."""
    audio_bytes = None

    if payload.audio_base64:
        b64_str = payload.audio_base64
        if "," in b64_str:
            b64_str = b64_str.split(",", 1)[1]
        audio_bytes = base64.b64decode(b64_str)
    elif payload.audio_file_path:
        path = Path(payload.audio_file_path)
        if path.exists():
            with open(path, "rb") as f:
                audio_bytes = f.read()

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="No audio data provided for verification.")

    return voice_biometrics.verify_audio(audio_bytes)

@router.post("/clear")
def clear_voice_profile() -> Dict[str, Any]:
    """Deletes the enrolled voiceprint profile."""
    voice_biometrics.clear_profile()
    return {"success": True, "message": "Voice profile cleared."}
