from __future__ import annotations
import httpx

class ProviderError(RuntimeError):
    pass

class LLMProvider:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 45):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        if not (self.base_url and self.api_key and self.model):
            raise ProviderError("Provider is not configured")
        url = self.base_url + "/chat/completions"
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
                url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            body = response.json()
            return body["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError(f"LLM provider request failed: {type(exc).__name__}: {exc}") from exc
