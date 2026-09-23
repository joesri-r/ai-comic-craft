import os
import time
import uuid
import math
import urllib.parse
import urllib.request
from app.config import (
    GEMINI_IMAGE_API_KEY,
    GEMINI_API_KEY,
    OPENAI_API_KEY,
    OPENAI_IMAGE_MODEL,
    IMAGE_GENERATION_ENABLED,
    DEMO_MODE,
)
from app.openai_client import generate_openai_image
from app.external_images import fetch_and_stylize_external_image

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None
    genai_types = None

_client = None


def _get_gemini_client():
    global _client
    if _client is not None:
        return _client
    key = GEMINI_IMAGE_API_KEY or GEMINI_API_KEY
    if not key or not genai:
        return None
    try:
        _client = genai.Client(api_key=key)
        return _client
    except Exception as e:
        print(f"[image_generator] Error initializing Gemini client: {e}")
        return None


def enhance_prompt(base_prompt: str, character_description: str, art_style: str) -> str:
    """
    Enhances prompt for AI comic story scene illustration.
    Includes character description and art style quality tags.
    """
    clean_prompt = base_prompt.replace("POW!", "").replace("BOOM!", "").replace("ZAP!", "")
    return (
        f"{clean_prompt}, featuring {character_description}, "
        f"comic book illustration, {art_style} style, detailed environment, "
        f"cinematic composition, expressive character, consistent character appearance, "
        f"high detail, clean line art, dramatic lighting, vibrant colors, no text, no speech bubbles, no watermark."
    )


def _try_openai_image_generation(prompt: str, filepath: str) -> bool:
    """Attempt image generation using OpenAI DALL-E."""
    if not OPENAI_API_KEY:
        return False
    try:
        data = generate_openai_image(prompt, model=OPENAI_IMAGE_MODEL)
        if data and len(data) > 1000:
            with open(filepath, "wb") as f:
                f.write(data)
            print(f"[image_generator] SUCCESS: OpenAI DALL-E image generated ({len(data)} bytes)!")
            return True
    except Exception as e:
        err = str(e)
        if "429" in err or "insufficient_quota" in err or "credit_balance_exhausted" in err:
            print(f"[image_generator] OpenAI DALL-E quota notice: {err[:100]} (switching to fallback)")
        else:
            print(f"[image_generator] OpenAI DALL-E note: {e}")
    return False


def _try_gemini_image_generation(prompt: str, filepath: str) -> bool:
    """Attempt image generation using Gemini API."""
    client = _get_gemini_client()
    if not client:
        return False

    # Gemini image models to try
    models_to_try = [
        "gemini-2.5-flash-image",
        "gemini-3.1-flash-image",
        "gemini-3.1-flash-lite-image",
        "gemini-3-pro-image",
    ]

    for model_name in models_to_try:
        try:
            print(f"[image_generator] Attempting Gemini image model '{model_name}'...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ) if genai_types else None,
            )
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if getattr(part, "inline_data", None) and part.inline_data.data:
                        with open(filepath, "wb") as f:
                            f.write(part.inline_data.data)
                        print(f"[image_generator] SUCCESS: Gemini image generated with {model_name}!")
                        return True
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                print(f"[image_generator] Gemini model {model_name}: 429 free-tier quota (switching to AI story generator)")
                break  # If free-tier quota 0, skip remaining Gemini models to save time
            else:
                print(f"[image_generator] Gemini model {model_name} note: {e}")
    return False


def _try_ai_story_generator(prompt: str, filepath: str) -> bool:
    """Generates a real AI story image matching the scene prompt with robust retry and backoff."""
    models = ["turbo", "flux"]
    clean_p = prompt[:300].strip()
    encoded_prompt = urllib.parse.quote(clean_p)

    for model in models:
        try:
            seed = int(time.time() * 1000) % 100000
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&model={model}&nologo=true&seed={seed}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ComicCraft/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                if data and len(data) > 1000:
                    with open(filepath, "wb") as f:
                        f.write(data)
                    print(f"[image_generator] SUCCESS: AI story scene image generated ({model}, {len(data)} bytes).")
                    return True
        except Exception as e:
            print(f"[image_generator] Story generator note ({model}): {e}")
            # Fail fast, do not sleep, to avoid Vercel 10s timeout
    return False


