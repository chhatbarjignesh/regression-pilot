# Python conventions

## General rules

- Python 3.11+, all files start with `from __future__ import annotations`
- `ruff` for linting (line length 100), `mypy` strict mode for types
- All functions need return type annotations — mypy strict will fail otherwise
- Logger per module: `logger = logging.getLogger(__name__)`

---

## Type annotation patterns

### Claude API response blocks
Never access `.text` directly on `response.content[0]` — it's a union type and mypy strict will reject it:

```python
# WRONG — mypy error: union-attr
raw = response.content[0].text.strip()

# RIGHT — guard with hasattr
block = response.content[0]
if not hasattr(block, "text"):
    return some_fallback
raw = block.text.strip()  # type: ignore[union-attr]
```

### Optional fields
Use `Optional[X]` from `typing` (not `X | None`) for class-level fields that start as `None`:
```python
from typing import Optional
from playwright.sync_api import Playwright

self._pw: Optional[Playwright] = None   # correct
self._pw = None                          # wrong — mypy can't infer type
```

### httpx JSON responses
`resp.json()` returns `Any` — always wrap or cast:
```python
pr_url: str = resp.json().get("html_url", "")   # explicit annotation
key = str(resp.json()["key"])                    # explicit cast
```

### Selenium page_source
`driver.page_source` returns `Any` in Selenium stubs — always cast:
```python
return str(self._driver.page_source)
```

### FastAPI async functions
All endpoint and lifespan functions need return types:
```python
async def health() -> dict[str, str]: ...
async def list_heals(limit: int = 50) -> dict[str, Any]: ...
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]: ...
```

### CLI functions (Typer)
Always add `-> None`:
```python
def serve(...) -> None: ...
def heal(...) -> None: ...
```

---

## Ruff rules — common violations to avoid

| Error | Fix |
|---|---|
| `F401` imported but unused | Remove the import |
| `E741` ambiguous variable name | Never use `l`, `O`, `I` as variable names |
| `F841` assigned but never used | Remove the assignment |

Run before every commit: `ruff check .`
Auto-fix safe issues: `ruff check . --fix`

---

## Error handling patterns

### Agent methods — never let exceptions bubble to orchestrator unhandled
```python
try:
    result = self._do_thing()
except Exception as exc:
    logger.warning(f"[module] step failed: {exc}")
    return fallback_value
```

### Orchestrator — always returns HealResult, never raises
The top-level `orchestrator.heal()` wraps everything in `try/except Exception` and sets `result.status = HealStatus.FAILED` with `result.error = str(exc)`.

---

## Import order (ruff enforces this)

```python
from __future__ import annotations
# stdlib
import json
import logging
# third party
from anthropic import Anthropic
from fastapi import FastAPI
# local
from config.settings import settings
from agent.models import TestFailure
```

---

## Adding a new agent module

1. Create `agent/new_agent.py`
2. Add logger: `logger = logging.getLogger(__name__)`
3. Class with `__init__` injecting dependencies (settings, client)
4. Public methods typed end-to-end
5. Import and instantiate in `orchestrator.py`
6. Add `from agent.new_agent import NewAgent` — check for unused imports immediately

---

## Testing patterns

Tests live in `tests/`. Use `unittest.mock.patch` and `MagicMock` for external dependencies (Claude API, httpx, git, Jira).

```python
from unittest.mock import MagicMock, patch

@patch("agent.detector.Anthropic")
def test_ai_classify(self, mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value.content = [
        MagicMock(text="real_bug")
    ]
    # ... assert
```

Run: `pytest --cov=agent --cov=adapters --cov-report=term-missing -q`