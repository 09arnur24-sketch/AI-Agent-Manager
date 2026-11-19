from __future__ import annotations
import os
import httpx

def post_issue_comment(repository: str, issue_number: int, body: str) -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not available")
    url = f"https://api.github.com/repos/{repository}/issues/{issue_number}/comments"
    response = httpx.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"body": body[:60000]},
        timeout=30,
    )
    response.raise_for_status()
