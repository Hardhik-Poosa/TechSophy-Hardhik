# scripts/train_bert_categories.py
"""
Fine-tune DistilBERT to classify transaction descriptions into spending categories.

Input:
    data/training_categories.csv

Expected columns:
    - description  (str): raw transaction text
    - category     (str): target label, e.g. "Food", "Travel", ...

Output:
    - HuggingFace model + tokenizer saved to:
        models/bert_category_model/
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from transformers import (
    DistilBertForSequenceClassification,
    DistilBertTokenizerFast,
    Trainer,
    TrainingArguments,
)

DATA_PATH = Path("data") / "training_categories.csv"
MODEL_DIR = Path("models") / "bert_category_model"


def load_dataset() -> tuple[pd.DataFrame, dict[str, int], dict[int, str]]:
    """
    Load training CSV and build label mappings.
    Returns:
        df           : full shuffled dataframe
        label2id     : mapping category -> int
        id2label     : mapping int -> category
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Training data not found at {DATA_PATH}. "
            "Make sure data/training_categories.csv exists."
        )

    df = pd.read_csv(DATA_PATH)

    if "description" not in df.columns or "category" not in df.columns:
        raise ValueError(
            "Expected columns 'description' and 'category' "
            f"in {DATA_PATH}, got {list(df.columns)}"
        )

    df = df.dropna(subset=["description", "category"]).copy()
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)

    categories: list[str] = sorted(df["category"].unique())
    label2id: dict[str, int] = {label: i for i, label in enumerate(categories)}
    id2label: dict[int, str] = {i: label for label, i in label2id.items()}

    return df, label2id, id2label


class TransactionDataset(torch.utils.data.Dataset):
    """Simple PyTorch Dataset wrapping tokenized texts and integer labels."""

    def __init__(self, encodings, labels: list[int]):
        self.encodings = encodings
        self.labels = labels

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        item = {key: val[idx] for key, val in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item


def tokenize_split(
    df: pd.DataFrame,
    tokenizer: DistilBertTokenizerFast,
    label2id: dict[str, int],
    max_length: int = 64,
) -> tuple[TransactionDataset, TransactionDataset]:
    """Tokenize descriptions and create train/validation datasets."""
    train_df, val_df = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df["category"]
    )

    def encode(text_series: pd.Series):
        return tokenizer(
            text_series.tolist(),
            truncation=True,
            padding=True,
            max_length=max_length,
        )

    train_encodings = encode(train_df["description"])
    val_encodings = encode(val_df["description"])

    train_labels = [label2id[c] for c in train_df["category"]]
    val_labels = [label2id[c] for c in val_df["category"]]

    train_dataset = TransactionDataset(train_encodings, train_labels)
    val_dataset = TransactionDataset(val_encodings, val_labels)

    return train_dataset, val_dataset


def compute_metrics(eval_pred):
    """Simple accuracy metric for evaluation."""
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    accuracy = (preds == labels).mean().item()
    return {"accuracy": accuracy}


def main() -> None:
    print("[INFO] Loading dataset...")
    df, label2id, id2label = load_dataset()

    print(f"[INFO] Found {len(df)} labeled rows.")
    print(f"[INFO] Categories: {sorted(label2id.keys())}")

    print("[INFO] Loading tokenizer and base model (distilbert-base-uncased)...")
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

    train_dataset, val_dataset = tokenize_split(df, tokenizer, label2id)

    num_labels = len(label2id)
    print(f"[INFO] Number of labels: {num_labels}")

    model = DistilBertForSequenceClassification.from_pretrained(
        "distilbert-base-uncased",
        num_labels=num_labels,
    )

    model.config.label2id = label2id
    model.config.id2label = id2label

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print(
        "[INFO] Initializing TrainingArguments (compatible with older transformers)..."
    )
    args = TrainingArguments(
        output_dir=str(MODEL_DIR / "checkpoints"),
        num_train_epochs=2,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        learning_rate=5e-5,
        warmup_steps=0,
        weight_decay=0.01,
        logging_dir=str(MODEL_DIR / "logs"),
        logging_steps=50,
        do_train=True,
        do_eval=True,
    )

    print("[INFO] Creating Trainer...")
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )

    print("[INFO] Starting training...")
    trainer.train()

    print("[INFO] Evaluating on validation set...")
    metrics = trainer.evaluate()
    print(f"[INFO] Validation metrics: {metrics}")

    print(f"[INFO] Saving fine-tuned model to {MODEL_DIR} ...")
    model.save_pretrained(MODEL_DIR)
    tokenizer.save_pretrained(MODEL_DIR)

    print("[INFO] Done. BERT category model trained and saved.")


if __name__ == "__main__":
    main()
