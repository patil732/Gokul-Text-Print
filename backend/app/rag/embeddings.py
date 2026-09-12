"""
app/rag/embeddings.py
----------------------
Sprint 4 Step 3 — RAG Knowledge Engine

Configurable embedding backend with three interchangeable providers:
  - sentence_transformers  (offline, no API key required)
  - openai                 (requires OPENAI_API_KEY)
  - gemini                 (requires GEMINI_API_KEY)

Provider selection is driven entirely by ``config/model_config.yaml`` under the
``rag.embedding.provider`` key — the same ``load_config()`` pattern used by the
Sprint 1/2 ML pipelines.  Switching provider requires only a one-line YAML edit.

Public API
----------
    from app.rag.embeddings import embed, embed_batch, get_provider

    vector  = embed("Hello world")              # list[float]
    vectors = embed_batch(["text A", "text B"]) # list[list[float]]

Internal architecture
---------------------
    EmbeddingProvider   — abstract base class
    SentenceTransformerProvider
    OpenAIProvider
    GeminiProvider
    get_provider()      — singleton factory; reads YAML, lazy-imports library
    embed()             — module-level wrapper → get_provider().embed()
    embed_batch()       — module-level wrapper → get_provider().embed_batch()

Design notes
------------
- Every library is lazy-imported so the application starts successfully even
  when none of the optional packages are installed.
- ``get_provider()`` is cached at module level (``_PROVIDER_SINGLETON``).
  Call ``reset_provider()`` in tests to force re-instantiation with a mock.
- The active provider name and model are logged at INFO level on first use.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

# --------------------------------------------------------------------------- #
# Project root on sys.path
# --------------------------------------------------------------------------- #
_THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from utils.logger import logger  # noqa: E402

# Reuse the same YAML loader used throughout the ML pipelines
from app.ml.common.model_loader import load_config  # noqa: E402

_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config", "model_config.yaml")


# --------------------------------------------------------------------------- #
# Configuration dataclass
# --------------------------------------------------------------------------- #

@dataclass
class EmbeddingConfig:
    """Resolved embedding settings parsed from model_config.yaml."""

    provider:   str = "sentence_transformers"
    model:      str = "all-MiniLM-L6-v2"
    dimension:  int = 384
    batch_size: int = 32
    api_key:    str = ""


def _resolve_config(config_path: str = _CONFIG_PATH) -> EmbeddingConfig:
    """
    Parse the ``rag`` section of model_config.yaml and return an
    ``EmbeddingConfig`` instance for the active provider.
    """
    raw   = load_config(config_path)
    rag   = raw.get("rag", {})
    emb   = rag.get("embedding", {})
    provs = rag.get("providers", {})

    provider   = emb.get("provider", "sentence_transformers").lower()
    batch_size = int(emb.get("batch_size", 32))

    prov_cfg   = provs.get(provider, {})
    model      = prov_cfg.get("model", "all-MiniLM-L6-v2")
    dimension  = int(prov_cfg.get("dimension", 384))

    # Resolve optional API key from environment
    api_key_env = prov_cfg.get("api_key_env", "")
    api_key     = os.getenv(api_key_env, "") if api_key_env else ""

    return EmbeddingConfig(
        provider=provider,
        model=model,
        dimension=dimension,
        batch_size=batch_size,
        api_key=api_key,
    )


# --------------------------------------------------------------------------- #
# Abstract base
# --------------------------------------------------------------------------- #

class EmbeddingProvider(ABC):
    """Abstract interface that all provider implementations must satisfy."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Return a dense vector for a single text string."""

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return a list of dense vectors, one per input text."""


# --------------------------------------------------------------------------- #
# Concrete providers
# --------------------------------------------------------------------------- #

class SentenceTransformerProvider(EmbeddingProvider):
    """
    Embedding provider backed by ``sentence-transformers`` (offline).

    The model is downloaded on first use and cached by the library.
    """

    def __init__(self, cfg: EmbeddingConfig) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required for this provider. "
                "Install it with: pip install sentence-transformers"
            ) from exc
        logger.info(
            f"[embeddings] SentenceTransformer initialising model '{cfg.model}'"
        )
        self._model = SentenceTransformer(cfg.model)
        self._cfg   = cfg

    def embed(self, text: str) -> list[float]:
        vector = self._model.encode(text, convert_to_numpy=True)
        return vector.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(texts, convert_to_numpy=True, batch_size=self._cfg.batch_size)
        return [v.tolist() for v in vectors]


class OpenAIProvider(EmbeddingProvider):
    """
    Embedding provider backed by the OpenAI Embeddings API.

    Requires ``OPENAI_API_KEY`` (or the configured env var) to be set.
    """

    def __init__(self, cfg: EmbeddingConfig) -> None:
        try:
            import openai as _openai
        except ImportError as exc:
            raise ImportError(
                "openai is required for this provider. "
                "Install it with: pip install openai"
            ) from exc

        if not cfg.api_key:
            raise ValueError(
                "[embeddings] OpenAI provider requires an API key. "
                "Set OPENAI_API_KEY in your .env file."
            )
        self._client = _openai.OpenAI(api_key=cfg.api_key)
        self._cfg    = cfg
        logger.info(f"[embeddings] OpenAI provider initialised (model='{cfg.model}')")

    def embed(self, text: str) -> list[float]:
        response = self._client.embeddings.create(
            input=text,
            model=self._cfg.model,
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.embeddings.create(
            input=texts,
            model=self._cfg.model,
        )
        # API guarantees order matches input order
        return [item.embedding for item in response.data]


class GeminiProvider(EmbeddingProvider):
    """
    Embedding provider backed by the Google Gemini Embeddings API.

    Requires ``GEMINI_API_KEY`` (or the configured env var) to be set.
    """

    def __init__(self, cfg: EmbeddingConfig) -> None:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise ImportError(
                "google-generativeai is required for this provider. "
                "Install it with: pip install google-generativeai"
            ) from exc

        if not cfg.api_key:
            raise ValueError(
                "[embeddings] Gemini provider requires an API key. "
                "Set GEMINI_API_KEY in your .env file."
            )
        genai.configure(api_key=cfg.api_key)
        self._genai = genai
        self._cfg   = cfg
        logger.info(f"[embeddings] Gemini provider initialised (model='{cfg.model}')")

    def embed(self, text: str) -> list[float]:
        result = self._genai.embed_content(
            model=self._cfg.model,
            content=text,
            task_type="retrieval_document",
        )
        return result["embedding"]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return [self.embed(t) for t in texts]


# --------------------------------------------------------------------------- #
# Provider registry
# --------------------------------------------------------------------------- #

_PROVIDER_REGISTRY: dict[str, type[EmbeddingProvider]] = {
    "sentence_transformers": SentenceTransformerProvider,
    "openai":                OpenAIProvider,
    "gemini":                GeminiProvider,
}

# Module-level singleton — initialised on first call to get_provider()
_PROVIDER_SINGLETON: EmbeddingProvider | None = None


# --------------------------------------------------------------------------- #
# Factory & module-level helpers
# --------------------------------------------------------------------------- #

def get_provider(config_path: str = _CONFIG_PATH) -> EmbeddingProvider:
    """
    Return the active ``EmbeddingProvider`` singleton.

    The provider is instantiated once from the YAML config and cached.
    Subsequent calls return the cached instance without re-reading the file.

    Parameters
    ----------
    config_path : str
        Path to ``model_config.yaml``.  Override in tests via
        ``monkeypatch`` or by calling ``reset_provider()`` first.

    Raises
    ------
    ValueError
        If ``rag.embedding.provider`` names an unknown provider.
    """
    global _PROVIDER_SINGLETON
    if _PROVIDER_SINGLETON is not None:
        return _PROVIDER_SINGLETON

    cfg      = _resolve_config(config_path)
    prov_cls = _PROVIDER_REGISTRY.get(cfg.provider)

    if prov_cls is None:
        raise ValueError(
            f"[embeddings] Unknown provider '{cfg.provider}'. "
            f"Valid options: {list(_PROVIDER_REGISTRY)}"
        )

    logger.info(
        f"[embeddings] Creating provider '{cfg.provider}' "
        f"(model='{cfg.model}', batch_size={cfg.batch_size})"
    )
    _PROVIDER_SINGLETON = prov_cls(cfg)
    return _PROVIDER_SINGLETON


def reset_provider() -> None:
    """
    Clear the cached provider singleton.

    Call this in test teardown or when you need to force re-initialisation
    (e.g. after monkeypatching the config).
    """
    global _PROVIDER_SINGLETON
    _PROVIDER_SINGLETON = None


def set_provider(provider: EmbeddingProvider) -> None:
    """
    Directly inject a provider instance (used in unit tests to avoid
    loading real models or hitting live APIs).
    """
    global _PROVIDER_SINGLETON
    _PROVIDER_SINGLETON = provider


def embed(text: str) -> list[float]:
    """
    Embed a single text string using the active provider.

    Parameters
    ----------
    text : str
        The text to embed.

    Returns
    -------
    list[float]
        Dense embedding vector.
    """
    return get_provider().embed(text)


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of text strings using the active provider.

    Parameters
    ----------
    texts : list[str]
        The texts to embed.

    Returns
    -------
    list[list[float]]
        One vector per input text, in the same order.
    """
    return get_provider().embed_batch(texts)
