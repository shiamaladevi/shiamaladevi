"""Shared Gemini client setup and text generation."""
import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
logger = logging.getLogger(__name__)
PLACEHOLDER_KEYS = {
    "your_gemini_api_key_here",
    "your_key_here",
    "replace_me",
    "replace_me_with_your_gemini_api_key",
}

_configured_model = (
    os.getenv("GEMINI_MODEL")
    or os.getenv("GEMINI_PRO_MODEL")
    or os.getenv("GEMINI_FLASH_MODEL")
    or "gemini-3.8-flash"
).strip()
# Keep older .env files working after their Gemini 1.5 defaults were retired.
MODEL_NAME = "gemini-3.8-flash" if _configured_model.startswith("gemini-1.5-") else _configured_model
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash").strip()


def _http_status(exc: Exception):
    for attribute in ("code", "status_code"):
        value = getattr(exc, attribute, None)
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def generate_text(prompt: str) -> str:
    if not API_KEY or API_KEY.lower() in PLACEHOLDER_KEYS or API_KEY.lower().startswith("replace_me"):
        raise RuntimeError("GOOGLE_API_KEY is missing or still set to the example placeholder in .env")

    client = genai.Client(
        api_key=API_KEY,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                attempts=2,
                initial_delay=0.5,
                max_delay=1.5,
                http_status_codes=[408, 500, 502, 503, 504],
            )
        ),
    )
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    except Exception as exc:
        status = _http_status(exc)
        if status != 429 and (status is None or status < 500):
            raise
        if FALLBACK_MODEL == MODEL_NAME:
            raise
        logger.warning("Gemini model %s returned HTTP %s; retrying with %s",
                       MODEL_NAME, status, FALLBACK_MODEL)
        response = client.models.generate_content(model=FALLBACK_MODEL, contents=prompt)
    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response")
    return text
