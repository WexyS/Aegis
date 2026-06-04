import logging
import httpx
import time
import asyncio
from typing import Any

from aegis.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMProvider:
    """Handles communication with LLM backends with routing to specialized models."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.backend = self.settings.models.backend
        self.base_url = self.settings.models.base_url
        self.timeout = self.settings.models.timeout
        self.max_retries = 2

    def _resolve_model(self, model_type: str) -> str:
        """Map model_type to the actual model name from settings."""
        if model_type == "code":
            return self.settings.models.code_model
        if model_type == "chat":
            return self.settings.models.chat_model
        return self.settings.models.default_model

    async def generate(self, prompt: str, system_prompt: str | None = None, model_type: str = "default") -> str:
        """Generate text from the LLM with retry mechanism and model routing."""
        if not self.settings.models.model_calls_authorized:
            logger.warning("[LLM] Model call denied; config is metadata-only and not execution permission.")
            return ""

        model = self._resolve_model(model_type)
        
        if self.backend == "ollama":
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            }
        else:  # lm-studio or openai-compatible
            url = f"{self.base_url}/chat/completions"
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.1,
                "stream": False
            }

        for attempt in range(self.max_retries + 1):
            start_time = time.time()
            try:
                logger.info("[LLM] Attempt %d: %s | Model: %s | Backend: %s", attempt + 1, url, model, self.backend)
                
                async with httpx.AsyncClient(timeout=self.timeout, trust_env=False) as client:
                    response = await client.post(url, json=payload)
                    duration = time.time() - start_time
                    
                    logger.info("[LLM] Status: %d | Time: %.2fs", response.status_code, duration)
                    response.raise_for_status()
                    
                    data = response.json()
                    if self.backend == "ollama":
                        return data.get("response", "").strip()
                    else:
                        return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                duration = time.time() - start_time
                logger.warning("[LLM] Attempt %d failed (%.2fs): %s", attempt + 1, duration, e)
                if attempt < self.max_retries:
                    await asyncio.sleep(1.0) # Wait before retry
                    continue
            except Exception as e:
                logger.error("[LLM] Unexpected error: %s", e)
                break

        return ""

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings using the specialized embedding model."""
        if not self.settings.models.embedding_generation_authorized:
            logger.warning("[LLM-EMBED] Embedding denied; config is metadata-only and not permission.")
            return []

        model = self.settings.models.embed_model
        
        if self.backend == "ollama":
            url = f"{self.base_url}/api/embeddings"
            payload = {"model": model, "prompt": text}
        else:
            url = f"{self.base_url}/embeddings"
            payload = {"model": model, "input": text}

        try:
            async with httpx.AsyncClient(timeout=5.0, trust_env=False) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                if self.backend == "ollama":
                    return data.get("embedding", [])
                else:
                    return data.get("data", [{}])[0].get("embedding", [])
        except Exception as e:
            logger.error("[LLM-EMBED] Failed to generate embedding: %s", e)
            return []


# Singleton
_llm: LLMProvider | None = None

def get_llm() -> LLMProvider:
    global _llm
    if _llm is None:
        _llm = LLMProvider()
    return _llm
