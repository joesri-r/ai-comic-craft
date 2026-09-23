import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Separate key for image generation (falls back to main key if not set)
GEMINI_IMAGE_API_KEY = os.getenv("GEMINI_IMAGE_API_KEY") or GEMINI_API_KEY
HF_API_KEY = os.getenv("HF_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# ── Model Configuration ──
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-3.6-flash")
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-3.6-flash")
IMAGE_MODEL_ID = os.getenv("IMAGE_MODEL_ID", "runwayml/stable-diffusion-v1-5")

# ── OpenAI Models ──
OPENAI_TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")

# ── Provider Priority ──
_provider_raw = os.getenv("LLM_PROVIDER", "openai,gemini")
LLM_PROVIDERS = [p.strip().lower() for p in _provider_raw.split(",") if p.strip()]

# ── Fallback Models ──
# Comma-separated list of models to try when the primary model returns 503
_fallback_raw = os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.8-flash,gemini-3.5-flash")
GEMINI_FALLBACK_MODELS = [m.strip() for m in _fallback_raw.split(",") if m.strip()]

# ── Feature Flags ──
IMAGE_GENERATION_ENABLED = os.getenv("IMAGE_GENERATION_ENABLED", "true").lower() == "true"
ENABLE_EXTERNAL_IMAGE_FALLBACK = os.getenv("ENABLE_EXTERNAL_IMAGE_FALLBACK", "true").lower() == "true"
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"


def validate_config():
    """Validate that required configuration is present."""
    if not DEMO_MODE:
        if not GEMINI_API_KEY and not OPENAI_API_KEY:
            raise ValueError(
                "Neither GEMINI_API_KEY nor OPENAI_API_KEY is configured in .env. "
                "Please set at least one API key or set DEMO_MODE=true."
            )
        print(f"[config] LLM Providers       : {', '.join(LLM_PROVIDERS)}")
        print(f"[config] Primary flash model : {GEMINI_FLASH_MODEL}")
        print(f"[config] Primary pro model   : {GEMINI_PRO_MODEL}")
        print(f"[config] Fallback models     : {', '.join(GEMINI_FALLBACK_MODELS)}")
        print(f"[config] OpenAI text model   : {OPENAI_TEXT_MODEL}")
        print(f"[config] OpenAI image model  : {OPENAI_IMAGE_MODEL}")
        print(f"[config] Image model ID      : {IMAGE_MODEL_ID}")
        print(f"[config] HF_API_KEY set      : {'YES' if HF_API_KEY else 'NO'}")
        print(f"[config] OPENAI_API_KEY set  : {'YES' if OPENAI_API_KEY else 'NO'}")
        print(f"[config] GEMINI_API_KEY set  : {'YES' if GEMINI_API_KEY else 'NO'}")
        print(f"[config] UNSPLASH_KEY set    : {'YES' if UNSPLASH_ACCESS_KEY else 'NO'}")
        print(f"[config] External fallback   : {'ON' if ENABLE_EXTERNAL_IMAGE_FALLBACK else 'OFF'}")
        print(f"[config] Image generation    : {'ON' if IMAGE_GENERATION_ENABLED else 'OFF'}")

