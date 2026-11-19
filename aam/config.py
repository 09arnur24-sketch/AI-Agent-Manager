from __future__ import annotations
import os
from pathlib import Path
import yaml

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "agents.yml"

def load_config(path: str | None = None) -> dict:
    cfg_path = Path(path) if path else DEFAULT_CONFIG
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    provider = data.setdefault("provider", {})
    provider["base_url"] = os.getenv("AAM_API_BASE_URL", provider.get("base_url", "")).rstrip("/")
    provider["model"] = os.getenv("AAM_MODEL", provider.get("model", ""))
    provider["api_key"] = os.getenv(os.getenv("AAM_API_KEY_ENV", provider.get("api_key_env", "AAM_API_KEY")), "")
    data["mock"] = os.getenv("AAM_MOCK", "").lower() in {"1", "true", "yes"} or not (
        provider["base_url"] and provider["model"] and provider["api_key"]
    )
    return data
