---
name: regression-pilot-dev
description: >
  Development skill for the RegressionPilot open-source project — an AI agent
  that self-heals broken Playwright and Selenium UI tests. Use this skill whenever
  the user asks to add a feature, fix a bug, write tests, refactor code, or do
  anything else related to the RegressionPilot codebase. Trigger on any mention
  of: regression-pilot, self-healing tests, the orchestrator, DOM inspector,
  fix generator, detector agent, Jira agent, git agent, dashboard, or any file
  path inside the project (agent/, adapters/, config/, dashboard/). Also trigger
  when the user pastes a CI error, mypy error, ruff error, or pytest failure
  from this project — even without explicitly naming RegressionPilot.
---

# RegressionPilot — developer skill

Read `references/architecture.md` before touching any code.
Read `references/conventions.md` before writing or reviewing any Python.
Read `references/dashboard.md` before touching anything in `dashboard/`.

---

## What this project is

RegressionPilot is an open-source AI agent that self-heals broken UI tests.

When a Playwright or Selenium test breaks due to a UI change, the agent:
1. **Detects** the failure via CI/CD webhook (FastAPI)
2. **Classifies** it — UI change vs real bug vs flaky (Claude API + heuristics)
3. **Inspects** the current DOM to find what changed
4. **Generates** a fix using Claude (rewrites the broken selector/step)
5. **Verifies** by re-running the test
6. **Commits** the fixed file and opens a GitHub PR
7. **Logs** a maintenance entry or bug ticket in Jira Cloud

---

## Repo layout

```
regression-pilot/
├── agent/
│   ├── models.py          # All shared dataclasses (TestFailure, HealResult, etc.)
│   ├── detector.py        # Failure classifier — heuristic + Claude
│   ├── dom_inspector.py   # DOM differ, broken selector extractor
│   ├── fix_generator.py   # Claude-powered selector rewriter
│   ├── test_runner.py     # Applies fix, re-runs test (Playwright or Selenium)
│   ├── git_agent.py       # Commits fixed file, opens GitHub PR
│   ├── jira_agent.py      # Jira Cloud REST API — maintenance log + bug tickets
│   ├── orchestrator.py    # Master agent loop
│   ├── server.py          # FastAPI webhook server
│   ├── cli.py             # Typer CLI (serve / heal commands)
│   └── db/
│       ├── models.py      # HealEvent SQLAlchemy ORM model
│       ├── engine.py      # Async engine, session factory, create_tables()
│       ├── repository.py  # HealEventRepository — all DB queries
│       └── __init__.py
├── adapters/
│   ├── base.py            # BrowserAdapter ABC
│   ├── playwright_adapter.py
│   └── selenium_adapter.py
├── config/
│   ├── __init__.py
│   └── settings.py        # Pydantic settings — reads from .env
├── dashboard/             # React + Vite frontend
│   └── src/
│       ├── App.jsx        # Main dashboard
│       ├── components/    # StatusBadge, ConfidenceBar, SelectorDiff, Charts, HealDrawer, MetricCard
│       ├── hooks/useHeals.js
│       └── lib/api.js     # API client + mock data
├── alembic/
│   ├── env.py             # Async-compatible migration runner
│   └── versions/
│       └── 0001_initial.py  # Creates heal_events table
├── alembic.ini
├── tests/
│   └── test_detector.py
├── pyproject.toml         # hatchling build, ruff, mypy, pytest config
├── Dockerfile             # python:3.11-slim
└── docker-compose.yml
```

---

## Key data models (agent/models.py)

| Model | Purpose |
|---|---|
| `TestFailure` | Incoming CI failure — test name, file, framework, error, stack, repo info |
| `FailureType` | Enum: `ui_change`, `real_bug`, `flaky`, `unknown` |
| `Framework` | Enum: `playwright`, `selenium` |
| `DOMDiff` | Broken selector + old/new HTML context + candidate replacements |
| `FixProposal` | AI-generated fix — original/fixed code, confidence score, selectors |
| `HealResult` | Final outcome — status, Jira key, PR URL, commit SHA, time saved |
| `HealStatus` | Enum: `pending`, `healing`, `healed`, `failed`, `needs_review`, `quarantined` |

---

## Agent loop (orchestrator.py)

```
classify → ui_change → inspect DOM → generate fix → run test
                                                        ↓ pass
                                              commit + PR + Jira log → HEALED
                                                        ↓ fail (retry up to 3x)
                                              → FAILED after max retries

         → real_bug  → file Jira bug ticket → FAILED
         → flaky     → mark quarantined in Jira → QUARANTINED
         → unknown   → NEEDS_REVIEW
```

Confidence threshold (`settings.confidence_threshold`, default 0.75):
- Above → auto-commit
- Below → draft PR, route to needs_review

---

## Environment variables (.env)

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `AI_MODEL` | Default: `claude-sonnet-4-20250514` |
| `JIRA_BASE_URL` | e.g. `https://yourco.atlassian.net` |
| `JIRA_EMAIL` | Atlassian account email |
| `JIRA_API_TOKEN` | Jira Cloud API token |
| `JIRA_PROJECT_KEY` | e.g. `QA` |
| `GITHUB_TOKEN` | PAT with `repo` scope |
| `GITHUB_REPO` | e.g. `yourorg/regression-pilot` |
| `GITHUB_DEFAULT_BRANCH` | Default: `main` |
| `CONFIDENCE_THRESHOLD` | Default: `0.75` |
| `MAX_FIX_RETRIES` | Default: `3` |
| `TEST_TIMEOUT_SECONDS` | Default: `60` |

---

## CI pipeline (GitHub Actions)

Four steps in order — all must pass:
1. `ruff check .` — linting
2. `mypy --explicit-package-bases --ignore-missing-imports agent/ adapters/ config/` — type check
3. `alembic upgrade head` — run migrations against test DB (postgres service in CI)
4. `pytest --cov=agent --cov=adapters --cov-report=term-missing -q` — tests

Docker build runs only on `main` after tests pass.

Common CI failure patterns → see `references/ci-fixes.md`

---

## How to run locally

```bash
# Backend
cp .env.example .env   # fill in keys
pip install -e ".[dev]"
playwright install chromium
python -m agent.cli serve --reload

# Dashboard (separate terminal)
cd dashboard && npm install && npm run dev
# → http://localhost:5173 (works standalone with mock data)

# Full stack
docker-compose up
```

---

## Adding a new feature — checklist

1. Read the relevant reference file first
2. Update `agent/models.py` if new data fields are needed
3. Keep adapter pattern clean — Playwright/Selenium logic stays in `adapters/`, never in `agent/`
4. All new Python files: add type annotations, run `ruff check` + `mypy` before committing
5. Add or update tests in `tests/`
6. New DB columns: add to `agent/db/models.py`, generate migration with `alembic revision --autogenerate -m "description"`, review the generated file in `alembic/versions/`
7. Dashboard changes: update `lib/api.js` mock data AND `agent/db/repository.py` `to_dict()` / `get_stats()` to reflect new fields

---

## Reference files

- `references/architecture.md` — deep dive on each agent module
- `references/conventions.md` — Python style, type annotation rules, error handling patterns
- `references/dashboard.md` — React component guide, mock data schema, API contract
- `references/ci-fixes.md` — log of past CI failures and their fixes (check here before debugging)
- `references/database.md` — DB schema, repository patterns, migration workflow