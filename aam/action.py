from __future__ import annotations
import json
import os
from .config import load_config
from .orchestrator import run_task, render_markdown
from .provider import LLMProvider
from .github import post_issue_comment

def main():
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH missing")
    event = json.loads(open(event_path, encoding="utf-8").read())
    issue = event.get("issue") or {}
    repo = (event.get("repository") or {}).get("full_name") or os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise RuntimeError("Repository context missing")

    # The workflow only triggers for explicit /aam run or aam:run label.
    comment = event.get("comment") or {}
    command = (comment.get("body") or "").strip()
    labels = {x.get("name") for x in issue.get("labels", [])}
    if command != "/aam run" and "aam:run" not in labels:
        print("No explicit AAM trigger; exiting.")
        return

    body = (issue.get("body") or "").strip()
    title = (issue.get("title") or "Untitled issue").strip()
    task = f"Issue #{issue.get('number')}: {title}\n\n{body}"
    config = load_config()
    llm = None
    if not config["mock"]:
        p = config["provider"]
        llm = LLMProvider(p["base_url"], p["api_key"], p["model"], int(config["app"].get("request_timeout_seconds", 45)))
    report = run_task(task, config, llm)
    post_issue_comment(repo, int(issue["number"]), render_markdown(report))

if __name__ == "__main__":
    main()
