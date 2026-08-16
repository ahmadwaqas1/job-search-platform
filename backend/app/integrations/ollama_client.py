"""Thin wrapper around Ollama's REST API. Every LLM/embedding call in the
app - CV extraction, match explanations, cover-letter/answer drafting, and
the copilot chat - goes through this one module, so swapping models or
tweaking prompt-format handling only ever needs to happen in one place.

Uses raw httpx rather than the `ollama` PyPI package: httpx is already a
dependency for the job-source/salary API integrations, this keeps full
control over streaming/timeouts/structured-output params, and it keeps the
door open to pointing OLLAMA_BASE_URL at any OpenAI-compatible local
server later.
"""
from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

settings = get_settings()


class OllamaError(Exception):
    pass


class OllamaClient:
    def __init__(self, base_url: str | None = None, timeout: int | None = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.timeout = timeout or settings.ollama_request_timeout_seconds

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        json_schema: dict[str, Any] | None = None,
        temperature: float = 0.3,
    ) -> str:
        """Single-shot chat completion. Pass `json_schema` (a JSON Schema
        dict) to grammar-constrain the model's output via Ollama's
        structured-output `format` parameter - use with generate_json()
        below rather than calling this directly when you need JSON back.
        """
        payload: dict[str, Any] = {
            "model": model or settings.ollama_chat_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if json_schema is not None:
            payload["format"] = json_schema

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise OllamaError(f"Ollama chat request failed: {exc}") from exc

        data = resp.json()
        return data.get("message", {}).get("content", "")

    async def chat_stream(
        self, messages: list[dict[str, str]], model: str | None = None, temperature: float = 0.5
    ) -> AsyncIterator[str]:
        """Yields response text chunks as they arrive, for the copilot chat UI."""
        payload = {
            "model": model or settings.ollama_chat_model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": temperature},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if chunk.get("done"):
                            break
            except httpx.HTTPError as exc:
                raise OllamaError(f"Ollama chat stream failed: {exc}") from exc

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def embed(self, text: str, model: str | None = None) -> list[float]:
        payload = {"model": model or settings.ollama_embed_model, "input": text}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(f"{self.base_url}/api/embed", json=payload)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise OllamaError(f"Ollama embed request failed: {exc}") from exc

        data = resp.json()
        embeddings = data.get("embeddings")
        if not embeddings:
            raise OllamaError(f"Ollama embed response missing 'embeddings': {data}")
        return embeddings[0]

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any],
        model: str | None = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """Chat call constrained to a JSON schema, with one automatic
        repair round-trip if the model's output fails to parse/validate.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        raw = await self.chat(messages, model=model, json_schema=json_schema, temperature=temperature)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            repair_messages = messages + [
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": (
                        "That was not valid JSON matching the required schema. "
                        "Respond again with ONLY valid JSON matching the schema, no other text."
                    ),
                },
            ]
            raw_retry = await self.chat(
                repair_messages, model=model, json_schema=json_schema, temperature=0.0
            )
            try:
                return json.loads(raw_retry)
            except json.JSONDecodeError as exc:
                raise OllamaError(f"Model did not return valid JSON after retry: {raw_retry[:500]}") from exc


def get_ollama_client() -> OllamaClient:
    return OllamaClient()
