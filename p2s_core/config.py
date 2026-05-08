from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


ENV_PATTERN = re.compile(r"^\$\{([A-Z0-9_]+)\}$")


def load_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    config_path = Path(path)
    load_dotenv(config_path.with_name(".env"))
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return _resolve_env_values(data)


def _resolve_env_values(value):
    if isinstance(value, dict):
        return {key: _resolve_env_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_env_values(item) for item in value]
    if isinstance(value, str):
        match = ENV_PATTERN.match(value)
        if match:
            return os.environ.get(match.group(1), "")
    return value
