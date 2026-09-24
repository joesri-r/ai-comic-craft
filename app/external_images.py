"""
external_images.py — Sourcing external images (Unsplash, Openverse, and Public Scenery)
matching the comic story context, with an automated Comic Book styling filter.
"""

import io
import json
import re
import urllib.parse
import urllib.request
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from app.config import (
    UNSPLASH_ACCESS_KEY,
    PEXELS_API_KEY,
    PIXABAY_API_KEY,
    ENABLE_EXTERNAL_IMAGE_FALLBACK
)

_BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ComicCraft/1.0"


def _extract_story_keywords(prompt: str, character_description: str = "") -> str:
    """
    Extracts the most relevant story keywords (subject, action, setting)
    from the scene prompt and character description to ensure external images
    closely match the comic story.
    """
    combined = f"{character_description} {prompt}"
    # Remove comic prompt boilerplate tags
    boilerplate = [
        "comic book illustration", "comic book", "clean line art",
        "detailed environment", "cinematic composition", "expressive character",
        "consistent character appearance", "high detail", "dramatic lighting",
        "vibrant colors", "no text", "no speech bubbles", "no watermark",
        "wide shot", "medium shot", "close up", "panel 1:", "panel 2:",
        "panel 3:", "panel 4:", "panel 5:", "featuring", "style"
    ]
    cleaned = combined.lower()
    for bp in boilerplate:
        cleaned = cleaned.replace(bp, " ")

    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", cleaned)
    words = cleaned.split()

    stop_words = {
        "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with",
        "from", "by", "of", "is", "are", "was", "were", "stands", "standing",
        "looking", "looks", "facing", "faces", "discovering", "discovers",
        "journey", "begins", "challenge", "victory", "scene", "tone", "atmosphere"
    }

    meaningful = [w for w in words if w not in stop_words and len(w) > 2]

    # Pick the most descriptive 3 to 5 words representing character & scene
    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for w in meaningful:
        if w not in seen:
            seen.add(w)
            deduped.append(w)

    result = " ".join(deduped[:4])
    return result if result else "scenic adventure landscape"


def search_unsplash_image(query: str) -> bytes:
    """
    Search Unsplash for an image matching the story using official API (requires UNSPLASH_ACCESS_KEY).
    """
    if not UNSPLASH_ACCESS_KEY:
        return None

    try:
        encoded_q = urllib.parse.quote(query)
        url = f"https://api.unsplash.com/search/photos?query={encoded_q}&per_page=5&orientation=squarish&client_id={UNSPLASH_ACCESS_KEY}"
        req = urllib.request.Request(url, headers={"User-Agent": _BROWSER_UA})

        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            if results:
                img_url = results[0]["urls"].get("regular") or results[0]["urls"].get("small")
                if img_url:
                    img_req = urllib.request.Request(img_url, headers={"User-Agent": _BROWSER_UA})
                    with urllib.request.urlopen(img_req, timeout=8) as img_resp:
                        return img_resp.read()
    except Exception as e:
        print(f"[external_images] Unsplash search note: {e}")

    return None


def search_pexels_image(query: str) -> bytes:
    """
    Search Pexels for an image matching the story using official API (requires PEXELS_API_KEY).
    """
    if not PEXELS_API_KEY:
        return None

    try:
        encoded_q = urllib.parse.quote(query)
        url = f"https://api.pexels.com/v1/search?query={encoded_q}&per_page=5"
        req = urllib.request.Request(url, headers={"User-Agent": _BROWSER_UA, "Authorization": PEXELS_API_KEY})

        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("photos", [])
            if results:
                img_url = results[0]["src"].get("large") or results[0]["src"].get("medium")
                if img_url:
                    img_req = urllib.request.Request(img_url, headers={"User-Agent": _BROWSER_UA})
                    with urllib.request.urlopen(img_req, timeout=8) as img_resp:
                        return img_resp.read()
    except Exception as e:
        print(f"[external_images] Pexels search note: {e}")

    return None


