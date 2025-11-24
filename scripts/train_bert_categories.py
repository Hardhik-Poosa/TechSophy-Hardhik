# scripts/train_bert_categories.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "training_categories.csv"
MODELS_DIR = BASE_DIR / "models"
BERT_MODEL_DIR = MODELS_DIR / "bert_category_model"
METRICS_PATH = MODELS_DIR / "category_model_metrics.json"

BERT_MODEL_NAME = "bert-base-uncased"  # HF model name


class CategoryDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, label2id):
        self.texts = list(texts)
        self.labels = list(labels)
        self.tokenizer = tokenizer
        self.label2id = label2id

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx) -> dict[str, Any]:
        text = self.texts[idx]
        label = self.labels[idx]
        encoded = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=64,
            return_tensors="pt",
        )
        item = {k: v.squeeze(0) for k, v in encoded.items()}
        item["labels"] = torch.tensor(self.label2id[label], dtype=torch.long)
        return item


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)

    acc = accuracy_score(labels, preds)
    macro_f1 = f1_score(labels, preds, average="macro")
    cm = confusion_matrix(labels, preds).tolist()

    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "confusion_matrix": cm,
    }


def main() -> None:
    print(f"Loading dataset from {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)

    # column names in training_categories.csv
    texts = df["description"].astype(str).tolist()
    labels = df["category"].astype(str).tolist()

    unique_labels = sorted(df["category"].unique())
    label2id = {label: i for i, label in enumerate(unique_labels)}
    id2label = {i: label for label, i in label2id.items()}

    # ---- train / val / test split ----
    (
        texts_train,
        texts_temp,
        labels_train,
        labels_temp,
    ) = train_test_split(
        texts,
        labels,
        test_size=0.3,
        random_state=42,
        stratify=labels,
    )

    texts_val, texts_test, labels_val, labels_test = train_test_split(
        texts_temp,
        labels_temp,
        test_size=0.5,
        random_state=42,
        stratify=labels_temp,
    )

    print(f"Train size: {len(texts_train)}")
    print(f"Val size:   {len(texts_val)}")
    print(f"Test size:  {len(texts_test)}")

    tokenizer = AutoTokenizer.from_pretrained(BERT_MODEL_NAME)

    train_ds = CategoryDataset(texts_train, labels_train, tokenizer, label2id)
    val_ds = CategoryDataset(texts_val, labels_val, tokenizer, label2id)
    test_ds = CategoryDataset(texts_test, labels_test, tokenizer, label2id)

    model = AutoModelForSequenceClassification.from_pretrained(
        BERT_MODEL_NAME,
        num_labels=len(unique_labels),
        id2label=id2label,
        label2id=label2id,
    )

    # ---- minimal TrainingArguments (compatible with older transformers) ----
    training_args = TrainingArguments(
        output_dir=str(BERT_MODEL_DIR / "checkpoints"),
        num_train_epochs=3,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        learning_rate=2e-5,
        weight_decay=0.01,
        logging_steps=50,
        # don't pass evaluation_strategy/save_strategy/logging_strategy
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )

    # ---- train ----
    trainer.train()

    # ---- evaluate on test set ----
    print("Evaluating on test set...")
    raw_test_metrics = trainer.evaluate(eval_dataset=test_ds)
    print("Test metrics:", raw_test_metrics)

    # ---- save final model + tokenizer ----
    BERT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(BERT_MODEL_DIR)
    tokenizer.save_pretrained(BERT_MODEL_DIR)

    # ---- save compact metrics ----
    metrics_to_save = {
        "accuracy": float(raw_test_metrics.get("eval_accuracy", 0.0)),
        "macro_f1": float(raw_test_metrics.get("eval_macro_f1", 0.0)),
        "classes": unique_labels,
    }

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_PATH.open("w", encoding="utf-8") as f:
        json.dump(metrics_to_save, f, indent=2)

    print(f"Saved metrics to {METRICS_PATH}")


if __name__ == "__main__":
    main()
