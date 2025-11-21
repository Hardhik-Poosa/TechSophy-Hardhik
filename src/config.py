"""
Configuration loader.

All configuration is centralized in config.yaml and accessed via
helper functions. Config is cached in memory for performance.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

_CONFIG_CACHE: Dict[str, Any] | None = None


def _load_config_file(config_path: str | Path = "config.yaml") -> Dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {path.resolve()}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_config(reload: bool = False) -> Dict[str, Any]:
    """
    Return the full configuration dictionary, optionally reloading from disk.
    """
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None or reload:
        _CONFIG_CACHE = _load_config_file()
    return _CONFIG_CACHE


def _get_section(name: str) -> Dict[str, Any]:
    cfg = get_config()
    return cfg.get(name, {}) or {}


def get_data_config() -> Dict[str, Any]:
    return _get_section("data")


def get_model_config() -> Dict[str, Any]:
    return _get_section("model")


def get_preprocessing_config() -> Dict[str, Any]:
    return _get_section("preprocessing")


def get_business_rules_config() -> Dict[str, Any]:
    return _get_section("business_rules")


def get_visualization_config() -> Dict[str, Any]:
    return _get_section("visualization")


def get_logging_config() -> Dict[str, Any]:
    return _get_section("logging")
