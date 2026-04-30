"""
HealEventRepository — all database operations for HealEvent.
Keeps SQL out of the server/orchestrator layer.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select, desc, func

from agent.db.models import HealEvent
from agent.db.engine import get_session
from agent.models import HealResult, HealStatus, FailureType

logger = logging.getLogger(__name__)


class HealEventRepository:

    # ── Write operations ──────────────────────────────────────────────

    async def create(self, run_id: str, failure_payload: dict) -> HealEvent:  # type: ignore[type-arg]
        """Insert a new pending heal event. Called immediately on webhook receipt."""
        event = HealEvent(
            run_id=run_id,
            test_name=failure_payload.get("test_name", ""),
            test_file=failure_payload.get("test_file", ""),
            framework=failure_payload.get("framework", "playwright"),
            error_message=failure_payload.get("error_message", ""),
            stack_trace=failure_payload.get("stack_trace", ""),
            repo_path=failure_payload.get("repo_path", ""),
            branch=failure_payload.get("branch", ""),
            commit_sha=failure_payload.get("commit_sha", ""),
            ci_build_url=failure_payload.get("ci_build_url", ""),
            status=HealStatus.PENDING,
            failure_type=FailureType.UNKNOWN,
        )
        async with get_session() as session:
            session.add(event)
        logger.info(f"[db] Created heal event {run_id}")
        return event

    async def update_from_result(self, run_id: str, result: HealResult) -> None:
        """Update an existing event with the final heal outcome."""
        async with get_session() as session:
            event = await session.get(HealEvent, run_id)
            if not event:
                logger.warning(f"[db] HealEvent {run_id} not found for update")
                return

            event.status = result.status.value
            event.failure_type = result.failure_type.value
            event.retries = result.retries
            event.error = result.error

            if result.fix:
                event.selector_before = result.fix.selector_before
                event.selector_after = result.fix.selector_after
                event.confidence = result.fix.confidence

            event.jira_ticket = result.jira_ticket_key
            event.pr_url = result.pr_url
            event.git_commit_sha = result.commit_sha
            event.time_saved_minutes = result.time_saved_minutes

        logger.info(f"[db] Updated heal event {run_id} → {result.status.value}")

    async def update_status(self, run_id: str, status: HealStatus, error: str = "") -> None:
        """Quick status-only update (e.g. healing → failed on unexpected error)."""
        async with get_session() as session:
            event = await session.get(HealEvent, run_id)
            if event:
                event.status = status.value
                event.error = error

    # ── Read operations ───────────────────────────────────────────────

    async def get(self, run_id: str) -> Optional[HealEvent]:
        """Fetch a single heal event by run_id."""
        async with get_session() as session:
            return await session.get(HealEvent, run_id)

    async def list(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        framework: Optional[str] = None,
    ) -> tuple[list[HealEvent], int]:
        """
        List heal events, newest first.
        Returns (events, total_count).
        """
        async with get_session() as session:
            query = select(HealEvent).order_by(desc(HealEvent.created_at))
            count_query = select(func.count()).select_from(HealEvent)

            if status:
                query = query.where(HealEvent.status == status)
                count_query = count_query.where(HealEvent.status == status)
            if framework:
                query = query.where(HealEvent.framework == framework)
                count_query = count_query.where(HealEvent.framework == framework)

            total = (await session.execute(count_query)).scalar() or 0
            events = (await session.execute(query.limit(limit).offset(offset))).scalars().all()

        return list(events), int(total)

    async def get_stats(self) -> dict:  # type: ignore[type-arg]
        """Aggregate stats for the dashboard metric cards."""
        async with get_session() as session:
            rows = (
                await session.execute(
                    select(HealEvent.status, func.count().label("count"))
                    .group_by(HealEvent.status)
                )
            ).all()

            time_saved = (
                await session.execute(
                    select(func.sum(HealEvent.time_saved_minutes))
                )
            ).scalar() or 0.0

            avg_confidence = (
                await session.execute(
                    select(func.avg(HealEvent.confidence)).where(
                        HealEvent.confidence.is_not(None)
                    )
                )
            ).scalar() or 0.0

        counts = {row.status: row.count for row in rows}
        return {
            "healed":       counts.get(HealStatus.HEALED.value, 0),
            "failed":       counts.get(HealStatus.FAILED.value, 0),
            "quarantined":  counts.get(HealStatus.QUARANTINED.value, 0),
            "needs_review": counts.get(HealStatus.NEEDS_REVIEW.value, 0),
            "time_saved_minutes": round(float(time_saved), 1),
            "avg_confidence_pct": round(float(avg_confidence) * 100, 1),
        }


# Module-level singleton
heal_repo = HealEventRepository()
