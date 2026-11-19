from __future__ import annotations
import json
import os
from .config import load_config
from .orchestrator import run_task, render_markdown
from .provider import build_provider
from .github import post_issue_comment

def main():
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH missing")
    with open(event_path, encoding="utf-8") as handle:
        event = json.load(handle)
    issue = event.get("issue") or {}
    repo = (event.get("repository") or {}).get("full_name") or os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise RuntimeError("Repository context missing")
    comment = event.get("comment") or {}
    command = (comment.get("body") or "").strip()
    labels = {x.get("name") for x in issue.get("labels", [])}
    if command != "/aam run" and "aam:run" not in labels:
        print("No explicit AAM trigger; exiting.")
        return
    task = f"Issue #{issue.get('number')}: {(issue.get('title') or 'Untitled issue').strip()}\n\n{(issue.get('body') or '').strip()}"
    config = load_config()
    if config["mock"]:
        raise RuntimeError("No hosted AI provider configured. Add at least one provider secret; mock mode is disabled for Issue runs.")
    llm = build_provider(config)
    report = run_task(task, config, llm)
    post_issue_comment(repo, int(issue["number"]), render_markdown(report))

if __name__ == "__main__":
    main()
