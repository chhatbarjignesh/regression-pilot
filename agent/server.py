"""
FastAPI application — CI webhook receiver + REST API for the dashboard.
"""
from __future__ import annotations
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import settings
from agent.models import Framework, TestFailure, HealResult, HealStatus
from agent.orchestrator import Orchestrator

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# In-memory store for demo (replace with DB in production)
_heal_log: dict[str, dict[str, Any]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("RegressionPilot starting up")
    yield
    logger.info("RegressionPilot shutting down")


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


# ── Pydantic request/response models ────────────────────────────────────


class FailurePayload(BaseModel):
    test_name: str
    test_file: str
    framework: str          # "playwright" or "selenium"
    error_message: str
    stack_trace: str
    repo_path: str
    branch: str
    commit_sha: str
    page_url: str = ""
    ci_build_url: str = ""


class HealResponse(BaseModel):
    run_id: str
    status: str


# ── Endpoints ────────────────────────────────────────────────────────────


@app.post("/webhook/failure", response_model=HealResponse, status_code=202)
async def receive_failure(payload: FailurePayload, background_tasks: BackgroundTasks) -> HealResponse:
    """
    CI pipeline posts here when a test fails.
    Immediately returns 202 Accepted and heals in the background.
    """
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
    )
    _heal_log[run_id] = {"status": HealStatus.PENDING, "failure": payload.model_dump()}
    background_tasks.add_task(_run_heal, run_id, failure, payload.page_url)
    return HealResponse(run_id=run_id, status=HealStatus.PENDING)


@app.get("/heal/{run_id}")
async def get_heal_status(run_id: str) -> dict[str, Any]:
    """Poll heal status for a given run_id."""
    if run_id not in _heal_log:
        raise HTTPException(status_code=404, detail="Run not found")
    return _heal_log[run_id]


@app.get("/heals")
async def list_heals(limit: int = 50) -> dict[str, Any]:
    """Return the most recent heal events for the dashboard."""
    items = list(_heal_log.values())[-limit:]
    return {"heals": items, "total": len(_heal_log)}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


# ── Background task ──────────────────────────────────────────────────────


async def _run_heal(run_id: str, failure: TestFailure, page_url: str) -> None:
    orchestrator = Orchestrator()
    try:
        result: HealResult = orchestrator.heal(failure, page_url)
        _heal_log[run_id] = {
            "run_id": run_id,
            "status": result.status,
            "failure_type": result.failure_type,
            "test_name": failure.test_name,
            "test_file": failure.test_file,
            "jira_ticket": result.jira_ticket_key,
            "pr_url": result.pr_url,
            "commit_sha": result.commit_sha,
            "confidence": result.fix.confidence if result.fix else None,
            "selector_before": result.fix.selector_before if result.fix else None,
            "selector_after": result.fix.selector_after if result.fix else None,
            "time_saved_minutes": result.time_saved_minutes,
            "retries": result.retries,
            "error": result.error,
        }
    except Exception as exc:
        logger.exception(f"[server] Heal failed for run {run_id}: {exc}")
        _heal_log[run_id]["status"] = HealStatus.FAILED
        _heal_log[run_id]["error"] = str(exc)
