from __future__ import annotations
import argparse
import os
from .config import load_config
from .orchestrator import run_task, render_markdown
from .provider import create_provider


def main():
    parser = argparse.ArgumentParser(description="AI Agent Manager")
    parser.add_argument("--task", required=True)
    parser.add_argument("--config")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()
    if args.mock:
        os.environ["AAM_MOCK"] = "1"
    config = load_config(args.config)
    llm = None if config["mock"] else create_provider(config)
    if not config["mock"] and llm is None:
        raise RuntimeError("LLM mode requested but no provider is configured")
    report = run_task(args.task, config, llm)
    print(render_markdown(report))


if __name__ == "__main__":
    main()
