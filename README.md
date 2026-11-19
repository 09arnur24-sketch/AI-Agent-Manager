# AI Agent Manager (AAM)

A GitHub-Issues-driven multi-agent workflow runner. Researcher, Developer, and Reviewer generate an advisory report and publish it as an Issue comment.

## Hosted provider failover

The workflow tries configured providers in this order and moves to the next provider after a request failure:

1. Groq — OpenAI-compatible endpoint; default model: `llama-3.1-8b-instant`.
2. OpenRouter — default model: `openrouter/free`.
3. Cloudflare Workers AI — default model: `@cf/meta/llama-3.1-8b-instruct`.

Only providers with configured secrets are enabled. The workflow refuses to publish a mock report when no hosted provider is configured. Set optional model overrides as repository variables: `GROQ_MODEL`, `OPENROUTER_MODEL`, and `CLOUDFLARE_MODEL`.

## Required GitHub Actions secrets

- `GROQ_API_KEY`
- `OPENROUTER_API_KEY`
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

Never commit API keys or paste them into Issues, logs, or source files. Rotate any key that has been exposed.

## Run

1. Open or create a GitHub Issue.
2. Comment `/aam run` (or apply the `aam:run` label).
3. Open the Actions tab and inspect the AI Agent Manager run.
4. Read the report in the Issue comments or download the report artifact.

A workflow_dispatch run can also be started from Actions with a task description.

## Local mock tests

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m aam.cli --task "Design a small Python CLI" --mock
pytest -q
```

## Architecture

```
GitHub Issue
  -> GitHub Actions
  -> Groq -> OpenRouter -> Cloudflare Workers AI (configured providers only)
  -> Researcher -> Developer -> Reviewer
  -> Markdown/JSON report
  -> Issue comment + Actions artifact
```

## Safety and limitations

- Issue content is untrusted input.
- Model output is untrusted text and is never executed.
- The workflow has `contents: read` and `issues: write` permissions only.
- No automatic commits, branch pushes, deployments, or repository modifications.
- Provider availability, free quotas, rate limits, and model availability are controlled by each provider and can change.
- Provider failover does not guarantee unlimited free inference; the selected model and provider account terms determine usage limits.

## License

MIT. See `LICENSE`.
