"""
Ollama Async Client for SREE AI Engine
Handles model connection, health checks, streaming, and inference.
"""

import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx
from ..core.config import settings

logger = logging.getLogger("sree.ai.ollama")

class OllamaClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.default_model = settings.DEFAULT_MODEL
        self.fallback_model = settings.FALLBACK_MODEL
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=30.0)
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def is_available(self) -> bool:
        """Check if Ollama server is running and reachable."""
        try:
            client = await self.get_client()
            response = await client.get("/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama server unavailable at {self.base_url}: {e}")
            return False

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """List all models currently installed in local Ollama."""
        try:
            client = await self.get_client()
            response = await client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
            return []
        except Exception as e:
            logger.error(f"Error fetching Ollama models: {e}")
            return []

    async def resolve_model(self, requested_model: Optional[str] = None) -> str:
        """
        Determine the active model: requested -> default -> fallback -> first available.
        """
        models = await self.get_available_models()
        model_names = [m.get("name", "").split(":")[0] for m in models] + [m.get("name", "") for m in models]
        
        candidates = [requested_model, self.default_model, self.fallback_model]
        for c in candidates:
            if not c:
                continue
            base_c = c.split(":")[0]
            if c in model_names or base_c in model_names:
                return c
                
        # If none matched, return the first available model if any exist
        if models:
            return models[0].get("name", self.default_model)
            
        return requested_model or self.default_model

    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Standard non-streaming chat completion.
        """
        active_model = await self.resolve_model(model)
        client = await self.get_client()
        
        payload = {
            "model": active_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        response = await client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        
        return {
            "model": active_model,
            "content": data.get("message", {}).get("content", ""),
            "done": data.get("done", True),
            "eval_count": data.get("eval_count", 0),
            "eval_duration": data.get("eval_duration", 0)
        }

    async def chat_stream(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Streaming chat completion yielding text deltas token by token.
        """
        active_model = await self.resolve_model(model)
        client = await self.get_client()
        
        payload = {
            "model": active_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        
        async with client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
                except json.JSONDecodeError:
                    continue

# Global singleton
ollama_client = OllamaClient()

