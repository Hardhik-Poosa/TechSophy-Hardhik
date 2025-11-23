# src/category_model.py
"""
Category classification models for transaction descriptions.

At runtime we try to use the fine-tuned DistilBERT model saved under:
    models/bert_category_model/

If that model is missing or fails to load, callers are expected to catch
CategoryModelNotAvailableError and fall back to rule-based logic.
"""

from __future__ import annotations

from pathlib import Path

import torch
from transformers import DistilBertForSequenceClassification, DistilBertTokenizerFast

from src.logging_config import get_logger

logger = get_logger(__name__)

# Directory where train_bert_categories.py saved the model
MODEL_DIR = Path("models") / "bert_category_model"

# Simple in-memory cache so we only hit disk once
_MODEL: DistilBertForSequenceClassification | None = None
_TOKENIZER: DistilBertTokenizerFast | None = None
_ID2LABEL: dict[int, str] = {}


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

    if not MODEL_DIR.exists():
        raise CategoryModelNotAvailableError(
            f"BERT category model directory not found at {MODEL_DIR}"
        )

    try:
        logger.info("Loading BERT category model from %s", MODEL_DIR)

        # Local-only, offline load of the fine-tuned model to satisfy Bandit B615.
        _TOKENIZER = DistilBertTokenizerFast.from_pretrained(
            MODEL_DIR,
            local_files_only=True,  # nosec B615 - only load local fine-tuned weights
        )
        _MODEL = DistilBertForSequenceClassification.from_pretrained(
            MODEL_DIR,
            local_files_only=True,  # nosec B615 - only load local fine-tuned weights
        )
        _MODEL.eval()

        # Pull label mapping from config if available
        config = _MODEL.config
        if hasattr(config, "id2label") and isinstance(config.id2label, dict):
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


def predict_category(description: str) -> str:
    """
    Predict a high-level spending category for a transaction description.

    Raises:
        CategoryModelNotAvailableError if model is missing or fails to load.
    """
    _ensure_model_loaded()

    assert _MODEL is not None
    assert _TOKENIZER is not None

    text = description or ""
    inputs = _TOKENIZER(
        text,
        truncation=True,
        padding=True,
        max_length=64,
        return_tensors="pt",
    )

    # We do plain argmax on logits; no need for softmax
    with torch.no_grad():
        outputs = _MODEL(**inputs)
        logits = outputs.logits
        pred_id = int(torch.argmax(logits, dim=-1).item())

    label = _ID2LABEL.get(pred_id, str(pred_id))
    return label
