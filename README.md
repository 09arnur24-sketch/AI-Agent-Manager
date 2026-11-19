# AI Agent Manager (AAM)

A GitHub-Issues-driven multi-agent workflow runner. Agents research, plan, review,
and publish an advisory report as an Issue comment.

## Features

- Trigger from an Issue comment: `/aam run`, or add the `aam:run` label.
- Three sequential AI roles: Researcher, Developer, Reviewer.
- **No external API key required:** GitHub Actions downloads and runs Ollama with
  the compact Qwen 2.5 0.5B model.
- Reports are uploaded as workflow artifacts and posted to the Issue.
- Mock mode remains available for local tests.
- Model output is treated as untrusted text; it is never executed.
- Least-privilege GitHub token permissions.

## Run

1. Open or create a GitHub Issue.
2. Comment `/aam run` (or apply the `aam:run` label).
3. Wait for Actions to download the model and run all three agents.
4. Read the report in the Issue comments or download it from the workflow artifacts.

You do not need to create API keys, configure repository secrets, or add provider
variables. The workflow starts a local Ollama server on its temporary GitHub-hosted
runner and downloads `qwen2.5:0.5b` for each fresh runner.

## Local mock run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m aam.cli --task "Design a small Python CLI" --mock
pytest
```

## Architecture

```
GitHub Issue
  -> GitHub Actions
  -> Ollama local inference server
  -> Researcher
  -> Developer
  -> Reviewer
  -> Markdown/JSON report
  -> Issue comment + Actions artifact
```

The three roles use the same local model with different system prompts. This is
sequential role-based orchestration, not three independently hosted models.

## Safety and limitations

- Issue content is untrusted input.
- The model has no repository write credentials.
- Generated commands are never executed.
- The workflow has `contents: read` and `issues: write` permissions only.
- No automatic commits, branch pushes, PR creation, deployments, or secret disclosure.
- The 0.5B model is intentionally small to fit a free GitHub-hosted runner; reasoning
  quality is limited compared with larger hosted models.
- Model download and CPU inference add startup time and may occasionally hit runner
  time limits or upstream download failures.

## License

MIT. See `LICENSE`.
