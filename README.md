# RegressionPilot 🤖

> AI agent that self-heals broken UI tests for Playwright and Selenium

[![CI](https://github.com/yourorg/regression-pilot/actions/workflows/ci.yml/badge.svg)](https://github.com/yourorg/regression-pilot/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## What it does

When a Playwright or Selenium test breaks due to a UI change, RegressionPilot:

1. **Detects** the failure via CI webhook
2. **Classifies** it — UI change, real bug, or flaky test
3. **Inspects** the new DOM and finds what changed
4. **Generates** a fix using Claude AI (rewrites the broken selector/step)
5. **Verifies** by re-running the test
6. **Commits** the fixed test and opens a GitHub PR
7. **Logs** a maintenance entry in Jira

All without human intervention.

---

## Quickstart

```bash
# 1. Clone
git clone https://github.com/yourorg/regression-pilot.git
cd regression-pilot

# 2. Configure
cp .env.example .env
# Edit .env with your API keys

# 3. Run with Docker
docker-compose up

# 4. Or run locally
pip install -e ".[dev]"
playwright install chromium
python -m agent.cli serve
```

The webhook server starts at `http://localhost:8000`.

---

## CI integration

Add this step to your GitHub Actions workflow:

```yaml
- name: Notify RegressionPilot on failure
  if: failure()
  run: |
    curl -X POST https://your-regression-pilot-url/webhook/failure \
      -H "Content-Type: application/json" \
      -d '{
        "test_name": "${{ env.FAILED_TEST }}",
        "test_file": "${{ env.FAILED_FILE }}",
        "framework": "playwright",
        "error_message": "${{ env.ERROR_MSG }}",
        "stack_trace": "${{ env.STACK_TRACE }}",
        "repo_path": "${{ github.workspace }}",
        "branch": "${{ github.ref_name }}",
        "commit_sha": "${{ github.sha }}",
        "ci_build_url": "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
      }'
```

---

## Architecture

```
CI failure → Failure Detector → DOM Inspector → AI Fix Generator (Claude)
                                                        ↓
                                               Test Runner (verify fix)
                                                        ↓
                                          Git Agent (commit + PR) + Jira Logger
```

### Confidence scoring

Every AI-generated fix gets a confidence score (0–1):
- **≥ 0.75** → auto-committed, PR opened
- **< 0.75** → draft PR opened, routed to human review queue

Tune via `CONFIDENCE_THRESHOLD` in `.env`.

---

## Project structure

```
regression-pilot/
├── agent/
│   ├── orchestrator.py   # Main agent loop
│   ├── detector.py       # Failure classifier
│   ├── dom_inspector.py  # DOM differ
│   ├── fix_generator.py  # Claude-powered fix writer
│   ├── test_runner.py    # Applies fix & re-runs test
│   ├── git_agent.py      # Commits + opens PR
│   ├── jira_agent.py     # Jira Cloud integration
│   ├── server.py         # FastAPI webhook server
│   └── cli.py            # Typer CLI
├── adapters/
│   ├── base.py           # Adapter interface
│   ├── playwright_adapter.py
│   └── selenium_adapter.py
├── dashboard/            # React frontend (heal log + metrics)
├── config/
│   └── settings.py
└── tests/
```

---

## Environment variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `JIRA_BASE_URL` | e.g. `https://yourco.atlassian.net` |
| `JIRA_EMAIL` | Your Atlassian account email |
| `JIRA_API_TOKEN` | Jira Cloud API token |
| `JIRA_PROJECT_KEY` | e.g. `QA` |
| `GITHUB_TOKEN` | GitHub PAT with `repo` scope |
| `GITHUB_REPO` | e.g. `yourorg/yourrepo` |
| `CONFIDENCE_THRESHOLD` | Default `0.75` — below this = human review |
| `MAX_FIX_RETRIES` | Default `3` |

---

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md). PRs welcome!

---

## License

MIT © 2025 — Built with ❤️
