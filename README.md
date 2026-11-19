# AI Agent Manager (AAM)

A GitHub-Issues-driven multi-agent workflow runner. The first release is intentionally
read-only: agents research, plan, propose implementation steps, review one another,
and publish a report as an Issue comment. It does not execute model-generated shell
commands, edit repository files, or merge pull requests.

## Features

- GitHub Actions entry point (`/aam run` comment or `aam:run` label).
- Three cooperating agents: Researcher, Developer, Reviewer.
- Mock mode works without an API key.
- OpenAI-compatible provider adapter for free-tier providers such as Groq or OpenRouter.
- Structured JSONL audit log and Markdown reports.
- Tests run without network access.
- Least-privilege GitHub token permissions.

## Quick start

1. Add these files to a GitHub repository.
2. In **Settings → Secrets and variables → Actions**, add:
   - `AAM_API_KEY` (optional in mock mode; use a provider-issued key if enabling a hosted model).
3. Add repository variable `AAM_API_BASE_URL` (for example, the provider's OpenAI-compatible `/v1` URL)
   and `AAM_MODEL` (a model identifier currently available on your provider's free tier).
4. Add label `aam:run` to an Issue, or comment `/aam run`.
5. Open the Actions tab and inspect the run summary / Issue comment.

No OpenAI API key is required. No provider is hardcoded; free model availability and quotas
change, so choose a currently free model on the provider's dashboard.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m aam.cli --task "Design a small Python CLI" --mock
pytest
```

Hosted model mode:

```bash
export AAM_API_KEY="..."
export AAM_API_BASE_URL="https://api.provider.example/v1"
export AAM_MODEL="provider/model-id"
python -m aam.cli --task "Review this architecture"
```

## Safety model

- Issue content is untrusted data, never instructions to the workflow runner.
- The model receives a task prompt, not repository write credentials.
- Model output is treated as text and is never executed.
- The workflow has `contents: read` and `issues: write` only.
- No automatic commits, branch pushes, PR creation, deployments, or secret disclosure.
- Review output is advisory; a human decides what to implement.

## Architecture

`GitHub Issue → GitHub Actions → Orchestrator → Researcher → Developer → Reviewer → Report → Issue comment`

The provider adapter uses the OpenAI-compatible Chat Completions API. It can target any compatible
provider endpoint; it does not imply that the provider has a permanent free tier.

## Configuration

See `config/agents.yml`. Environment variables override YAML:

- `AAM_API_KEY`
- `AAM_API_BASE_URL`
- `AAM_MODEL`
- `AAM_MOCK` (`1`/`true` to force mock mode)

## Roadmap

- v0.1: issue-triggered multi-agent analysis, mock provider, tests, audit report.
- v0.2: repository context ingestion with strict file allowlist and size limits.
- v0.3: optional patch proposals as artifacts (still no auto-apply).
- v0.4: human-approved PR creation.
- v1.0: dashboard and run history.

## License

MIT. See `LICENSE`.
