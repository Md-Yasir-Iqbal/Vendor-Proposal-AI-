"""
Central application configuration.

Reads all runtime configuration from environment variables (via a local .env
file if present). Nothing sensitive is ever hard-coded here.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env once, from the project root, if it exists.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=_PROJECT_ROOT / ".env", override=False)


def _get_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None or val.strip() == "":
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    val = os.getenv(name)
    if val is None or val.strip() == "":
        return default
    try:
        return float(val)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    # --- Groq / LLM configuration -------------------------------------------------
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", "").strip())
    groq_model: str = field(default_factory=lambda: os.getenv("GROQ_MODEL", "").strip())
    groq_timeout_seconds: float = field(default_factory=lambda: _get_float("GROQ_TIMEOUT_SECONDS", 45.0))
    groq_max_retries: int = field(default_factory=lambda: _get_int("GROQ_MAX_RETRIES", 2))

    # --- Document processing -------------------------------------------------------
    max_extraction_chars: int = field(default_factory=lambda: _get_int("MAX_EXTRACTION_CHARS", 16000))
    chunk_max_chars: int = field(default_factory=lambda: _get_int("CHUNK_MAX_CHARS", 1200))
    chunk_overlap_chars: int = field(default_factory=lambda: _get_int("CHUNK_OVERLAP_CHARS", 150))

    # --- Retrieval -------------------------------------------------------------------
    chroma_persist_dir: str = field(
        default_factory=lambda: os.getenv("CHROMA_PERSIST_DIR", str(_PROJECT_ROOT / "data" / "chroma"))
    )
    chroma_collection_name: str = field(
        default_factory=lambda: os.getenv("CHROMA_COLLECTION_NAME", "vendor_proposals")
    )
    retrieval_top_k: int = field(default_factory=lambda: _get_int("RETRIEVAL_TOP_K", 4))

    # --- App -------------------------------------------------------------------------
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    def is_groq_configured(self) -> bool:
        return bool(self.groq_api_key) and bool(self.groq_model)


def get_settings() -> Settings:
    """Return a fresh Settings instance (cheap; safe to call repeatedly)."""
    return Settings()
