"""
Universal Multi-Provider AI Router with Intra-Provider Model Cascading & Autonomous Healing
Supports:
  - Local Ollama (100% Offline, GPU accelerated)
  - Groq Cloud (~200ms ultra-fast inference with free tier)
  - OpenRouter (100+ free open-weights models)
  - Google Gemini (Gemini 2.0 Flash with Google AI Studio free tier)
  - OpenAI (GPT-4o, GPT-4o-mini)
  - Custom OpenAI-Compatible Endpoints (LM Studio, LocalAI, vLLM, DeepSeek, Together AI)
"""

import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx
from ..core.config import settings
from .ollama_client import ollama_client

logger = logging.getLogger("universal_router")

# Intra-Provider Model Cascades (Fallback chains when 404/429 occurs)
PROVIDER_CASCADES = {
    "groq": [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "deepseek-r1-distill-llama-70b",
        "gemma2-9b-it"
    ],
    "openrouter": [
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemini-2.0-flash-exp:free",
        "deepseek/deepseek-r1:free",
        "qwen/qwen-2.5-72b-instruct:free"
    ],
    "gemini": [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-2.0-flash-exp"
    ],
    "openai": [
        "gpt-4o-mini",
        "gpt-4o"
    ],
    "ollama": [
        settings.DEFAULT_MODEL,
        settings.FALLBACK_MODEL
    ]
}

PROVIDER_ENDPOINTS = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions"
}

