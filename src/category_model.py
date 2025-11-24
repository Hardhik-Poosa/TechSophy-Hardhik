# src/category_model.py
"""
Category classification models for transaction descriptions.

At runtime we try to use the fine-tuned BERT model saved under:
    models/bert_category_model/

If that model is missing or fails to load, callers are expected to catch
CategoryModelNotAvailableError and fall back to rule-based logic.
"""

from __future__ import annotations

from pathlib import Path

import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.logging_config import get_logger

logger = get_logger(__name__)

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
BERT_MODEL_DIR = BASE_DIR / "models" / "bert_category_model"

# In-memory singletons
_MODEL: AutoModelForSequenceClassification | None = None
_TOKENIZER: AutoTokenizer | None = None
_ID2LABEL: dict[int, str] = {}

# Tune this based on your metrics
CONFIDENCE_THRESHOLD: float = 0.6


class CategoryModelNotAvailableError(RuntimeError):
    """
    Raised when a category model cannot be loaded (e.g. not trained yet).
    """

    pass


def _ensure_model_loaded() -> None:
    """
    Load tokenizer + model from disk once, or raise CategoryModelNotAvailableError.
    """
    global _MODEL, _TOKENIZER, _ID2LABEL

    if _MODEL is not None and _TOKENIZER is not None:
        return

    if not BERT_MODEL_DIR.exists():
        raise CategoryModelNotAvailableError(
            f"BERT category model directory not found at {BERT_MODEL_DIR}"
        )

    try:
        logger.info("Loading BERT category model from %s", BERT_MODEL_DIR)

        # Local-only, offline load of the fine-tuned model to satisfy Bandit B615.
        _TOKENIZER = AutoTokenizer.from_pretrained(
            BERT_MODEL_DIR,
            local_files_only=True,  # nosec B615 - only load local fine-tuned weights
        )
        _MODEL = AutoModelForSequenceClassification.from_pretrained(
            BERT_MODEL_DIR,
            local_files_only=True,  # nosec B615 - only load local fine-tuned weights
        )
        _MODEL.eval()

        config = _MODEL.config
        if hasattr(config, "id2label") and isinstance(config.id2label, dict):
            # keys might be str in config, normalize to int
            _ID2LABEL = {int(k): v for k, v in config.id2label.items()}
        else:
            num_labels = config.num_labels
            _ID2LABEL = {i: str(i) for i in range(num_labels)}

        logger.info("Loaded BERT category model with labels: %s", _ID2LABEL)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to load BERT category model: %s", exc, exc_info=True)
        _MODEL = None
        _TOKENIZER = None
        _ID2LABEL = {}
        raise CategoryModelNotAvailableError(
            f"Failed to load BERT category model: {exc}"
        ) from exc


def predict_category_with_confidence(text: str) -> tuple[str, float]:
    """
    Return (label, confidence) for a single transaction description.

    Raises:
        CategoryModelNotAvailableError if model is missing or fails to load.
    """
    _ensure_model_loaded()

    assert _MODEL is not None
    assert _TOKENIZER is not None

    inputs = _TOKENIZER(
        text or "",
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
    idx = int(pred_idx.item())
    label = _ID2LABEL.get(idx, str(idx))
    return label, confidence_val


def predict_category(text: str) -> str:
    """
    Wrapper used by the rest of the codebase.

    If confidence < CONFIDENCE_THRESHOLD, returns "Uncertain" so the
    frontend or downstream logic can highlight it for manual review.
    """
    label, conf = predict_category_with_confidence(text)
    if conf < CONFIDENCE_THRESHOLD:
        return "Uncertain"
    return label
