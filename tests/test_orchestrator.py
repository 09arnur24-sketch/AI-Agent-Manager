from pathlib import Path
import yaml
import pytest
from aam.orchestrator import run_task, render_markdown
from aam.config import DEFAULT_CONFIG

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

def test_report_marks_advisory():
    result = run_task("Check a design", config(), output_dir="/tmp/aam-test-report")
    markdown = render_markdown(result)
    assert "No repository files were changed" in markdown