class UniversalAIRouter:
    PROVIDERS = {
        "groq": {
            "models_cascade": PROVIDER_CASCADES["groq"],
            "default_model": settings.GROQ_MODEL
        },
        "openrouter": {
            "free_models": PROVIDER_CASCADES["openrouter"],
            "default_model": settings.OPENROUTER_MODEL
        },
        "gemini": {
            "models_cascade": PROVIDER_CASCADES["gemini"],
            "default_model": settings.GEMINI_MODEL
        },
        "openai": {
            "default_model": settings.OPENAI_MODEL
        },
        "custom": {
            "base_url": settings.CUSTOM_OPENAI_BASE_URL,
            "default_model": settings.CUSTOM_MODEL
        },
        "ollama": {
            "default_model": settings.DEFAULT_MODEL
        }
    }

    def __init__(self):
        self.active_provider = settings.AI_PROVIDER
        self.active_model = self._get_initial_model(self.active_provider)

    def set_active_provider(self, provider: str, model: Optional[str] = None):
        """Switches active provider and optionally model with validation."""
        valid_providers = ["ollama", "groq", "openrouter", "gemini", "openai", "custom"]
        if provider.lower() not in valid_providers:
            raise ValueError(f"Invalid AI Provider: {provider}. Must be one of {valid_providers}")
        self.set_provider(provider, model)

    def get_status(self) -> Dict[str, Any]:
        """Synchronous provider metadata status dictionary."""
        return {
            "active_provider": self.active_provider,
            "active_model": self.active_model,
            "providers": {
                "ollama": {
                    "configured": True,
                    "online": True,
                    "endpoint": settings.OLLAMA_BASE_URL,
                    "default_model": settings.DEFAULT_MODEL
                },
                "groq": {
                    "configured": bool(settings.GROQ_API_KEY),
                    "model": settings.GROQ_MODEL,
                    "models_cascade": PROVIDER_CASCADES["groq"]
                },
                "openrouter": {
                    "configured": bool(settings.OPENROUTER_API_KEY),
                    "model": settings.OPENROUTER_MODEL,
                    "free_models": PROVIDER_CASCADES["openrouter"]
                },
                "gemini": {
                    "configured": bool(settings.GEMINI_API_KEY),
                    "model": settings.GEMINI_MODEL,
                    "models_cascade": PROVIDER_CASCADES["gemini"]
                },
                "openai": {
                    "configured": bool(settings.OPENAI_API_KEY),
                    "model": settings.OPENAI_MODEL,
                    "default_model": settings.OPENAI_MODEL
                },
                "custom": {
                    "configured": bool(settings.CUSTOM_OPENAI_BASE_URL),
                    "base_url": settings.CUSTOM_OPENAI_BASE_URL,
                    "model": settings.CUSTOM_MODEL,
                    "default_model": settings.CUSTOM_MODEL
                }
            }
        }

    def _get_initial_model(self, provider: str) -> str:
        if provider == "groq": return settings.GROQ_MODEL
        if provider == "openrouter": return settings.OPENROUTER_MODEL
        if provider == "gemini": return settings.GEMINI_MODEL
        if provider == "openai": return settings.OPENAI_MODEL
        if provider == "custom": return settings.CUSTOM_MODEL
        return settings.DEFAULT_MODEL

    def set_provider(self, provider: str, model: Optional[str] = None):
        """Switches active provider and optionally model with persistence."""
        self.active_provider = provider.lower()
        if model:
            self.active_model = model
        else:
            self.active_model = self._get_initial_model(self.active_provider)
            
        settings.update_runtime_setting("AI_PROVIDER", self.active_provider)

    async def get_active_status(self) -> Dict[str, Any]:
        """Returns health telemetry and configuration of all available providers."""
        ollama_online = await ollama_client.is_available()
        return {
            "active_provider": self.active_provider,
            "active_model": self.active_model,
            "providers": {
                "ollama": {
                    "configured": True,
                    "online": ollama_online,
                    "endpoint": settings.OLLAMA_BASE_URL,
                    "default_model": settings.DEFAULT_MODEL
                },
                "groq": {
                    "configured": bool(settings.GROQ_API_KEY),
                    "model": settings.GROQ_MODEL,
                    "models_cascade": PROVIDER_CASCADES["groq"]
                },
                "openrouter": {
                    "configured": bool(settings.OPENROUTER_API_KEY),
                    "model": settings.OPENROUTER_MODEL,
                    "free_models": PROVIDER_CASCADES["openrouter"]
                },
                "gemini": {
                    "configured": bool(settings.GEMINI_API_KEY),
                    "model": settings.GEMINI_MODEL,
                    "models_cascade": PROVIDER_CASCADES["gemini"]
                },
                "openai": {
                    "configured": bool(settings.OPENAI_API_KEY),
                    "model": settings.OPENAI_MODEL
                },
                "custom": {
                    "configured": bool(settings.CUSTOM_OPENAI_BASE_URL),
                    "base_url": settings.CUSTOM_OPENAI_BASE_URL,
                    "model": settings.CUSTOM_MODEL
                }
            }
        }

    async def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> Dict[str, Any]:
        """
        Executes unified chat inference across the active provider with auto-cascading.
        """
        provider = self.active_provider
        
        # 1. Local Ollama execution
        if provider == "ollama" or not self._has_credentials(provider):
            return await self._call_ollama_with_cascade(messages, temperature)

        # 2. Google Gemini execution
        if provider == "gemini":
            return await self._call_gemini_with_cascade(messages, temperature)

        # 3. OpenAI-Compatible Providers (Groq, OpenRouter, OpenAI, Custom)
        return await self._call_openai_compatible_with_cascade(provider, messages, temperature)

    async def chat_stream(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> AsyncGenerator[str, None]:
        """
        Executes streaming chat inference across the active provider with auto-cascading.
        """
        provider = self.active_provider

        # 1. Local Ollama Streaming
        if provider == "ollama" or not self._has_credentials(provider):
            async for chunk in self._stream_ollama(messages, temperature):
                yield chunk
            return

        # 2. OpenAI-Compatible Streaming (Groq, OpenRouter, OpenAI, Custom)
        if provider in ("groq", "openrouter", "openai", "custom"):
            async for chunk in self._stream_openai_compatible(provider, messages, temperature):
                yield chunk
            return

        # 3. Gemini fallback streaming (yield full result)
        res = await self._call_gemini_with_cascade(messages, temperature)
        yield res.get("content", "")

    # ==========================================
    # PROVIDER CALL IMPLEMENTATIONS & CASCADES
    # ==========================================
    def _has_credentials(self, provider: str) -> bool:
        if provider == "groq": return bool(settings.GROQ_API_KEY)
        if provider == "openrouter": return bool(settings.OPENROUTER_API_KEY)
        if provider == "gemini": return bool(settings.GEMINI_API_KEY)
        if provider == "openai": return bool(settings.OPENAI_API_KEY)
        if provider == "custom": return bool(settings.CUSTOM_OPENAI_BASE_URL)
        return True

    async def _call_ollama_with_cascade(self, messages: List[Dict[str, str]], temperature: float) -> Dict[str, Any]:
        """Calls local Ollama with fallback to sibling model."""
        models_to_try = [self.active_model] + [m for m in PROVIDER_CASCADES["ollama"] if m != self.active_model]
        
        for model in models_to_try:
            try:
                res = await ollama_client.chat(messages=messages, model=model, temperature=temperature)
                if model != self.active_model:
                    self._heal_config("ollama", model)
                return res
            except Exception as e:
                logger.warning(f"Ollama model {model} failed: {e}. Cascading...")

        raise RuntimeError("All local Ollama models in cascade failed.")

    async def _stream_ollama(self, messages: List[Dict[str, str]], temperature: float) -> AsyncGenerator[str, None]:
        try:
            async for chunk in ollama_client.chat_stream(messages=messages, model=self.active_model, temperature=temperature):
                yield chunk
        except Exception:
            # Fallback to secondary model
            async for chunk in ollama_client.chat_stream(messages=messages, model=settings.FALLBACK_MODEL, temperature=temperature):
                yield chunk

    async def _call_openai_compatible_with_cascade(self, provider: str, messages: List[Dict[str, str]], temperature: float) -> Dict[str, Any]:
        """Calls OpenAI-compatible endpoints (Groq, OpenRouter, OpenAI, Custom) with cascading."""
        endpoint, api_key = self._get_provider_details(provider)
        cascade_models = [self.active_model] + [m for m in PROVIDER_CASCADES.get(provider, []) if m != self.active_model]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        if provider == "openrouter":
            headers["HTTP-Referer"] = "http://localhost:8005"
            headers["X-Title"] = "SREE Personal AI Assistant"

        async with httpx.AsyncClient(timeout=30.0) as client:
            for model in cascade_models:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature
                }
                try:
                    res = await client.post(endpoint, json=payload, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        content = data["choices"][0]["message"]["content"]
                        if model != self.active_model:
                            self._heal_config(provider, model)
                        return {
                            "model": f"{provider}:{model}",
                            "content": content,
                            "eval_count": data.get("usage", {}).get("total_tokens", 0)
                        }
                    elif res.status_code in (404, 429):
                        logger.warning(f"{provider} returned HTTP {res.status_code} for {model}. Cascading to sibling model...")
                        continue
                    else:
                        logger.error(f"{provider} error HTTP {res.status_code}: {res.text}")
                except Exception as e:
                    logger.warning(f"{provider} request error on {model}: {e}. Cascading...")

        # Ultimate fallback to local Ollama if cloud provider is exhausted
        logger.info(f"Cloud provider {provider} exhausted. Cascading to local Ollama...")
        return await self._call_ollama_with_cascade(messages, temperature)

    async def _stream_openai_compatible(self, provider: str, messages: List[Dict[str, str]], temperature: float) -> AsyncGenerator[str, None]:
        endpoint, api_key = self._get_provider_details(provider)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        if provider == "openrouter":
            headers["HTTP-Referer"] = "http://localhost:8005"
            headers["X-Title"] = "SREE Personal AI Assistant"

        payload = {
            "model": self.active_model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                async with client.stream("POST", endpoint, json=payload, headers=headers) as res:
                    if res.status_code == 200:
                        async for line in res.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:].strip()
                                if data_str == "[DONE]": break
                                try:
                                    chunk_data = json.loads(data_str)
                                    delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content: yield content
                                except Exception:
                                    continue
                        return
                    else:
                        logger.warning(f"Stream error {res.status_code}. Falling back to Ollama stream.")
        except Exception as e:
            logger.warning(f"Streaming error on {provider}: {e}")

        # Stream Ollama fallback
        async for chunk in self._stream_ollama(messages, temperature):
            yield chunk

    async def _call_gemini_with_cascade(self, messages: List[Dict[str, str]], temperature: float) -> Dict[str, Any]:
        """Calls Google Gemini with model cascading."""
        api_key = settings.GEMINI_API_KEY
        cascade_models = [self.active_model] + [m for m in PROVIDER_CASCADES["gemini"] if m != self.active_model]
        
        # Format messages for Gemini
        gemini_contents = []
        for m in messages:
            role = "user" if m["role"] in ("user", "system") else "model"
            gemini_contents.append({
                "role": role,
                "parts": [{"text": m["content"]}]
            })

        async with httpx.AsyncClient(timeout=30.0) as client:
            for model in cascade_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                payload = {
                    "contents": gemini_contents,
                    "generationConfig": {"temperature": temperature}
                }
                try:
                    res = await client.post(url, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        if model != self.active_model:
                            self._heal_config("gemini", model)
                        return {
                            "model": f"gemini:{model}",
                            "content": text,
                            "eval_count": 0
                        }
                    elif res.status_code in (404, 429):
                        logger.warning(f"Gemini {model} returned {res.status_code}. Cascading...")
                        continue
                except Exception as e:
                    logger.warning(f"Gemini {model} error: {e}")

        # Ultimate fallback
        return await self._call_ollama_with_cascade(messages, temperature)

    def _get_provider_details(self, provider: str) -> tuple[str, str]:
        if provider == "groq":
            return PROVIDER_ENDPOINTS["groq"], settings.GROQ_API_KEY
        if provider == "openrouter":
            return PROVIDER_ENDPOINTS["openrouter"], settings.OPENROUTER_API_KEY
        if provider == "openai":
            return PROVIDER_ENDPOINTS["openai"], settings.OPENAI_API_KEY
        if provider == "custom":
            base = settings.CUSTOM_OPENAI_BASE_URL.rstrip("/")
            endpoint = f"{base}/chat/completions" if not base.endswith("/chat/completions") else base
            return endpoint, settings.CUSTOM_OPENAI_API_KEY
        return "", ""

    def _heal_config(self, provider: str, healed_model: str):
        """
        Autonomous Configuration Healing:
        Persists newly verified model to active settings and .env.
        """
        logger.info(f"[AUTONOMOUS HEALING] Updating active model from {self.active_model} to {healed_model} on {provider}")
        self.active_model = healed_model
        setting_key = f"{provider.upper()}_MODEL" if provider != "ollama" else "DEFAULT_MODEL"
        settings.update_runtime_setting(setting_key, healed_model)

universal_router = UniversalAIRouter()
