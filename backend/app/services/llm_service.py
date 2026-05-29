"""Local-only LLM client (Ollama) with offline-safe fallbacks.

The HTTP surface is intentionally tiny. Higher-level prompt construction lives
in `RecommendationService` and `ChatService`.
"""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.utils.text import extract_json_block


logger = get_logger(__name__)


class LLMUnavailable(RuntimeError):
    """Raised by callers that can't tolerate the LLM being missing."""


class LLMService:
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.llm_model
        self.timeout = httpx.Timeout(settings.llm_timeout_seconds, connect=5.0)

    async def ping(self) -> dict:
        """Return ``{ok, model, base_url, models}`` without raising."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                r.raise_for_status()
                tags = r.json().get("models", [])
                return {
                    "ok": True,
                    "model": self.model,
                    "base_url": self.base_url,
                    "models": [t.get("name") for t in tags if isinstance(t, dict)],
                }
        except Exception as exc:  # noqa: BLE001
            logger.info("LLM ping failed: %s", exc)
            return {"ok": False, "model": self.model, "base_url": self.base_url, "error": str(exc)}

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        """Single-shot generation. Raises :class:`LLMUnavailable` on failure."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": settings.llm_max_tokens, "temperature": 0.2},
        }
        if system:
            payload["system"] = system
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(f"{self.base_url}/api/generate", json=payload)
                r.raise_for_status()
                data = r.json()
                return str(data.get("response", "")).strip()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("LLM generate failed: %s", exc)
            raise LLMUnavailable(str(exc)) from exc

    async def stream(self, prompt: str, *, system: str | None = None) -> AsyncIterator[str]:
        """Yield text chunks from Ollama's streaming endpoint."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {"num_predict": settings.llm_max_tokens, "temperature": 0.3},
        }
        if system:
            payload["system"] = system
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as r:
                    r.raise_for_status()
                    async for line in r.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        piece = chunk.get("response")
                        if piece:
                            yield piece
                        if chunk.get("done"):
                            break
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM stream failed: %s", exc)
            raise LLMUnavailable(str(exc)) from exc

    async def generate_json(self, prompt: str, schema_hint: str = "") -> dict:
        """Generate text and best-effort coerce it to JSON.

        Raises :class:`LLMUnavailable` if the model itself is unreachable.
        Returns an empty dict if the model produced no parseable JSON.
        """
        instruction = (
            "Respond with ONLY a valid JSON object. No prose, no markdown, no code fences."
            + (f" The JSON must follow this shape: {schema_hint}" if schema_hint else "")
        )
        text = await self.generate(f"{instruction}\n\n{prompt}")
        parsed = extract_json_block(text)
        return parsed if isinstance(parsed, dict) else {}


llm_service = LLMService()
