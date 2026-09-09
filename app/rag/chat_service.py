"""
app/rag/chat_service.py
------------------------
Sprint 4 Step 5 — RAG Chat Service

Orchestrates the full RAG chat flow:
  question → retriever → prompt_builder → LLM → {answer, sources}

Provider pattern
----------------
Identical to app/rag/embeddings.py (Sprint 4 Step 3):
- Abstract ``ChatProvider`` base class.
- Concrete ``GeminiChatProvider`` and ``OpenAIChatProvider``.
- ``get_chat_provider()``   — cached singleton, reads from model_config.yaml.
- ``set_chat_provider()``   — inject a test double (no real API needed in tests).
- ``reset_chat_provider()`` — clear the singleton in test teardown.

Isolation guarantee
-------------------
This module imports ONLY from ``app/rag/`` and stdlib/config.
It has zero dependency on ``app/ml/`` (Sales / Inventory).

Public API
----------
    from app.rag.chat_service import chat

    result = chat("What triggers a purchase order?")
    # {
    #   "answer":  "A purchase order is triggered when ...",
    #   "sources": [
    #     {"document": "Inventory Policy.pdf", "page": 3},
    #     {"document": "SOP.pdf",              "page": 1},
    #   ]
    # }
"""

from __future__ import annotations

import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

# --------------------------------------------------------------------------- #
# Project root on sys.path
# --------------------------------------------------------------------------- #
_THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from utils.logger import logger  # noqa: E402
from app.ml.common.model_loader import load_config  # noqa: E402
from app.rag.retriever     import retrieve           # noqa: E402
from app.rag.prompt_builder import (                 # noqa: E402
    build_prompt,
    extract_sources,
)
from app.rag.chat_history import save_chat_turn       # noqa: E402

_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config", "model_config.yaml")


# --------------------------------------------------------------------------- #
# Config helper
# --------------------------------------------------------------------------- #

@dataclass
class ChatConfig:
    """Resolved chat settings parsed from model_config.yaml."""
    provider:    str   = "gemini"
    model:       str   = "gemini-1.5-flash"
    api_key:     str   = ""
    top_k:       int   = 5
    max_tokens:  int   = 1024
    temperature: float = 0.2


def _resolve_chat_config(config_path: str = _CONFIG_PATH) -> ChatConfig:
    raw      = load_config(config_path)
    rag      = raw.get("rag", {})
    chat_cfg = rag.get("chat", {})
    provs    = rag.get("chat_providers", {})

    provider    = chat_cfg.get("provider", "gemini").lower()
    top_k       = int(chat_cfg.get("top_k", 5))
    max_tokens  = int(chat_cfg.get("max_tokens", 1024))
    temperature = float(chat_cfg.get("temperature", 0.2))

    prov_cfg    = provs.get(provider, {})
    model       = prov_cfg.get("model", "gemini-1.5-flash")
    api_key_env = prov_cfg.get("api_key_env", "")
    api_key     = os.getenv(api_key_env, "") if api_key_env else ""

    return ChatConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        top_k=top_k,
        max_tokens=max_tokens,
        temperature=temperature,
    )


# --------------------------------------------------------------------------- #
# Abstract provider base
# --------------------------------------------------------------------------- #

class ChatProvider(ABC):
    """Abstract interface for all LLM chat providers."""

    @abstractmethod
    def complete(self, system_prompt: str, user_message: str) -> str:
        """
        Send a chat completion request and return the response text.

        Parameters
        ----------
        system_prompt : str
            Instructions that frame how the model should behave.
        user_message : str
            The context block + question assembled by prompt_builder.

        Returns
        -------
        str
            The model's generated answer text.
        """


# --------------------------------------------------------------------------- #
# Concrete providers
# --------------------------------------------------------------------------- #

