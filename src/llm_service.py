"""LLM (Gemini) utilities for generating finance summaries."""

from __future__ import annotations

import json
import os
import textwrap
from typing import Any

import google.generativeai as genai

from src.logging_config import get_logger

logger = get_logger(__name__)

_GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
_MODEL: genai.GenerativeModel | None = None


def _configure_gemini() -> None:
    """Configure the Gemini client from environment variables."""
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Please configure it before using LLM features.",
        )

    genai.configure(api_key=api_key)


def _get_model() -> genai.GenerativeModel:
    """Lazily create and cache the GenerativeModel instance."""
    global _MODEL  # noqa: PLW0603

    if _MODEL is None:
        _configure_gemini()
        logger.info(
            "Initializing Gemini model '%s' for monthly summaries",
            _GEMINI_MODEL_NAME,
        )
        _MODEL = genai.GenerativeModel(_GEMINI_MODEL_NAME)

    return _MODEL


def _build_prompt(summary_payload: dict[str, Any]) -> str:
    """Construct a natural-language prompt from the numeric summary payload."""
    # Make it safe/pretty JSON for the model
    payload_json = json.dumps(summary_payload, indent=2, ensure_ascii=False)

    prompt = textwrap.dedent(
        f"""
        You are a personal finance assistant. The user has uploaded a CSV
        of their transactions, and an analytics pipeline has already run.
        You are given a compact JSON summary with key metrics:

        {payload_json}

        Please write a clear, friendly monthly summary for the user. Include:

        1. A short overview of total income, total spending, and net cash flow.
        2. A breakdown of the top spending categories and any noticeable patterns.
        3. A brief note on anomalies or unusual transactions, if any.
        4. 3–5 concrete, practical recommendations to improve financial health.

        Style guidelines:
        - Use plain, simple language.
        - Do NOT repeat the raw numbers verbatim more than necessary.
        - Avoid bullet lists inside bullet lists; keep it readable.
        - Address the user directly as "you".
        """,
    ).strip()

    return prompt


def generate_month_summary(summary_payload: dict[str, Any]) -> str:
    """
    Call Gemini to generate a monthly finance summary.

    `summary_payload` is typically constructed in src.llm_routes.create_month_summary,
    and contains aggregate stats for a single pipeline run.
    """
    model = _get_model()

    prompt = _build_prompt(summary_payload)

    logger.info("Calling Gemini for monthly summary")

    try:
        response = model.generate_content(prompt)
    except Exception as exc:  # pragma: no cover - let FastAPI handle HTTP error
        # Surface the error message so the API returns something meaningful.
        raise RuntimeError(str(exc)) from exc

    # Normalise various possible shapes of the response
    if hasattr(response, "text"):
        text = response.text
    elif isinstance(response, dict) and "text" in response:
        text = str(response["text"])
    else:
        text = str(response)

    return text.strip()
