# src/category_model.py
"""
Category classification models for transaction descriptions.

We load a fine-tuned BERT model from:
    models/bert_category_model/

Exports:
    - CategoryModelNotAvailableError
    - predict_category_with_confidence(text) -> (label, confidence)
    - predict_category(text) -> label
        * Returns "Uncertain" if confidence is below CONFIDENCE_THRESHOLD.
"""

from __future__ import annotations

from pathlib import Path

import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.logging_config import get_logger

logger = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
BERT_MODEL_DIR = BASE_DIR / "models" / "bert_category_model"

CONFIDENCE_THRESHOLD: float = 0.6  # you can tune this


class CategoryModelNotAvailableError(RuntimeError):
    """Raised when a category model cannot be loaded (e.g. not trained yet)."""

    pass


# Lazy-loaded singletons
_TOKENIZER: AutoTokenizer | None = None
_MODEL: AutoModelForSequenceClassification | None = None
_LOADED: bool = False


def _ensure_model_loaded() -> None:
    """
    Load tokenizer + model from disk once, or raise CategoryModelNotAvailableError.
    """
    global _TOKENIZER, _MODEL, _LOADED

    if _LOADED and _TOKENIZER is not None and _MODEL is not None:
        return

    if not BERT_MODEL_DIR.exists():
        raise CategoryModelNotAvailableError(
            f"BERT category model directory not found at {BERT_MODEL_DIR}"
        )

    try:
        logger.info("Loading BERT category model from %s", BERT_MODEL_DIR)

        _TOKENIZER = AutoTokenizer.from_pretrained(
            BERT_MODEL_DIR,
            local_files_only=True,  # only load fine-tuned local weights
        )
        _MODEL = AutoModelForSequenceClassification.from_pretrained(
            BERT_MODEL_DIR,
            local_files_only=True,
        )
        _MODEL.eval()

        _LOADED = True

        logger.info(
            "Loaded BERT category model with labels: %s",
            getattr(_MODEL.config, "id2label", {}),
        )

    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to load BERT category model: %s", exc, exc_info=True)
        _TOKENIZER = None
        _MODEL = None
        _LOADED = False
        raise CategoryModelNotAvailableError(
            f"Failed to load BERT category model: {exc}"
        ) from exc


def predict_category_with_confidence(text: str) -> tuple[str, float]:
    """
    Return (label, confidence) for a single transaction description.

    Raises:
        CategoryModelNotAvailableError if the fine-tuned model cannot be loaded.
    """
    _ensure_model_loaded()
    assert _TOKENIZER is not None
    assert _MODEL is not None

    text = text or ""
    inputs = _TOKENIZER(
        text,
        truncation=True,
        padding=True,
        max_length=64,
        return_tensors="pt",
    )

    with torch.no_grad():
        outputs = _MODEL(**inputs)
        logits = outputs.logits
        probs = F.softmax(logits, dim=-1)
        confidence, pred_idx = torch.max(probs, dim=-1)

    confidence_val = float(confidence.item())

    # id2label is stored on the model config
    id2label = getattr(_MODEL.config, "id2label", None)
    if isinstance(id2label, dict):
        label = id2label[int(pred_idx)]
    else:
        # Fallback: just use the index as string
        label = str(int(pred_idx))

    return label, confidence_val


def predict_category(text: str) -> str:
    """
    Wrapper used by the rest of the codebase.

    Returns a category label, or "Uncertain" if confidence is below
    CONFIDENCE_THRESHOLD.

    Raises:
        CategoryModelNotAvailableError if the model cannot be loaded.
    """
    label, conf = predict_category_with_confidence(text)
    if conf < CONFIDENCE_THRESHOLD:
        return "Uncertain"
    return label
