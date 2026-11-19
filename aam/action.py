from __future__ import annotations
import json
import os
from .config import load_config
from .orchestrator import run_task, render_markdown
from .provider import create_provider
from .github import post_issue_comment


def main():
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH missing")
    with open(event_path, encoding="utf-8") as handle:
        event = json.loads(handle.read())
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

    body = (issue.get("body") or "").strip()
    title = (issue.get("title") or "Untitled issue").strip()
    task = f"Issue #{issue.get('number')}: {title}\n\n{body}"
    config = load_config()
    llm = None if config["mock"] else create_provider(config)
    if not config["mock"] and llm is None:
        raise RuntimeError("Hosted/local LLM mode requested but no provider is configured")
    report = run_task(task, config, llm)
    post_issue_comment(repo, int(issue["number"]), render_markdown(report))


if __name__ == "__main__":
    main()
