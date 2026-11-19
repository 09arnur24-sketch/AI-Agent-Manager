from __future__ import annotations
from dataclasses import dataclass
import httpx

class ProviderError(RuntimeError):
    pass

@dataclass
class ProviderSpec:
    name: str
    base_url: str
    api_key: str
    model: str
    timeout: int = 90

class LLMProvider:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 90):
        self.base_url, self.api_key, self.model, self.timeout = base_url.rstrip("/"), api_key, model, timeout

    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        if not (self.base_url and self.api_key and self.model):
            raise ProviderError("Provider is not configured")
        try:
            response = httpx.post(
                self.base_url + "/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "temperature": temperature, "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]},
                timeout=self.timeout,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ProviderError("Provider returned an empty response")
            return content
        except ProviderError:
            raise
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"HTTP {exc.response.status_code}") from exc
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError(f"Request failed: {type(exc).__name__}") from exc

class MultiProvider:
    def __init__(self, providers: list[tuple[str, LLMProvider]]):
        self.providers = providers
        self.used: list[str] = []

    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        failures = []
        for name, provider in self.providers:
            try:
                result = provider.complete(system_prompt, user_prompt, temperature)
                if name not in self.used:
                    self.used.append(name)
                return result
            except ProviderError as exc:
                failures.append(f"{name}: {exc}")
        raise ProviderError("All configured providers failed (" + "; ".join(failures) + ")")

def build_provider(config: dict):
    providers = []
    for item in config.get("providers", []):
        providers.append((item["name"], LLMProvider(
            item["base_url"], item["api_key"], item["model"], int(item.get("timeout", 90))
        )))
    if not providers:
        item = config.get("provider", {})
        if item.get("base_url") and item.get("api_key") and item.get("model"):
            providers.append(("legacy", LLMProvider(
                item["base_url"], item["api_key"], item["model"],
                int(config.get("app", {}).get("request_timeout_seconds", 90))
            )))
    return MultiProvider(providers) if providers else None