class GeminiChatProvider(ChatProvider):
    """
    LLM provider backed by Google Gemini (google-generativeai).

    Requires ``GEMINI_API_KEY`` (or the configured env var) to be set.
    """

    def __init__(self, cfg: ChatConfig) -> None:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise ImportError(
                "google-generativeai is required for the Gemini chat provider. "
                "Install it with: pip install google-generativeai"
            ) from exc

        if not cfg.api_key:
            raise ValueError(
                "[chat_service] Gemini provider requires an API key. "
                "Set GEMINI_API_KEY in your .env file."
            )

        genai.configure(api_key=cfg.api_key)
        self._model = genai.GenerativeModel(
            model_name=cfg.model,
            system_instruction=None,   # injected per-call via contents
        )
        self._cfg   = cfg
        logger.info(f"[chat_service] Gemini provider initialised (model={cfg.model})")

    def complete(self, system_prompt: str, user_message: str) -> str:
        import google.generativeai as genai

        generation_config = genai.GenerationConfig(
            max_output_tokens=self._cfg.max_tokens,
            temperature=self._cfg.temperature,
        )
        # Gemini multi-turn: system goes in as first "user" turn with role context
        contents = [
            {"role": "user",  "parts": [system_prompt]},
            {"role": "model", "parts": ["Understood. I will answer using only the provided context and cite sources as instructed."]},
            {"role": "user",  "parts": [user_message]},
        ]
        try:
            response = self._model.generate_content(
                contents,
                generation_config=generation_config,
            )
            return response.text.strip()
        except Exception as exc:
            # If the requested model is not found or deprecated, fall back to gemini-flash-latest
            if "404" in str(exc) or "not found" in str(exc).lower():
                logger.warning(
                    f"[chat_service] Model '{self._cfg.model}' not found ({exc}). "
                    f"Falling back to 'gemini-flash-latest'."
                )
                self._model = genai.GenerativeModel("gemini-flash-latest")
                response = self._model.generate_content(
                    contents,
                    generation_config=generation_config,
                )
                return response.text.strip()
            raise


class OpenAIChatProvider(ChatProvider):
    """
    LLM provider backed by the OpenAI Chat Completions API.

    Requires ``OPENAI_API_KEY`` (or the configured env var) to be set.
    """

    def __init__(self, cfg: ChatConfig) -> None:
        try:
            import openai as _openai
        except ImportError as exc:
            raise ImportError(
                "openai is required for the OpenAI chat provider. "
                "Install it with: pip install openai"
            ) from exc

        if not cfg.api_key:
            raise ValueError(
                "[chat_service] OpenAI provider requires an API key. "
                "Set OPENAI_API_KEY in your .env file."
            )

        self._client = _openai.OpenAI(api_key=cfg.api_key)
        self._cfg    = cfg
        logger.info(f"[chat_service] OpenAI provider initialised (model={cfg.model})")

    def complete(self, system_prompt: str, user_message: str) -> str:
        response = self._client.chat.completions.create(
            model=self._cfg.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            max_tokens=self._cfg.max_tokens,
            temperature=self._cfg.temperature,
        )
        return response.choices[0].message.content.strip()


# --------------------------------------------------------------------------- #
# Provider registry & singleton
# --------------------------------------------------------------------------- #

_CHAT_PROVIDER_REGISTRY: dict[str, type[ChatProvider]] = {
    "gemini": GeminiChatProvider,
    "openai": OpenAIChatProvider,
}

_CHAT_PROVIDER_SINGLETON: ChatProvider | None = None


