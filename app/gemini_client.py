"""
gemini_client.py — Reusable Gemini helper with automatic retry and model fallback.

Usage:
    from app.gemini_client import generate_with_fallback

    text = generate_with_fallback(prompt, primary_model="gemini-3.8-flash")
"""

import time
from google import genai
from app.config import (
    GEMINI_API_KEY,
    GEMINI_FALLBACK_MODELS,
    DEMO_MODE,
    OPENAI_API_KEY,
    OPENAI_TEXT_MODEL,
    LLM_PROVIDERS,
)
from app.openai_client import generate_openai_text

# ── Constants ──
import os as _os
if _os.getenv("VERCEL"):
    MAX_RETRIES = 1
    INITIAL_BACKOFF_SECONDS = 1
else:
    MAX_RETRIES = 3
    INITIAL_BACKOFF_SECONDS = 2  # doubles each retry: 2 → 4 → 8

# Substrings that indicate a temporary/retriable server error
_RETRIABLE_MARKERS = ("503", "unavailable", "high demand", "temporarily")

# Status codes that should NOT be retried (client-side / config errors)
_NON_RETRIABLE_CODES = ("400", "401", "403", "404")

# ── Singleton Client ──
_client = None


def _get_client():
    """Lazily create and cache a single genai.Client."""
    global _client
    if _client is not None:
        return _client
    if not GEMINI_API_KEY:
        return None
    _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _is_quota_exhausted(error: Exception) -> bool:
    """Return True if model exceeded quota or rate limit."""
    msg = str(error).lower()
    return "429" in msg or "resource_exhausted" in msg or "quota" in msg


def _is_retriable(error: Exception) -> bool:
    """Return True if the error looks like a temporary 503 / high-demand issue."""
    msg = str(error).lower()

    if _is_quota_exhausted(error):
        return False

    for code in _NON_RETRIABLE_CODES:
        if code in msg:
            return False

    return any(marker in msg for marker in _RETRIABLE_MARKERS)


def _try_gemini_models(prompt: str, primary_model: str) -> str:
    """Try Gemini primary model and all fallback models."""
    client = _get_client()
    if not client:
        raise ValueError("Gemini API key is not configured.")

    models_to_try = [primary_model]
    for fb in GEMINI_FALLBACK_MODELS:
        if fb not in models_to_try:
            models_to_try.append(fb)

    last_error = None
    for model in models_to_try:
        try:
            return _try_model(client, model, prompt)
        except Exception as e:
            last_error = e
            if _is_quota_exhausted(e):
                print(f"[gemini] Model '{model}' free quota exhausted. Switching immediately to next model...")
                continue
            elif _is_retriable(e):
                print(f"[gemini] Model '{model}' busy. Switching to next fallback model...")
                continue
            else:
                print(f"[gemini] Error on '{model}': {e}. Trying next model...")
                continue

    raise last_error or ValueError("All Gemini models failed.")


def _try_model(client, model: str, prompt: str) -> str:
    """
    Try a single model with up to MAX_RETRIES attempts using exponential backoff.
    """
    last_error = None
    backoff = INITIAL_BACKOFF_SECONDS

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[gemini] Trying model: {model} (attempt {attempt}/{MAX_RETRIES})")

            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )

            text = response.text
            if not text:
                raise ValueError("Gemini returned an empty response.")

            print(f"[gemini] OK - Request successful using: {model}")
            return text

        except Exception as e:
            last_error = e

            if _is_retriable(e) and attempt < MAX_RETRIES:
                print(
                    f"[gemini] Model temporarily unavailable. "
                    f"Retrying in {backoff}s..."
                )
                time.sleep(backoff)
                backoff *= 2
            elif _is_retriable(e):
                print(f"[gemini] Model {model} still unavailable after {MAX_RETRIES} attempts.")
                break
            else:
                print(f"[gemini] Non-retriable error on {model}: {e}")
                raise

    raise last_error


def generate_with_fallback(prompt: str, primary_model: str) -> str:
    """
    Generate content using the configured providers (OpenAI, Gemini) with
    automatic fallback across providers and models.

    Args:
        prompt:        The full prompt string to send.
        primary_model: The preferred Gemini model name (e.g. "gemini-3.6-flash").

    Returns:
        The raw text response.
    """
    if DEMO_MODE:
        raise RuntimeError("generate_with_fallback should not be called in DEMO_MODE.")

    providers = LLM_PROVIDERS if LLM_PROVIDERS else ["openai", "gemini"]
    errors = []

    for provider in providers:
        if provider == "openai":
            if not OPENAI_API_KEY:
                continue
            try:
                print(f"[multi-llm] Attempting OpenAI ({OPENAI_TEXT_MODEL})...")
                return generate_openai_text(prompt, model=OPENAI_TEXT_MODEL)
            except Exception as e:
                err_str = str(e)
                print(f"[multi-llm] OpenAI attempt failed: {err_str[:120]} (falling back)")
                errors.append(f"OpenAI: {err_str}")

        elif provider == "gemini":
            if not GEMINI_API_KEY:
                continue
            try:
                print(f"[multi-llm] Attempting Gemini ({primary_model})...")
                return _try_gemini_models(prompt, primary_model)
            except Exception as e:
                err_str = str(e)
                print(f"[multi-llm] Gemini attempt failed: {err_str[:120]} (falling back)")
                errors.append(f"Gemini: {err_str}")

    raise ValueError(f"All LLM providers failed. Details: {' | '.join(errors)}")
