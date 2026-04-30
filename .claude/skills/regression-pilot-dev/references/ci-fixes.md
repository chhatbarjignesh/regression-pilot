# CI fixes log

A running log of CI failures and how they were fixed. Check here before debugging a new CI error.

---

## hatchling: "Unable to determine which files to ship"

**Symptom**: `pip install -e ".[dev]"` fails with `ValueError: Unable to determine which files to ship`

**Cause**: hatchling looks for a folder named after the project (`regression_pilot`) and can't find it — folders are named `agent`, `adapters`, `config`.

**Fix**: Add to `pyproject.toml`:
```toml
[tool.hatch.build.targets.wheel]
packages = ["agent", "adapters", "config"]
```

---

## hatchling: "Readme file does not exist: README.md" (Docker)

**Symptom**: Docker build fails at `pip install -e ".[dev]"` with `OSError: Readme file does not exist: README.md`

**Cause**: Dockerfile copies `pyproject.toml` alone for layer caching, then runs pip install — but `README.md` (referenced in pyproject.toml) isn't present yet.

**Fix**: Copy both files together in Dockerfile:
```dockerfile
# Before (broken)
COPY pyproject.toml .

# After (fixed)
COPY pyproject.toml README.md ./
```

---

## mypy: "Source file found twice under different module names"

**Symptom**: `config/settings.py: error: Source file found twice under different module names: "settings" and "config.settings"`

**Cause**: `config/` was missing `__init__.py` so mypy didn't treat it as a package, picking up `settings.py` twice.

**Fix**:
1. Create `config/__init__.py` (empty file)
2. Add to `pyproject.toml` `[tool.mypy]`:
```toml
explicit_package_bases = true
mypy_path = "."
```
3. CI command: `mypy --explicit-package-bases --ignore-missing-imports agent/ adapters/ config/`

---

## mypy: union-attr on response.content[0].text

**Symptom**: Multiple errors like `Item "ThinkingBlock" of "TextBlock | ThinkingBlock | ..." has no attribute "text"`

**Cause**: Anthropic SDK types `response.content` as a union of many block types, only `TextBlock` has `.text`.

**Fix**: Guard with `hasattr` before accessing `.text`:
```python
block = response.content[0]
if not hasattr(block, "text"):
    return fallback_value
raw = block.text.strip()  # type: ignore[union-attr]
```

---

## mypy: "Incompatible types in assignment" on Playwright _pw field

**Symptom**: `adapters/playwright_adapter.py: error: Incompatible types in assignment (expression has type "Playwright", variable has type "None")`

**Cause**: `self._pw = None` without annotation — mypy infers type as `None`, then rejects the real assignment.

**Fix**:
```python
from typing import Optional
from playwright.sync_api import Playwright

self._pw: Optional[Playwright] = None
```

---

## mypy: "Returning Any" from httpx JSON responses

**Symptom**: `error: Returning Any from function declared to return "str"` on lines accessing `resp.json()`

**Cause**: `httpx`'s `resp.json()` returns `Any`. Returning it from a typed function fails strict mode.

**Fix**:
```python
# git_agent.py
pr_url: str = resp.json().get("html_url", "")

# jira_agent.py
return str(resp.json()["key"])
```

---

## mypy: "Function is missing a return type annotation"

**Symptom**: Errors on FastAPI endpoint functions and Typer CLI functions.

**Fix**: Add explicit return types to all functions:
```python
# server.py
async def health() -> dict[str, str]: ...
async def list_heals(limit: int = 50) -> dict[str, Any]: ...
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]: ...

# cli.py
def serve(...) -> None: ...
def heal(...) -> None: ...
```

---

## mypy: ignore_missing_imports

**Symptom**: `Cannot find implementation or library stub for module named "selenium"` / `"uvicorn"`

**Cause**: These packages don't ship mypy stubs.

**Fix**: Add to `pyproject.toml`:
```toml
[tool.mypy]
ignore_missing_imports = true
```

---

## ruff: common violations

| Error | File | Fix |
|---|---|---|
| `F401` unused import `re` | `adapters/selenium_adapter.py` | Remove `import re` |
| `F401` unused import `json` | `agent/cli.py` | Remove `import json` |
| `F401` unused `Framework` | `agent/detector.py`, `agent/fix_generator.py` | Remove from import |
| `F401` unused `FailureType`, `FixProposal` | `agent/jira_agent.py` | Remove from import |
| `F401` unused `tempfile` | `agent/test_runner.py` | Remove `import tempfile` |
| `F401` unused `pytest` | `tests/test_detector.py` | Remove `import pytest` |
| `E741` ambiguous var `l` | `agent/fix_generator.py` | Rename to `line` |
| `F841` assigned but unused `fix` | `agent/jira_agent.py` | Remove `fix = result.fix` line |

---

## asyncpg: "cannot perform operation: another operation is in progress"

**Symptom**: Random test failures with asyncpg connection errors under concurrent load.

**Cause**: Sharing a single session across async tasks.

**Fix**: Always use `get_session()` as a context manager per operation — never share sessions between coroutines. Each `async with get_session()` gets its own connection from the pool.

---

## alembic: "Target database is not up to date"

**Symptom**: `alembic upgrade head` fails or app starts with schema mismatch.

**Cause**: Migration file exists but wasn't applied (usually first-time setup or new column added without generating migration).

**Fix**:
```bash
alembic upgrade head         # apply pending migrations
alembic current              # check current revision
alembic history              # see all revisions
```

---

## SQLAlchemy: "greenlet_spawn has not been called"

**Symptom**: `MissingGreenlet` error at runtime when using async SQLAlchemy.

**Cause**: Missing `greenlet` package or using sync SQLAlchemy patterns in async context.

**Fix**: Ensure `greenlet>=3.0.3` is in dependencies. Never use `session.execute()` outside an `async with` block.