def get_chat_provider(config_path: str = _CONFIG_PATH) -> ChatProvider:
    """
    Return the active ``ChatProvider`` singleton.

    Instantiated once from YAML on first call; cached thereafter.
    Call ``reset_chat_provider()`` in tests to force re-initialisation.

    Raises
    ------
    ValueError
        If ``rag.chat.provider`` names an unknown provider.
    """
    global _CHAT_PROVIDER_SINGLETON
    if _CHAT_PROVIDER_SINGLETON is not None:
        return _CHAT_PROVIDER_SINGLETON

    cfg      = _resolve_chat_config(config_path)
    prov_cls = _CHAT_PROVIDER_REGISTRY.get(cfg.provider)

    if prov_cls is None:
        raise ValueError(
            f"[chat_service] Unknown chat provider '{cfg.provider}'. "
            f"Valid options: {list(_CHAT_PROVIDER_REGISTRY)}"
        )

    logger.info(
        f"[chat_service] Creating chat provider '{cfg.provider}' "
        f"(model={cfg.model}, top_k={cfg.top_k})"
    )
    _CHAT_PROVIDER_SINGLETON = prov_cls(cfg)
    return _CHAT_PROVIDER_SINGLETON


def reset_chat_provider() -> None:
    """Clear the cached chat provider singleton (call in test teardown)."""
    global _CHAT_PROVIDER_SINGLETON
    _CHAT_PROVIDER_SINGLETON = None


def set_chat_provider(provider: ChatProvider) -> None:
    """
    Inject a provider instance directly (used in unit tests to avoid
    real API calls or requiring API keys).
    """
    global _CHAT_PROVIDER_SINGLETON
    _CHAT_PROVIDER_SINGLETON = provider


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

# Fallback message when the index is empty
_NO_CONTEXT_ANSWER = (
    "I don't have enough information in the provided documents to answer "
    "that question. Please upload relevant documents first."
)


def chat(question: str, user: str = "system") -> dict[str, Any]:
    """
    Answer a question using retrieved document context and persist the interaction.

    Flow
    ----
    1. ``retrieve(question, top_k)`` → ranked chunks.
    2. ``build_prompt(question, chunks)`` → (system, user).
    3. ``get_chat_provider().complete(system, user)`` → answer text.
    4. ``extract_sources(chunks)`` → deterministic citations.
    5. ``save_chat_turn(question, answer, sources, user)`` → persist to DB.
    6. Return ``{chat_id, answer, sources}``.

    Parameters
    ----------
    question : str
        The user's natural-language question.
    user : str
        Identity of the user asking the question (defaults to "system").

    Returns
    -------
    dict
        ``{"chat_id": str, "answer": str, "sources": list[{"document": str, "page": int}]}``

    Raises
    ------
    ValueError
        If *question* is empty.
    RuntimeError
        If the LLM provider call fails (caller should surface this as HTTP 500).
    """
    if not question or not question.strip():
        raise ValueError("[chat_service] question must not be empty.")

    cfg = _resolve_chat_config()

    # ── 1. Retrieve context ────────────────────────────────────────────────── #
    chunks = retrieve(question, top_k=cfg.top_k)

    if not chunks:
        logger.info("[chat_service] Index empty — returning fallback answer.")
        chat_id = save_chat_turn(
            question=question,
            answer=_NO_CONTEXT_ANSWER,
            sources=[],
            user=user,
        )
        return {
            "chat_id": chat_id,
            "answer":  _NO_CONTEXT_ANSWER,
            "sources": [],
        }

    # ── 2. Assemble prompt ─────────────────────────────────────────────────── #
    system_prompt, user_message = build_prompt(question, chunks)

    # ── 3. Call LLM ───────────────────────────────────────────────────────── #
    provider = get_chat_provider()
    try:
        answer = provider.complete(system_prompt, user_message)
    except Exception as exc:
        logger.error(f"[chat_service] LLM call failed: {exc}")
        raise RuntimeError(f"LLM provider error: {exc}") from exc

    # ── 4. Extract sources (deterministic — from chunk metadata) ──────────── #
    sources = extract_sources(chunks)

    # ── 5. Persist to chat_history ────────────────────────────────────────── #
    chat_id = save_chat_turn(
        question=question,
        answer=answer,
        sources=sources,
        user=user,
    )

    logger.info(
        f"[chat_service] Answered: '{question[:60]}' "
        f"— {len(sources)} source(s) (chat_id={chat_id})"
    )

    return {
        "chat_id": chat_id,
        "answer":  answer,
        "sources": sources,
    }