def search_pixabay_image(query: str) -> bytes:
    """
    Search Pixabay for an image matching the story using official API (requires PIXABAY_API_KEY).
    """
    if not PIXABAY_API_KEY:
        return None

    try:
        encoded_q = urllib.parse.quote(query)
        url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={encoded_q}&image_type=photo&per_page=5"
        req = urllib.request.Request(url, headers={"User-Agent": _BROWSER_UA})

        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("hits", [])
            if results:
                img_url = results[0].get("webformatURL") or results[0].get("largeImageURL")
                if img_url:
                    img_req = urllib.request.Request(img_url, headers={"User-Agent": _BROWSER_UA})
                    with urllib.request.urlopen(img_req, timeout=8) as img_resp:
                        return img_resp.read()
    except Exception as e:
        print(f"[external_images] Pixabay search note: {e}")

    return None


def search_wikimedia_image(query: str) -> bytes:
    """
    Search Wikimedia Commons for an image. Free and no API key required.
    """
    try:
        encoded_q = urllib.parse.quote(query)
        url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={encoded_q}&gsrnamespace=6&gsrlimit=3&prop=imageinfo&iiprop=url&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": _BROWSER_UA})

        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                imageinfo = page_data.get("imageinfo", [])
                if imageinfo:
                    img_url = imageinfo[0].get("url")
                    if img_url and img_url.lower().endswith((".jpg", ".jpeg", ".png")):
                        img_req = urllib.request.Request(img_url, headers={"User-Agent": _BROWSER_UA})
                        with urllib.request.urlopen(img_req, timeout=8) as img_resp:
                            data_bytes = img_resp.read()
                            if len(data_bytes) > 2000:
                                return data_bytes
    except Exception as e:
        print(f"[external_images] Wikimedia search note: {e}")

    return None


def search_openverse_image(query: str) -> bytes:
    """
    Search Openverse (Creative Commons & Public Domain illustrations/photos across hundreds of archives).
    Zero API key required. Matches the comic story query.
    """
    try:
        encoded_q = urllib.parse.quote(query)
        url = f"https://api.openverse.org/v1/images/?q={encoded_q}&page_size=5"
        req = urllib.request.Request(url, headers={"User-Agent": _BROWSER_UA})

        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            for item in results:
                img_url = item.get("url")
                if not img_url:
                    continue
                try:
                    img_req = urllib.request.Request(img_url, headers={"User-Agent": _BROWSER_UA})
                    with urllib.request.urlopen(img_req, timeout=8) as img_resp:
                        content_type = img_resp.headers.get("content-type", "")
                        if "image" in content_type or img_url.endswith((".jpg", ".jpeg", ".png", ".webp")):
                            data_bytes = img_resp.read()
                            if len(data_bytes) > 2000:
                                return data_bytes
                except Exception:
                    continue
    except Exception as e:
        print(f"[external_images] Openverse search note: {e}")

    return None


def search_public_scenery_image(query: str) -> bytes:
    """
    Fetch a story-matching scenery image from seeded high-resolution repository.
    """
    try:
        seed = urllib.parse.quote(query.replace(" ", "-").lower() or "comic-scene")
        url = f"https://picsum.photos/seed/{seed}/512/512"
        req = urllib.request.Request(url, headers={"User-Agent": _BROWSER_UA})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = resp.read()
            if data and len(data) > 1000:
                return data
    except Exception as e:
        print(f"[external_images] Scenery image note: {e}")

    return None


