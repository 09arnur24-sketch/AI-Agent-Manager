from __future__ import annotations

import os
from pathlib import Path
import yaml

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "agents.yml"


def _first_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def load_config(path: str | None = None) -> dict:
    cfg_path = Path(path) if path else DEFAULT_CONFIG
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    provider = data.setdefault("provider", {})
    timeout = int(data.setdefault("app", {}).get("request_timeout_seconds", 90))

    # Priority order: hosted free tiers first, local Ollama last.
    providers = []
    groq_key = _first_env("AAM_GROQ_API_KEY", "GROQ_API_KEY")
    if groq_key:
        providers.append({
            "name": "groq",
            "base_url": "https://api.groq.com/openai/v1",
            "api_key": groq_key,
            "model": _first_env("AAM_GROQ_MODEL") or "qwen/qwen3.6-27b",
        })

    openrouter_key = _first_env("AAM_OPENROUTER_API_KEY", "OPENROUTER_API_KEY")
    if openrouter_key:
        providers.append({
            "name": "openrouter",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": openrouter_key,
            "model": _first_env("AAM_OPENROUTER_MODEL") or "inclusionai/ling-3.2-flash:free",
            "extra_headers": {"HTTP-Referer": "https://github.com/09arnur24-sketch/AI-Agent-Manager", "X-Title": "AI Agent Manager"},
        })

    # Keep compatibility with the existing Ollama/custom OpenAI-compatible setup.
    legacy_base = _first_env("AAM_API_BASE_URL") or provider.get("base_url", "")
    legacy_model = _first_env("AAM_MODEL") or provider.get("model", "")
    legacy_key_env = _first_env("AAM_API_KEY_ENV") or provider.get("api_key_env", "AAM_API_KEY")
    legacy_key = os.getenv(legacy_key_env, "").strip()
    if legacy_base and legacy_model and legacy_key:
        is_ollama = "127.0.0.1" in legacy_base or "localhost" in legacy_base
        providers.append({
            "name": "ollama" if is_ollama else "custom",
            "base_url": legacy_base.rstrip("/"),
            "api_key": legacy_key,
            "model": legacy_model,
        })

    data["providers"] = providers
    data["mock"] = _first_env("AAM_MOCK").lower() in {"1", "true", "yes"} or not providers
    data["provider_timeout_seconds"] = timeout
    return data
