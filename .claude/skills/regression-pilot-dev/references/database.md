# Database reference

## Stack

- PostgreSQL 16 (production + CI)
- SQLAlchemy 2.x async ORM (`sqlalchemy[asyncio]`)
- `asyncpg` driver
- Alembic for migrations

---

## Schema — heal_events table

| Column | Type | Notes |
|---|---|---|
| `run_id` | VARCHAR(8) PK | Short UUID, generated at webhook receipt |
| `created_at` | TIMESTAMPTZ | UTC, set on insert |
| `updated_at` | TIMESTAMPTZ | UTC, auto-updated on every write |
| `test_name` | VARCHAR(500) | |
| `test_file` | VARCHAR(500) | Relative path |
| `framework` | VARCHAR(20) | `playwright` or `selenium` |
| `error_message` | TEXT | |
| `stack_trace` | TEXT | |
| `repo_path` | VARCHAR(500) | |
| `branch` | VARCHAR(255) | |
| `commit_sha` | VARCHAR(40) | Git SHA of failing commit |
| `ci_build_url` | VARCHAR(1000) | |
| `failure_type` | VARCHAR(20) | `ui_change`, `real_bug`, `flaky`, `unknown` |
| `status` | VARCHAR(20) | `pending`, `healing`, `healed`, `failed`, `needs_review`, `quarantined` |
| `retries` | INTEGER | |
| `error` | TEXT | Error message if heal failed |
| `selector_before` | TEXT | Broken selector |
| `selector_after` | TEXT | Fixed selector |
| `confidence` | FLOAT | NULL for non-ui-change heals |
| `jira_ticket` | VARCHAR(50) | e.g. `QA-1042` |
| `pr_url` | VARCHAR(1000) | |
| `git_commit_sha` | VARCHAR(40) | SHA of the fix commit |
| `time_saved_minutes` | FLOAT | |

**Indexes**: `status`, `framework`, `created_at` (all B-tree).

---

## Session pattern

Always use the `get_session()` context manager — never create sessions manually:

```python
from agent.db.engine import get_session

async with get_session() as session:
    session.add(event)
    # auto-committed on clean exit
    # auto-rolled-back on exception
```

Never call `session.commit()` manually inside the block — the context manager handles it.

---

## Repository — HealEventRepository

All DB access goes through `agent/db/repository.py`. Never write ORM queries in server.py, orchestrator, or anywhere else.

Import the module-level singleton:
```python
from agent.db import heal_repo
```

### Writing a new query

Add a method to `HealEventRepository`:

```python
async def get_by_framework(self, framework: str) -> list[HealEvent]:
    async with get_session() as session:
        result = await session.execute(
            select(HealEvent)
            .where(HealEvent.framework == framework)
            .order_by(desc(HealEvent.created_at))
        )
        return list(result.scalars().all())
```

Return type: always `list[HealEvent]`, `Optional[HealEvent]`, `tuple[list[HealEvent], int]`, or a plain `dict` for aggregates.

---

## Migrations

### Apply all pending migrations
```bash
alembic upgrade head
```

### Generate a new migration after changing models.py
```bash
alembic revision --autogenerate -m "add column X to heal_events"
```
Then **review the generated file** in `alembic/versions/` before committing — autogenerate is not always 100% accurate, especially for enum columns.

### Roll back one migration
```bash
alembic downgrade -1
```

### Adding a new column — full workflow
1. Add the column to `HealEvent` in `agent/db/models.py`
2. Run `alembic revision --autogenerate -m "add X column"`
3. Review and edit the generated migration if needed
4. Run `alembic upgrade head` locally to test
5. Add the field to `HealEvent.to_dict()` so the API returns it
6. Update `heal_repo.update_from_result()` to populate the new field
7. Update dashboard mock data in `lib/api.js`

---

## Docker setup

`docker-compose.yml` runs PostgreSQL as a service with a healthcheck. The API container waits for the DB to be healthy, then runs `alembic upgrade head` before starting the server:

```yaml
command: >
  sh -c "alembic upgrade head && python -m agent.cli serve ..."
```

Connection string inside Docker uses the service name as host:
```
postgresql+asyncpg://postgres:postgres@db:5432/regression_pilot
```

Local development uses `localhost`:
```
postgresql+asyncpg://postgres:postgres@localhost:5432/regression_pilot
```

---

## CI setup

GitHub Actions spins up a `postgres:16-alpine` service container, then runs:
```yaml
- name: Run migrations
  env:
    DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/regression_pilot_test
  run: alembic upgrade head

- name: Run tests
  env:
    DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/regression_pilot_test
  run: pytest ...
```

Tests use a separate `regression_pilot_test` database so they don't pollute production data.