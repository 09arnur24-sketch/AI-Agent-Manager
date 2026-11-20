from __future__ import annotations
import os
from pathlib import Path
import yaml

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "agents.yml"

def load_config(path: str | None = None) -> dict:
    cfg_path = Path(path) if path else DEFAULT_CONFIG
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    provider = data.setdefault("provider", {})
    timeout = int(data.get("app", {}).get("request_timeout_seconds", 90))
    providers = []

    groq = os.getenv("GROQ_API_KEY", "").strip()
    if groq:
        providers.append({"name": "groq", "base_url": "https://api.groq.com/openai/v1",
            "api_key": groq, "model": os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"), "timeout": timeout})

    openrouter = os.getenv("OPENROUTER_API_KEY", "").strip()
    if openrouter:
        providers.append({"name": "openrouter", "base_url": "https://openrouter.ai/api/v1",
            "api_key": openrouter, "model": os.getenv("OPENROUTER_MODEL", "openrouter/free"), "timeout": timeout})

    cf_token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
    cf_account = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
    if cf_token and cf_account:
        providers.append({"name": "cloudflare",
            "base_url": f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/ai/v1",
            "api_key": cf_token,
            "model": os.getenv("CLOUDFLARE_MODEL", "@cf/meta/llama-3.1-8b-instruct"), "timeout": timeout})

    legacy_key_name = os.getenv("AAM_API_KEY_ENV", provider.get("api_key_env", "AAM_API_KEY"))
    legacy_key = os.getenv(legacy_key_name, "").strip()
    legacy_url = os.getenv("AAM_API_BASE_URL", provider.get("base_url", "")).rstrip("/")
    legacy_model = os.getenv("AAM_MODEL", provider.get("model", ""))
    if legacy_url and legacy_key and legacy_model:
        providers.append({"name": "legacy-local", "base_url": legacy_url, "api_key": legacy_key,
            "model": legacy_model, "timeout": timeout})

    data["providers"] = providers
    data["mock"] = os.getenv("AAM_MOCK", "").lower() in {"1", "true", "yes"} or not providers
    data["runtime_mode"] = "multi-provider" if len(providers) > 1 else (
        "hosted-provider" if providers and providers[0]["name"] != "legacy-local" else "local-llm")
    return data
