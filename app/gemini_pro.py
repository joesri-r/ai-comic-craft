"""
gemini_pro.py — Generates detailed story content for a 5-panel comic.
Uses the reusable generate_with_fallback() helper for retry + model fallback.
"""

import json
import re
from app.config import GEMINI_PRO_MODEL, DEMO_MODE
from app.gemini_client import generate_with_fallback


def generate_story(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
    outline: list,
) -> list:
    """Generate detailed story content for each panel. Returns a list of panel dicts."""

    if DEMO_MODE:
        story = []
        for panel in outline:
            p = panel.copy()
            if p["panel_number"] == 1:
                p["caption"] = f"The {setting} was quiet..."
                p["narration"] = f"{character_name} knew this was just the beginning."
                p["dialogue"] = "I must find the truth."
            elif p["panel_number"] == 2:
                p["caption"] = "A few hours later..."
                p["narration"] = "A strange light caught their eye."
                p["dialogue"] = "What is this?"
            elif p["panel_number"] == 3:
                p["caption"] = "Suddenly!"
                p["narration"] = "Danger approached rapidly."
                p["dialogue"] = "I won't back down!"
            elif p["panel_number"] == 4:
                p["caption"] = "With quick thinking..."
                p["narration"] = f"{character_name} outsmarted the threat."
                p["dialogue"] = "Take that!"
            else:
                p["caption"] = "At last."
                p["narration"] = "The journey was successful."
                p["dialogue"] = "I did it!"
            story.append(p)
        return story

    # ── Build the prompt ──
    outline_json = json.dumps(outline, indent=2)
    prompt = f"""You are a professional comic book writer. Generate the detailed story content (caption, narration, dialogue) for the following 5-panel comic outline.

Context:
Story Prompt: {story_prompt}
Main Character Name: {character_name}
Setting: {setting}
Tone: {tone}
Art Style: {art_style}

Outline:
{outline_json}

Return the output STRICTLY as a JSON array containing exactly 5 objects. Each object must have:
- panel_number (integer 1-5, matching the outline)
- title (string, matching the outline)
- scene_description (string, matching the outline)
- caption (string, e.g., 'Meanwhile...', 'Later that day...')
- narration (string, voiceover explaining the story)
- dialogue (string, what the characters are saying)

Maintain character, setting, and tone consistency across all 5 panels.
Output only the JSON. Do not include any other text."""

    # ── Call LLMs with multi-provider retry + fallback ──
    try:
        text = generate_with_fallback(prompt, primary_model=GEMINI_PRO_MODEL)
        json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        story = json.loads(text)
        if isinstance(story, list) and len(story) >= 5:
            return story[:5]
    except Exception as e:
        print(f"[story] Cloud LLMs temporarily unavailable or quota-limited ({e}). Using dynamic story engine...")

    # Dynamic story content fallback tailored to user input
    captions = [
        f"The {setting} stretched endlessly ahead...",
        "A few moments later, deeper in...",
        "Suddenly, the ground trembled!",
        "With lightning-fast reflexes...",
        "As the dust settled..."
    ]
    narrations = [
        f"{character_name} stepped forward, ready for whatever lay ahead.",
        f"A peculiar glimmer caught {character_name}'s eye.",
        f"Danger emerged from the shadows of {setting}.",
        f"{character_name} found an opening and struck with precision.",
        f"The challenge was overcome, and peace returned to {setting}."
    ]
    dialogues = [
        f'{character_name}: "This is where it all begins."',
        f'{character_name}: "Wait... what is that glow?"',
        f'{character_name}: "I won\'t back down now!"',
        f'{character_name}: "Think fast!"',
        f'{character_name}: "We did it. Time to head home."'
    ]

    story = []
    for idx, panel in enumerate(outline[:5]):
        p = panel.copy()
        p["caption"] = captions[idx]
        p["narration"] = narrations[idx]
        p["dialogue"] = dialogues[idx]
        story.append(p)

    return story
