"""The only module that talks to AI providers. Failures become AIUnavailable with a plain-language message.

Nothing from a request (rows, errors, questions) or the key is ever written to the logs.
"""
from __future__ import annotations

import json
import logging
import os
import ssl
from typing import Any, Dict, List

import httpx
from openai import OpenAI

from .config import Settings

log = logging.getLogger("reportpulse.llm")


class AIUnavailable(Exception):
    def __init__(self, code: str, message: str, status: int = 503):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


_FRIENDLY = {
    "AuthenticationError": ("auth", "{provider} rejected the API key. Check that it is correct and not revoked."),
    "PermissionDeniedError": ("permission", "The key is valid but is not allowed to use this model. Ask who manages the key."),
    "NotFoundError": ("model", "{provider} says this model is unavailable. Check the provider's model access and backend model setting."),
    "RateLimitError": ("rate_limit", "{provider} is receiving too many requests from this key right now. Wait a minute and try again, one finding at a time."),
    "APIConnectionError": ("network", "Could not reach {provider}. The network or a proxy may be blocking it."),
    "APITimeoutError": ("timeout", "{provider} took too long to answer. Try again."),
}


def _wrap(e: Exception, provider: str = "OpenAI") -> AIUnavailable:
    name = type(e).__name__
    if name == "RateLimitError" and getattr(e, "code", None) == "insufficient_quota":
        log.warning("%s call failed: insufficient_quota", provider)
        return AIUnavailable("quota", f"{provider} reports no available credit or a reached spend limit. Check Billing and usage limits.")
    code, message = _FRIENDLY.get(name, ("error", f"{provider} returned an unexpected error ({name})."))
    log.warning("%s call failed: %s", provider, name)  # the error name only
    return AIUnavailable(code, message.format(provider=provider))


def _client(s: Settings) -> OpenAI:
    client_options: Dict[str, Any] = {
        "api_key": s.api_key,
        "timeout": s.request_timeout,
        "max_retries": 1,
    }
    if s.ai_provider == "groq":
        client_options["base_url"] = s.groq_base_url
    if os.name == "nt":
        client_options["http_client"] = httpx.Client(
            verify=ssl.create_default_context(),
            timeout=s.request_timeout,
        )
    return OpenAI(**client_options)


def _require(s: Settings) -> None:
    if not s.ai_enabled:
        raise AIUnavailable("no_key", f"The {s.provider_name} key is not set on the backend. Add {s.key_env_name} to backend/.env and restart the backend.")


def _extra(s: Settings) -> Dict[str, Any]:
    return {} if s.temperature is None else {"temperature": s.temperature}


def _gemini_generate(s: Settings, system: str, user: str, json_mode: bool) -> str:
    payload: Dict[str, Any] = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
    }
    generation_config: Dict[str, Any] = {}
    if json_mode:
        generation_config["responseMimeType"] = "application/json"
    if s.temperature is not None:
        generation_config["temperature"] = s.temperature
    if generation_config:
        payload["generationConfig"] = generation_config

    url = f"{s.gemini_base_url.rstrip('/')}/models/{s.model}:generateContent"
    try:
        with httpx.Client(verify=ssl.create_default_context(), timeout=s.request_timeout) as client:
            response = client.post(url, headers={"x-goog-api-key": s.api_key}, json=payload)
        if response.status_code == 401:
            raise AIUnavailable("auth", "Gemini rejected the API key. Check that it is active and allowed to use the Gemini API.")
        if response.status_code == 403:
            raise AIUnavailable("permission", "Gemini denied access. Check the key's API restrictions and project permissions.")
        if response.status_code == 404:
            raise AIUnavailable("model", "Gemini could not find this model for the selected API. Set GEMINI_MODEL to a model available to your key.")
        if response.status_code == 429:
            raise AIUnavailable("rate_limit", "Gemini is rate limiting this key or project. Check its quota and try again later.")
        if response.status_code == 503:
            raise AIUnavailable("unavailable", "This Gemini model is temporarily overloaded. Try again shortly or select another available model.")
        if not response.is_success:
            log.warning("Gemini request failed: HTTP %d", response.status_code)
            raise AIUnavailable("error", f"Gemini rejected the request (HTTP {response.status_code}). Check the model and request settings.")
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        if not text:
            raise AIUnavailable("bad_answer", "Gemini returned an empty answer. Try again.")
        return text
    except AIUnavailable:
        raise
    except httpx.TimeoutException:
        raise AIUnavailable("timeout", "Gemini took too long to answer. Try again.")
    except httpx.TransportError as e:
        log.warning("Gemini request failed: %s", type(e).__name__)
        raise AIUnavailable("network", "Could not reach Gemini. Check the network or proxy.")
    except (ValueError, KeyError, IndexError, TypeError):
        raise AIUnavailable("bad_answer", "Gemini returned an answer in an unexpected format. Try again.")


def chat_json(s: Settings, system: str, user: str) -> Dict[str, Any]:
    _require(s)
    try:
        if s.ai_provider == "gemini":
            data = json.loads(_gemini_generate(s, system, user, json_mode=True))
            if not isinstance(data, dict):
                raise ValueError("not an object")
            return data
        res = _client(s).chat.completions.create(
            model=s.model, response_format={"type": "json_object"}, **_extra(s),
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        data = json.loads(res.choices[0].message.content)
        if not isinstance(data, dict):
            raise ValueError("not an object")
        return data
    except (ValueError, TypeError):
        raise AIUnavailable("bad_answer", "The AI provider returned an answer in an unexpected format. Try again.")
    except Exception as e:  # noqa: BLE001
        raise _wrap(e, s.provider_name)


def chat_text(s: Settings, system: str, user: str) -> str:
    _require(s)
    try:
        if s.ai_provider == "gemini":
            return _gemini_generate(s, system, user, json_mode=False)
        res = _client(s).chat.completions.create(
            model=s.model, **_extra(s),
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        text = (res.choices[0].message.content or "").strip()
        if not text:
            raise ValueError("empty")
        return text
    except ValueError:
        raise AIUnavailable("bad_answer", "The AI provider returned an empty answer. Try again.")
    except Exception as e:  # noqa: BLE001
        raise _wrap(e, s.provider_name)


def embed(s: Settings, texts: List[str]) -> List[List[float]]:
    _require(s)
    if not s.embeddings_enabled:
        raise AIUnavailable("model", "Semantic embeddings are unavailable with the selected provider; keyword search is used instead.")
    try:
        res = _client(s).embeddings.create(model=s.embedding_model, input=texts)
        return [d.embedding for d in res.data]
    except Exception as e:  # noqa: BLE001
        raise _wrap(e, s.provider_name)
