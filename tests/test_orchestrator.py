from pathlib import Path
import yaml
import pytest
from aam.orchestrator import run_task, render_markdown
from aam.config import DEFAULT_CONFIG, load_config
from aam.provider import MultiProvider, ProviderError

def config():
    data = yaml.safe_load(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    data["mock"] = True
    return data

def test_mock_run_creates_report(tmp_path):
    result = run_task("Build a safe task tracker", config(), output_dir=str(tmp_path))
    assert result["mode"] == "mock"
    assert set(result["agents"]) == {"researcher", "developer", "reviewer"}
    assert list(tmp_path.glob("report-*.md"))
    assert (tmp_path / "audit.jsonl").exists()

def test_empty_task_rejected(tmp_path):
    with pytest.raises(ValueError, match="empty"):
        run_task("   ", config(), output_dir=str(tmp_path))

def test_task_limit_enforced(tmp_path):
    cfg = config()
    cfg["app"]["max_task_chars"] = 5
    with pytest.raises(ValueError, match="exceeds"):
        run_task("this task is too long", cfg, output_dir=str(tmp_path))

def test_report_marks_advisory(tmp_path):
    result = run_task("Check a design", config(), output_dir=str(tmp_path))
    markdown = render_markdown(result)
    assert "No repository files were changed" in markdown

def test_llm_mode_requires_provider(tmp_path):
    cfg = config()
    cfg["mock"] = False
    with pytest.raises(RuntimeError, match="no provider"):
        run_task("Review a plan", cfg, llm=None, output_dir=str(tmp_path))

def test_local_llm_mode_and_model_in_report(tmp_path):
    class FakeLLM:
        def complete(self, system_prompt, user_prompt, temperature=0.2):
            return f"Analysis for: {user_prompt[:30]}"

    cfg = config()
    cfg["mock"] = False
    cfg["provider"]["model"] = "qwen2.5:0.5b"
    result = run_task("Review a plan", cfg, llm=FakeLLM(), output_dir=str(tmp_path))
    assert result["mode"] == "local-llm"
    assert result["model"] == "qwen2.5:0.5b"
    assert all(result["agents"].values())

def test_multi_provider_falls_back_after_error():
    class Broken:
        def complete(self, *args, **kwargs):
            raise ProviderError("HTTP 429")
    class Working:
        def complete(self, *args, **kwargs):
            return "real response"
    client = MultiProvider([("first", Broken()), ("second", Working())])
    assert client.complete("system", "task") == "real response"
    assert client.used == ["second"]

def test_multi_provider_fails_when_all_providers_fail():
    class Broken:
        def complete(self, *args, **kwargs):
            raise ProviderError("HTTP 503")
    client = MultiProvider([("one", Broken()), ("two", Broken())])
    with pytest.raises(ProviderError, match="All configured providers failed"):
        client.complete("system", "task")

def test_load_config_enables_only_providers_with_secrets(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-groq")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "test-cf")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "account")
    monkeypatch.delenv("AAM_MOCK", raising=False)
    cfg = load_config()
    assert [p["name"] for p in cfg["providers"]] == ["groq", "cloudflare"]
    assert cfg["mock"] is False
    assert cfg["runtime_mode"] == "multi-provider"

def test_load_config_uses_mock_when_no_secrets(monkeypatch):
    for key in ("GROQ_API_KEY", "OPENROUTER_API_KEY", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID", "AAM_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("AAM_MOCK", raising=False)
    cfg = load_config()
    assert cfg["providers"] == []
    assert cfg["mock"] is True
