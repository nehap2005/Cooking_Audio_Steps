from typing import List
import re
import requests
import pyttsx3
import tempfile
import time
import os

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"


def clean_text(text: str) -> str:
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


COOKING_CONNECTORS = (
    r"\bthen\b|\band\b|\bafter that\b|\bnext\b|\bonce\b|"
    r"\bmeanwhile\b|\buntil\b|\bbefore\b|\bfinally\b"
)

def split_into_candidate_steps(text: str) -> List[str]:
    parts = re.split(r"[.!?]", text)
    steps = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        sub_parts = re.split(COOKING_CONNECTORS, part, flags=re.IGNORECASE)
        for sp in sub_parts:
            sp = sp.strip()
            if len(sp.split()) >= 3:
                steps.append(sp)

    return steps


def normalize_steps(steps: List[str]) -> List[str]:
    normalized = []
    seen = set()

    for step in steps:
        step = step.capitalize()
        step = re.sub(r"\s*(optional|if desired).*", "", step, flags=re.I)
        step = step.rstrip(",;:")

        key = step.lower()
        if key not in seen:
            seen.add(key)
            normalized.append(step)

    return normalized


def refine_with_ollama(steps: List[str]) -> List[str]:
    joined = "\n".join(f"- {s}" for s in steps)

    prompt = f"""
Rewrite the following cooking steps to be:
- Short
- Clear
- Imperative
- Suitable for audio playback

Do not add new steps.
Return numbered steps only.

Steps:
{joined}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=60
    )

    text = response.json()["response"]
    return [line.strip() for line in text.split("\n") if re.match(r"^\d+\.", line.strip())]


# ✅ AUDIO → BYTES (STREAMLIT-SAFE)
def generate_audio_bytes(steps: List[str], rate: int = 165) -> bytes:
    engine = pyttsx3.init()
    engine.setProperty("rate", rate)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        audio_path = tmp.name

    engine.save_to_file(" ".join(steps), audio_path)
    engine.runAndWait()

    time.sleep(0.3)

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    os.remove(audio_path)
    return audio_bytes


def convert_to_audio_steps(
    recipe_text: str,
    with_audio: bool = False,
    speech_rate: int = 165
):
    if not recipe_text.strip():
        return [], None

    text = clean_text(recipe_text)
    candidates = split_into_candidate_steps(text)
    normalized = normalize_steps(candidates)

    try:
        refined = refine_with_ollama(normalized)
        steps = refined if refined else normalized
    except Exception:
        steps = normalized

    numbered = [
        s if re.match(r"^\d+\.", s) else f"{i+1}. {s}"
        for i, s in enumerate(steps)
    ]

    audio_bytes = None
    if with_audio:
        audio_bytes = generate_audio_bytes(numbered, rate=speech_rate)

    return numbered, audio_bytes
