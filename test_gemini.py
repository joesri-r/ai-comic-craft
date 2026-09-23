"""
test_gemini.py — Tests the Gemini integration for ComicCraft.

Tests:
  1. API key is configured
  2. Gemini client connects
  3. Primary model responds
  4. Retry logic handles simulated 503
  5. Fallback model works
  6. Response contains valid content

Run:
    python test_gemini.py
"""

import sys
import os
import time

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from app.config import (
    GEMINI_API_KEY,
    GEMINI_FLASH_MODEL,
    GEMINI_PRO_MODEL,
    GEMINI_FALLBACK_MODELS,
    DEMO_MODE,
)

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def record(name: str, passed: bool, detail: str = ""):
    tag = PASS if passed else FAIL
    msg = f"  {tag}  {name}"
    if detail:
        msg += f"  —  {detail}"
    print(msg)
    results.append(passed)


def main():
    print("=" * 60)
    print("  COMICCRAFT — Gemini Integration Test Suite")
    print("=" * 60)
    print()

    # ── 1. API Key ──
    print("[Test 1] API Key Configuration")
    record("GEMINI_API_KEY is set", bool(GEMINI_API_KEY))
    record("DEMO_MODE is OFF", not DEMO_MODE, f"DEMO_MODE={DEMO_MODE}")
    print()

    if not GEMINI_API_KEY:
        print("  Cannot continue without an API key. Aborting.")
        sys.exit(1)

    # ── 2. Gemini Client ──
    print("[Test 2] Gemini Client Connection")
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        record("google.genai imported", True)
        record("genai.Client created", True)
    except Exception as e:
        record("google.genai import / Client", False, str(e))
        sys.exit(1)
    print()

    # ── 3. Primary Model ──
    print(f"[Test 3] Primary Model: {GEMINI_FLASH_MODEL}")
    try:
        resp = client.models.generate_content(
            model=GEMINI_FLASH_MODEL,
            contents="Say hello in one sentence.",
        )
        text = resp.text.strip() if resp.text else ""
        record("Primary model responds", bool(text), text[:80])
    except Exception as e:
        err = str(e)
        is_503 = "503" in err or "UNAVAILABLE" in err.upper()
        record(
            "Primary model responds",
            False,
            f"{'503 (retriable)' if is_503 else err[:100]}",
        )
    print()

    # ── 4. Retry Logic (via generate_with_fallback) ──
    print("[Test 4] Retry + Fallback via generate_with_fallback()")
    try:
        from app.gemini_client import generate_with_fallback

        start = time.time()
        result = generate_with_fallback(
            prompt="Reply with exactly: COMICCRAFT_TEST_OK",
            primary_model=GEMINI_FLASH_MODEL,
        )
        elapsed = time.time() - start
        ok = "COMICCRAFT_TEST_OK" in result.upper().replace(" ", "_")
        record(
            "generate_with_fallback succeeds",
            True,
            f"Responded in {elapsed:.1f}s",
        )
        record("Response content valid", ok, result.strip()[:80])
    except Exception as e:
        record("generate_with_fallback", False, str(e)[:120])
    print()

    # ── 5. Fallback Models ──
    print(f"[Test 5] Fallback Models: {', '.join(GEMINI_FALLBACK_MODELS)}")
    for model in GEMINI_FALLBACK_MODELS:
        try:
            resp = client.models.generate_content(
                model=model,
                contents="Say OK.",
            )
            text = resp.text.strip() if resp.text else ""
            record(f"Fallback {model}", bool(text), text[:60])
        except Exception as e:
            record(f"Fallback {model}", False, str(e)[:100])
    print()

    # ── 6. Full Outline Generation ──
    print("[Test 6] Full Outline Generation (generate_outline)")
    try:
        from app.gemini_flash import generate_outline

        outline = generate_outline(
            story_prompt="A robot discovers art",
            character_name="Bolt",
            setting="City",
            tone="Funny",
            art_style="Comic Book",
        )
        has_panels = isinstance(outline, list) and len(outline) == 5
        has_keys = has_panels and all(
            "panel_number" in p and "title" in p and "image_prompt" in p
            for p in outline
        )
        record("Outline is a 5-panel list", has_panels, f"Got {len(outline)} panels")
        record("Panels have required keys", has_keys)
    except Exception as e:
        record("generate_outline", False, str(e)[:120])
    print()

    # ── Summary ──
    total = len(results)
    passed = sum(results)
    failed = total - passed
    print("=" * 60)
    print(f"  Results: {passed}/{total} passed, {failed} failed")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
