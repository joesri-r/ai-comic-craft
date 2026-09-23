"""
gemini_flash.py — Generates a 5-panel comic outline using Gemini.
Uses the reusable generate_with_fallback() helper for retry + model fallback.
"""

import json
import re
from app.config import GEMINI_FLASH_MODEL, DEMO_MODE
from app.gemini_client import generate_with_fallback


def generate_outline(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
) -> list:
    """Generate a 5-panel comic outline. Returns a list of panel dicts."""

    if DEMO_MODE:
        return [
            {
                "panel_number": 1,
                "title": "The Journey Begins",
                "scene_description": f"{character_name} stands at the edge of the {setting}, looking determined.",
                "image_prompt": f"comic book illustration, {art_style} style, {character_name} looking at {setting}, {tone} atmosphere, wide shot.",
            },
            {
                "panel_number": 2,
                "title": "A Mysterious Discovery",
                "scene_description": f"{character_name} finds a hidden path glowing with strange light.",
                "image_prompt": f"comic book illustration, {art_style} style, {character_name} discovering a glowing path in the {setting}, {tone} atmosphere, medium shot.",
            },
            {
                "panel_number": 3,
                "title": "The Challenge",
                "scene_description": f"{character_name} faces a seemingly insurmountable obstacle.",
                "image_prompt": f"comic book illustration, {art_style} style, {character_name} facing a challenge in the {setting}, {tone} atmosphere, dramatic angle.",
            },
            {
                "panel_number": 4,
                "title": "Overcoming the Obstacle",
                "scene_description": f"{character_name} cleverly solves the problem using wits.",
                "image_prompt": f"comic book illustration, {art_style} style, {character_name} overcoming the obstacle, dynamic action, {tone} atmosphere, close up.",
            },
            {
                "panel_number": 5,
                "title": "Victory",
                "scene_description": f"{character_name} succeeds and smiles towards the horizon.",
                "image_prompt": f"comic book illustration, {art_style} style, {character_name} celebrating victory in the {setting}, {tone} atmosphere, beautiful landscape.",
            },
        ]

    # ── Build the prompt ──
    prompt = f"""You are a professional comic book writer. Generate a 5-panel comic outline based on the following:
Story Prompt: {story_prompt}
Main Character Name: {character_name}
Setting: {setting}
Tone: {tone}
Art Style: {art_style}

Return the output STRICTLY as a JSON array containing exactly 5 objects. Each object must have:
- panel_number (integer 1-5)
- title (string)
- scene_description (string)
- image_prompt (string, highly detailed for an AI image generator, must include character and setting)

Output only the JSON. Do not include any other text."""

    # ── Call LLMs with multi-provider retry + fallback ──
    try:
        text = generate_with_fallback(prompt, primary_model=GEMINI_FLASH_MODEL)
        json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        outline = json.loads(text)
        if isinstance(outline, list) and len(outline) >= 5:
            return outline[:5]
    except Exception as e:
        print(f"[outline] Cloud LLMs temporarily unavailable or quota-limited ({e}). Using dynamic story engine...")

    # Dynamic story outline fallback tailored to user input
    return [
        {
            "panel_number": 1,
            "title": f"Arrival at {setting}",
            "scene_description": f"{character_name} stands ready in {setting} to face: {story_prompt}.",
            "image_prompt": f"comic book illustration, {art_style} style, {character_name} entering {setting}, {tone} atmosphere, wide establishing shot.",
        },
        {
            "panel_number": 2,
            "title": "A Strange Discovery",
            "scene_description": f"{character_name} discovers a glowing clue buried deep in {setting}.",
            "image_prompt": f"comic book illustration, {art_style} style, {character_name} examining a mysterious artifact in {setting}, dramatic angle.",
        },
        {
            "panel_number": 3,
            "title": "The Perilous Encounter",
            "scene_description": f"Danger looms as {character_name} faces an unexpected threat in {setting}.",
            "image_prompt": f"comic book illustration, {art_style} style, {character_name} confronting danger in {setting}, high tension, dynamic action.",
        },
        {
            "panel_number": 4,
            "title": "Turning the Tide",
            "scene_description": f"With determination and skill, {character_name} turns the tables.",
            "image_prompt": f"comic book illustration, {art_style} style, {character_name} executing a clever counter-strategy, vibrant energy, close up.",
        },
        {
            "panel_number": 5,
            "title": "Triumph in the Horizon",
            "scene_description": f"{character_name} stands victorious as peace is restored to {setting}.",
            "image_prompt": f"comic book illustration, {art_style} style, {character_name} celebrating victory in {setting}, inspiring golden hour lighting.",
        },
    ]
