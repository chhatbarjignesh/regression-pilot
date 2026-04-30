"""
FastAPI application — CI webhook receiver + REST API for the dashboard.
"""
from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import settings
from agent.models import Framework, TestFailure, HealResult, HealStatus
from agent.orchestrator import Orchestrator
from agent.db import create_tables, close_engine, heal_repo

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("RegressionPilot starting up — creating DB tables")
    await create_tables()
    yield
    logger.info("RegressionPilot shutting down — closing DB engine")
    await close_engine()


app = FastAPI(
    title="RegressionPilot",
    description="AI agent that self-heals broken UI tests",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic request/response models ──────────────────────────────────

class FailurePayload(BaseModel):
    test_name: str
    test_file: str
    framework: str
    error_message: str
    stack_trace: str
    repo_path: str
    branch: str
    commit_sha: str
    page_url: str = ""
    ci_build_url: str = ""
    dom_snapshot: str = ""  # full page HTML captured at moment of failure


class HealResponse(BaseModel):
    run_id: str
    status: str


# ── Endpoints ──────────────────────────────────────────────────────────

@app.post("/webhook/failure", response_model=HealResponse, status_code=202)
async def receive_failure(
    payload: FailurePayload,
    background_tasks: BackgroundTasks,
) -> HealResponse:
    """CI posts here on test failure. Returns 202 immediately, heals in background."""
    run_id = str(uuid.uuid4())[:8]

    failure = TestFailure(
        test_name=payload.test_name,
        test_file=payload.test_file,
        framework=Framework(payload.framework),
        error_message=payload.error_message,
        stack_trace=payload.stack_trace,
        repo_path=payload.repo_path,
        branch=payload.branch,
        commit_sha=payload.commit_sha,
        ci_build_url=payload.ci_build_url,
        run_id=run_id,
        dom_snapshot=payload.dom_snapshot,
    )

    await heal_repo.create(run_id, payload.model_dump())
    background_tasks.add_task(_run_heal, run_id, failure, payload.page_url)

    return HealResponse(run_id=run_id, status=HealStatus.PENDING)


@app.get("/heal/{run_id}")
async def get_heal_status(run_id: str) -> dict[str, Any]:
    """Poll heal status for a given run_id."""
    event = await heal_repo.get(run_id)
    if not event:
        raise HTTPException(status_code=404, detail="Run not found")
    return event.to_dict()


@app.get("/heals")
async def list_heals(
    limit: int = 50,
    offset: int = 0,
    status: str = "",
    framework: str = "",
) -> dict[str, Any]:
    """Return paginated heal events for the dashboard."""
    events, total = await heal_repo.list(
        limit=limit,
        offset=offset,
        status=status or None,
        framework=framework or None,
    )
    return {
        "heals": [e.to_dict() for e in events],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/stats")
async def get_stats() -> dict[str, Any]:
    """Aggregate stats for dashboard metric cards."""
    return await heal_repo.get_stats()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


# ── Background task ────────────────────────────────────────────────────

async def _run_heal(run_id: str, failure: TestFailure, page_url: str) -> None:
    orchestrator = Orchestrator()
    try:
        result: HealResult = orchestrator.heal(failure, page_url)
        await heal_repo.update_from_result(run_id, result)
    except Exception as exc:
        logger.exception(f"[server] Heal failed for run {run_id}: {exc}")
        await heal_repo.update_status(run_id, HealStatus.FAILED, str(exc))
