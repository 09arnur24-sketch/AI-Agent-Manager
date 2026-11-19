from __future__ import annotations
import argparse
import json
import os
from .config import load_config
from .orchestrator import run_task, render_markdown
from .provider import LLMProvider

def main():
    parser = argparse.ArgumentParser(description="AI Agent Manager")
    parser.add_argument("--task", required=True)
    parser.add_argument("--config")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()
    if args.mock:
        os.environ["AAM_MOCK"] = "1"
    config = load_config(args.config)
    llm = None
    if not config["mock"]:
        p = config["provider"]
        llm = LLMProvider(p["base_url"], p["api_key"], p["model"], int(config["app"].get("request_timeout_seconds", 45)))
    report = run_task(args.task, config, llm)
    print(render_markdown(report))

if __name__ == "__main__":
    main()
