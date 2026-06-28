from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RuntimeConfig:
    sources: dict[str, Any]
    scoring: dict[str, Any]
    llm: dict[str, str]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_config(config_dir: Path | None = None) -> RuntimeConfig:
    load_dotenv()
    base = config_dir or ROOT / "config"
    llm = {
        "base_url": os.getenv("LLM_BASE_URL", "").rstrip("/"),
        "api_key": os.getenv("LLM_API_KEY", ""),
        "model": os.getenv("LLM_MODEL", ""),
        "timeout_seconds": os.getenv("LLM_TIMEOUT_SECONDS", "15"),
    }
    present = [bool(llm["base_url"]), bool(llm["api_key"]), bool(llm["model"])]
    if any(present) and not all(present):
        raise ValueError("LLM_BASE_URL, LLM_API_KEY, and LLM_MODEL must be configured together.")
    return RuntimeConfig(
        sources=load_yaml(base / "sources.yaml"),
        scoring=load_yaml(base / "scoring.yaml"),
        llm=llm,
    )
