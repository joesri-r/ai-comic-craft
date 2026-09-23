"""
openai_client.py — Helper for OpenAI text (chat completion) and DALL-E image generation.
"""

import base64
import urllib.request
from app.config import OPENAI_API_KEY, OPENAI_TEXT_MODEL, OPENAI_IMAGE_MODEL

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

_client = None


def get_openai_client():
    """Lazily create and cache the OpenAI client."""
    global _client
    if _client is not None:
        return _client
    if not OPENAI_API_KEY or OpenAI is None:
        return None
    try:
        _client = OpenAI(api_key=OPENAI_API_KEY)
        return _client
    except Exception as e:
        print(f"[openai] Error initializing OpenAI client: {e}")
        return None


def generate_openai_text(prompt: str, model: str = None, temperature: float = 0.7) -> str:
    """
    Generate text using OpenAI Chat Completions (e.g. gpt-4o-mini, gpt-4o).
    Raises exception on failure so caller can fall back.
    """
    client = get_openai_client()
    if not client:
        raise ValueError("OpenAI client is not configured or OPENAI_API_KEY is missing.")

    selected_model = model or OPENAI_TEXT_MODEL
    print(f"[openai] Generating text with model '{selected_model}'...")

    response = client.chat.completions.create(
        model=selected_model,
        messages=[
            {
                "role": "system",
                "content": "You are a professional comic book writer and storyboard artist. Always follow formatting instructions precisely.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI returned an empty response.")

    print(f"[openai] OK - Request successful using: {selected_model}")
    return content


def generate_openai_image(prompt: str, model: str = None, size: str = "1024x1024") -> bytes:
    """
    Generate an image using OpenAI DALL-E (dall-e-3 or dall-e-2).
    Returns raw image bytes.
    Raises exception on failure.
    """
    client = get_openai_client()
    if not client:
        raise ValueError("OpenAI client is not configured or OPENAI_API_KEY is missing.")

    selected_model = model or OPENAI_IMAGE_MODEL
    print(f"[openai] Generating image with model '{selected_model}'...")

    # DALL-E 2 only supports up to 1024x1024; DALL-E 3 supports 1024x1024, 1024x1792, 1792x1024
    # Default to 1024x1024 for standard panel layout
    img_size = "1024x1024" if selected_model == "dall-e-3" else "512x512"

    try:
        response = client.images.generate(
            model=selected_model,
            prompt=prompt,
            n=1,
            size=img_size,
        )
    except Exception as e:
        # Some accounts/endpoints accept response_format="b64_json"
        if "response_format" not in str(e):
            raise
        response = client.images.generate(
            model=selected_model,
            prompt=prompt,
            n=1,
            size=img_size,
        )

    image_item = response.data[0]
    if getattr(image_item, "b64_json", None) and image_item.b64_json:
        return base64.b64decode(image_item.b64_json)
    elif getattr(image_item, "url", None) and image_item.url:
        req = urllib.request.Request(
            image_item.url,
            headers={"User-Agent": "Mozilla/5.0 ComicCraft/1.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()

    raise ValueError("OpenAI did not return image data.")