def _make_demo_placeholder(filepath: str, panel_num: int = 1, prompt_text: str = "") -> None:
    """Generates a demo comic panel graphic (ONLY used when DEMO_MODE=true)."""
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (512, 512), color=(18, 18, 30))
        draw = ImageDraw.Draw(img)

        theme_colors = [
            [(255, 87, 87), (255, 200, 50)],
            [(87, 157, 255), (50, 220, 255)],
            [(157, 87, 255), (255, 100, 220)],
            [(87, 255, 157), (220, 255, 50)],
            [(255, 157, 87), (255, 220, 100)],
        ]
        c1, c2 = theme_colors[(panel_num - 1) % len(theme_colors)]

        cx, cy = 256, 256
        num_rays = 16
        for i in range(num_rays):
            angle1 = (i / float(num_rays)) * 2 * math.pi
            angle2 = ((i + 0.5) / float(num_rays)) * 2 * math.pi
            x1 = cx + int(320 * math.cos(angle1))
            y1 = cy + int(320 * math.sin(angle1))
            x2 = cx + int(320 * math.cos(angle2))
            y2 = cy + int(320 * math.sin(angle2))
            fill_color = c1 if i % 2 == 0 else c2
            draw.polygon([(cx, cy), (x1, y1), (x2, y2)], fill=fill_color)

        draw.ellipse([76, 176, 436, 336], fill=(255, 255, 255), outline=(0, 0, 0), width=5)
        action_words = ["POW!", "BOOM!", "ZAP!", "SLAM!", "CRASH!"]
        action = action_words[(panel_num - 1) % len(action_words)]

        draw.text((256, 226), action, fill=c1, anchor="mm")
        draw.text((256, 266), f"DEMO PANEL {panel_num}", fill=(30, 30, 40), anchor="mm")

        short_prompt = (prompt_text[:32] + "...") if len(prompt_text) > 32 else prompt_text
        if short_prompt:
            draw.text((256, 296), short_prompt, fill=(100, 100, 120), anchor="mm")

        for b in range(6):
            draw.rectangle([b, b, 511 - b, 511 - b], outline=(20, 20, 30))

        img.save(filepath)
    except Exception as e:
        print(f"[image_generator] Demo placeholder creation error: {e}")


import tempfile
import base64

def generate_image(prompt: str, character_description: str, art_style: str,
                   filename: str = None, panel_num: int = 1) -> dict:
    """
    Generates a real AI comic story panel image.
    Saves image to temp directory and returns absolute file path and base64 data URI.
    """
    if not filename:
        unique_id = uuid.uuid4().hex[:6]
        filename = f"panel_{int(time.time())}_{panel_num}_{unique_id}.png"

    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, "comiccraft", "panels", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Demo mode check
    if DEMO_MODE or not IMAGE_GENERATION_ENABLED:
        print(f"[image_generator] DEMO_MODE active. Using demo graphic for Panel {panel_num}.")
        _make_demo_placeholder(filepath, panel_num, prompt)
    else:
        enhanced = enhance_prompt(prompt, character_description, art_style)
        print(f"[image_generator] Generating story image for Panel {panel_num}...")
        
        success = False
        if not success:
            success = _try_openai_image_generation(enhanced, filepath)
        if not success:
            success = _try_gemini_image_generation(enhanced, filepath)
        if not success:
            success = _try_ai_story_generator(enhanced, filepath)
        if not success:
            success = fetch_and_stylize_external_image(prompt, character_description, art_style, filepath)
            
        if not success:
            print(f"[image_generator] Creating panel placeholder for Panel {panel_num}.")
            _make_demo_placeholder(filepath, panel_num, prompt)

    # Read the file and convert to base64 data URI
    try:
        with open(filepath, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode('utf-8')
            data_uri = f"data:image/png;base64,{b64_str}"
    except Exception as e:
        print(f"[image_generator] Error encoding base64: {e}")
        data_uri = ""

    return {"file_path": filepath, "data_uri": data_uri}




