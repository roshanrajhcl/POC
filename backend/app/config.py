"""Settings, read from environment variables.

Provider keys live in backend/.env (or the file named by ENV_FILE). That file is never committed
and is left out of the zip made by scripts/make_zip.ps1.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

log = logging.getLogger("reportpulse.config")
BACKEND_DIR = Path(__file__).resolve().parent.parent


def _load_env_file() -> None:
    explicit = os.environ.get("ENV_FILE")
    path = Path(explicit) if explicit else BACKEND_DIR / ".env"
    if not path.is_file():
        return
    load_dotenv(path)
    if "onedrive" in str(path).lower():
        log.warning("The env file is inside OneDrive, so the key may sync to the cloud. "
                    "Keep it outside OneDrive and set ENV_FILE to its path.")


_load_env_file()


@dataclass(frozen=True)
class Settings:
    ai_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    embedding_model: str = "text-embedding-3-small"
    request_timeout: float = 45.0
    temperature: Optional[float] = None     # unset by default: some models only allow their default
    max_rounds: int = 4                      # suggestions before the assistant escalates
    top_k: int = 6                           # excerpts passed to the model
    min_cosine: float = 0.28                 # embedding similarity needed to count as relevant
    min_coverage: float = 0.30               # keyword coverage needed to count as relevant
    knowledge_dir: Path = BACKEND_DIR / "knowledge"
    data_dir: Path = BACKEND_DIR / "data"

    @property
    def ai_enabled(self) -> bool:
        return bool(self.api_key)

    @property
    def api_key(self) -> str:
        if self.ai_provider == "groq":
            return self.groq_api_key
        if self.ai_provider == "gemini":
            return self.gemini_api_key
        return self.openai_api_key

    @property
    def provider_name(self) -> str:
        return {"groq": "Groq", "gemini": "Gemini", "openai": "OpenAI"}[self.ai_provider]

    @property
    def key_env_name(self) -> str:
        return {"groq": "GROQ_API_KEY", "gemini": "GEMINI_API_KEY", "openai": "OPENAI_API_KEY"}[self.ai_provider]

    @property
    def model(self) -> str:
        return {"groq": self.groq_model, "gemini": self.gemini_model, "openai": self.openai_model}[self.ai_provider]

    @property
    def embeddings_enabled(self) -> bool:
        return self.ai_provider == "openai" and self.ai_enabled

    def __repr__(self) -> str:  # never let the key reach a log or traceback
        embeddings = self.embedding_model if self.embeddings_enabled else None
        return f"Settings(provider={self.provider_name!r}, model={self.model!r}, embeddings={embeddings!r}, ai_enabled={self.ai_enabled})"


def _float(name: str, default: Optional[float]) -> Optional[float]:
    raw = os.environ.get(name, "").strip()
    return float(raw) if raw else default


def load_settings() -> Settings:
    d = Settings()
    provider = os.environ.get("AI_PROVIDER", d.ai_provider).strip().lower()
    if provider not in {"openai", "groq", "gemini"}:
        raise ValueError("AI_PROVIDER must be 'openai', 'groq', or 'gemini'.")
    return Settings(
        ai_provider=provider,
        openai_api_key=os.environ.get("OPENAI_API_KEY", "").strip(),
        openai_model=os.environ.get("OPENAI_MODEL", d.openai_model).strip(),
        groq_api_key=os.environ.get("GROQ_API_KEY", "").strip(),
        groq_model=os.environ.get("GROQ_MODEL", d.groq_model).strip(),
        groq_base_url=os.environ.get("GROQ_BASE_URL", d.groq_base_url).strip(),
        gemini_api_key=os.environ.get("GEMINI_API_KEY", "").strip(),
        gemini_model=os.environ.get("GEMINI_MODEL", d.gemini_model).strip(),
        gemini_base_url=os.environ.get("GEMINI_BASE_URL", d.gemini_base_url).strip(),
        embedding_model=os.environ.get("OPENAI_EMBEDDING_MODEL", d.embedding_model).strip(),
        request_timeout=_float("AI_TIMEOUT", _float("OPENAI_TIMEOUT", d.request_timeout)),
        temperature=_float("OPENAI_TEMPERATURE", None),
        max_rounds=int(os.environ.get("MAX_ROUNDS", d.max_rounds)),
        top_k=int(os.environ.get("RAG_TOP_K", d.top_k)),
        min_cosine=_float("RAG_MIN_COSINE", d.min_cosine),
        min_coverage=_float("RAG_MIN_COVERAGE", d.min_coverage),
    )
