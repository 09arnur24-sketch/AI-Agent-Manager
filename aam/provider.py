from __future__ import annotations

from dataclasses import dataclass
import httpx


class ProviderError(RuntimeError):
    """A provider request failed without exposing credentials or response bodies."""


@dataclass
class ProviderSpec:
    name: str
    base_url: str
    api_key: str
    model: str
    timeout: int = 90
    extra_headers: dict[str, str] | None = None


class LLMProvider:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int = 90,
        name: str = "custom",
        extra_headers: dict[str, str] | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.name = name
        self.extra_headers = extra_headers or {}

    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        if not (self.base_url and self.api_key and self.model):
            raise ProviderError(f"{self.name}: provider is not configured")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.extra_headers,
        }
        payload = {
            "model": self.model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            response = httpx.post(
                self.base_url + "/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ProviderError(f"{self.name}: empty completion")
            return content
        except ProviderError:
            raise
        except httpx.HTTPStatusError as exc:
            # Do not include response bodies: providers may echo sensitive request data.
            raise ProviderError(f"{self.name}: HTTP {exc.response.status_code}") from None
        except httpx.TimeoutException:
            raise ProviderError(f"{self.name}: request timed out") from None
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.name}: network error ({type(exc).__name__})") from None
        except (KeyError, IndexError, TypeError, ValueError):
            raise ProviderError(f"{self.name}: invalid API response") from None


class MultiProvider:
    """Try configured providers in order; continue after rate limits and outages."""

    def __init__(self, providers: list[LLMProvider]):
        if not providers:
            raise ValueError("At least one provider is required")
        self.providers = providers
        self.last_used: str | None = None
        self.used: list[str] = []
        self.models = {p.name: p.model for p in providers}

    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        failures: list[str] = []
        for provider in self.providers:
            try:
                result = provider.complete(system_prompt, user_prompt, temperature)
                self.last_used = provider.name
                self.used.append(provider.name)
                return result
            except ProviderError as exc:
                failures.append(str(exc))
        raise ProviderError("All configured providers failed: " + "; ".join(failures))


def create_provider(config: dict):
    """Build a single or failover provider from validated runtime configuration."""
    timeout = int(config.get("app", {}).get("request_timeout_seconds", 90))
    specs = config.get("providers") or []
    if not specs:
        legacy = config.get("provider", {})
        if legacy.get("base_url") and legacy.get("api_key") and legacy.get("model"):
            specs = [{
                "name": "ollama" if "127.0.0.1" in legacy["base_url"] or "localhost" in legacy["base_url"] else "custom",
                "base_url": legacy["base_url"],
                "api_key": legacy["api_key"],
                "model": legacy["model"],
            }]
    clients = [
        LLMProvider(
            spec["base_url"],
            spec["api_key"],
            spec["model"],
            timeout,
            spec.get("name", "custom"),
            spec.get("extra_headers"),
        )
        for spec in specs
        if spec.get("base_url") and spec.get("api_key") and spec.get("model")
    ]
    if not clients:
        return None
    if len(clients) == 1:
        return clients[0]
    return MultiProvider(clients)
