from pathlib import Path
import yaml
import pytest
from aam.orchestrator import run_task, render_markdown
from aam.config import DEFAULT_CONFIG
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


def test_hosted_llm_mode_and_model_in_report(tmp_path):
    class FakeLLM:
        name = "test-provider"
        model = "test-model"

        def complete(self, system_prompt, user_prompt, temperature=0.2):
            return f"Analysis for: {user_prompt[:30]}"

    cfg = config()
    cfg["mock"] = False
    result = run_task("Review a plan", cfg, llm=FakeLLM(), output_dir=str(tmp_path))
    assert result["mode"] == "hosted-llm"
    assert result["model"] == "test-model"
    assert result["provider"] == "test-provider"
    assert all(result["agents"].values())


def test_multi_provider_falls_back_after_primary_failure(tmp_path):
    class BrokenProvider:
        name = "primary"
        model = "primary-model"

        def complete(self, *args, **kwargs):
            raise ProviderError("primary: HTTP 429")

    class WorkingProvider:
        name = "backup"
        model = "backup-model"

        def complete(self, system_prompt, user_prompt, temperature=0.2):
            return "backup response"

    cfg = config()
    cfg["mock"] = False
    llm = MultiProvider([BrokenProvider(), WorkingProvider()])
    result = run_task("Review a plan", cfg, llm=llm, output_dir=str(tmp_path))
    assert result["mode"] == "multi-provider"
    assert result["providers_used"] == ["backup"]
    assert result["agents"]["researcher"] == "backup response"


def test_multi_provider_reports_all_failures_without_secrets():
    class BrokenProvider:
        def __init__(self, name):
            self.name = name
            self.model = "private-model"

        def complete(self, *args, **kwargs):
            raise ProviderError(f"{self.name}: HTTP 429")

    llm = MultiProvider([BrokenProvider("groq"), BrokenProvider("openrouter")])
    with pytest.raises(ProviderError, match="groq.*openrouter"):
        llm.complete("system", "task")