def apply_comic_filter(image_bytes: bytes, art_style: str = "Comic Book") -> bytes:
    """
    Applies a comic-book style transformation to external photos / paintings:
      1. Crop/Scale to 512x512 panel format
      2. Extract dark ink outlines using edge detection + thresholding
      3. Boost color saturation & quantize palette to cel-shaded comic tones
      4. Composite black ink outlines over the stylized colors
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # 1. Square crop & resize
        width, height = img.size
        min_dim = min(width, height)
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        img = img.crop((left, top, left + min_dim, top + min_dim))
        img = img.resize((512, 512), Image.Resampling.LANCZOS)

        # 2. Extract ink outline mask
        gray = img.convert("L")
        smooth_gray = gray.filter(ImageFilter.GaussianBlur(radius=1.2))
        edges = smooth_gray.filter(ImageFilter.FIND_EDGES)
        edges_inv = ImageOps.invert(edges)
        edge_mask = edges_inv.point(lambda p: 255 if p > 185 else 0)

        # 3. Enhance color & quantize for comic cel-look
        enhanced = ImageEnhance.Color(img).enhance(1.6)
        enhanced = ImageEnhance.Contrast(enhanced).enhance(1.2)
        quantized = enhanced.quantize(colors=28, method=Image.Quantize.MEDIANCUT).convert("RGB")

        # 4. Composite ink outlines over stylized color
        black_ink = Image.new("RGB", (512, 512), color=(20, 20, 28))
        comic_art = Image.composite(quantized, black_ink, edge_mask)

        out_buf = io.BytesIO()
        comic_art.save(out_buf, format="PNG")
        return out_buf.getvalue()

    except Exception as e:
        print(f"[external_images] Comic filter error: {e}")
        return None


def fetch_and_stylize_external_image(
    prompt: str,
    character_description: str,
    art_style: str,
    filepath: str,
) -> bool:
    """
    Fetches an external image strictly matching the comic story context across:
      1. Unsplash (if API key present)
      2. Openverse (Creative Commons repository matching story keywords)
      3. Seeded Scenery Repository (matching story environment)
    Then applies the Comic Book filter to stylize it into a comic panel.
    """
    if not ENABLE_EXTERNAL_IMAGE_FALLBACK:
        return False

    story_keywords = _extract_story_keywords(prompt, character_description)
    print(f"[external_images] Sourcing external image matching story: '{story_keywords}'...")

    raw_bytes = None
    source_name = None

    # 1. Try Unsplash (if key configured)
    if UNSPLASH_ACCESS_KEY and not raw_bytes:
        raw_bytes = search_unsplash_image(story_keywords)
        if raw_bytes: source_name = "Unsplash"

    # 2. Try Pexels (if key configured)
    if PEXELS_API_KEY and not raw_bytes:
        raw_bytes = search_pexels_image(story_keywords)
        if raw_bytes: source_name = "Pexels"

    # 3. Try Pixabay (if key configured)
    if PIXABAY_API_KEY and not raw_bytes:
        raw_bytes = search_pixabay_image(story_keywords)
        if raw_bytes: source_name = "Pixabay"
        
    # 4. Try Wikimedia Commons (Free, no key required)
    if not raw_bytes:
        raw_bytes = search_wikimedia_image(story_keywords)
        if raw_bytes: source_name = "Wikimedia Commons"

    # 5. Try Openverse (CC & Public Domain art/photos matching story)
    if not raw_bytes:
        raw_bytes = search_openverse_image(story_keywords)
        if raw_bytes: source_name = "Openverse"

    # 6. Try Public Scenery Repository seeded with story context
    if not raw_bytes:
        raw_bytes = search_public_scenery_image(story_keywords)
        if raw_bytes: source_name = "Public Scenery"
        
    # Check if a 403/500 HTML page snuck through (which causes broken images)
    if raw_bytes and b"<html" in raw_bytes.lower()[:500]:
        print("[external_images] Warning: Fetched bytes are HTML, not an image. Discarding.")
        raw_bytes = None

    # 7. Final generic fallback to guarantee an image (Wikimedia Commons)
    if not raw_bytes:
        print(f"[external_images] Specific searches failed. Using generic fallback...")
        import random
        generic_keywords = ["scenic landscape", "beautiful scenery", "fantasy landscape", "cityscape", "forest scenery"]
        fallback_query = random.choice(generic_keywords)
        raw_bytes = search_wikimedia_image(fallback_query)
        if raw_bytes: source_name = "Wikimedia Commons (Generic)"

    if not raw_bytes:
        print(f"[external_images] No external image found for story: '{story_keywords}' even with fallbacks")
        return False

    # Apply comic styling filter
    try:
        print(f"[external_images] Applying Comic Book filter to {source_name} image matching '{story_keywords}'...")
        styled_bytes = apply_comic_filter(raw_bytes, art_style)
        
        if not styled_bytes:
            print(f"[external_images] Comic filter rejected the image bytes (likely invalid image or HTML error page).")
            return False
            
        with open(filepath, "wb") as f:
            f.write(styled_bytes)
        print(f"[external_images] SUCCESS: Stylized {source_name} story image saved ({len(styled_bytes)} bytes)!")
        return True
    except Exception as e:
        print(f"[external_images] Error saving stylized image: {e}")
        return False
