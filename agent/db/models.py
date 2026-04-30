"""
SQLAlchemy ORM models for RegressionPilot.
All tables use UUID primary keys and UTC timestamps.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Float, Integer, String, Text, DateTime, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from agent.models import FailureType, Framework, HealStatus


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())[:8]


class Base(DeclarativeBase):
    pass


class HealEvent(Base):
    """One row per heal cycle triggered by a CI failure."""

    __tablename__ = "heal_events"

    # Identity
    run_id: Mapped[str] = mapped_column(String(8), primary_key=True, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    # Failure info
    test_name: Mapped[str] = mapped_column(String(500))
    test_file: Mapped[str] = mapped_column(String(500))
    framework: Mapped[str] = mapped_column(SAEnum(Framework), nullable=False)
    error_message: Mapped[str] = mapped_column(Text)
    stack_trace: Mapped[str] = mapped_column(Text, default="")
    repo_path: Mapped[str] = mapped_column(String(500), default="")
    branch: Mapped[str] = mapped_column(String(255), default="")
    commit_sha: Mapped[str] = mapped_column(String(40), default="")
    ci_build_url: Mapped[str] = mapped_column(String(1000), default="")

    # Classification
    failure_type: Mapped[str] = mapped_column(
        SAEnum(FailureType), nullable=False, default=FailureType.UNKNOWN
    )

    # Outcome
    status: Mapped[str] = mapped_column(
        SAEnum(HealStatus), nullable=False, default=HealStatus.PENDING
    )
    retries: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str] = mapped_column(Text, default="")

    # Fix details
    selector_before: Mapped[str] = mapped_column(Text, default="")
    selector_after: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, nullable=True)

    # Outputs
    jira_ticket: Mapped[str] = mapped_column(String(50), default="")
    pr_url: Mapped[str] = mapped_column(String(1000), default="")
    git_commit_sha: Mapped[str] = mapped_column(String(40), default="")
    time_saved_minutes: Mapped[float] = mapped_column(Float, default=0.0)

    def to_dict(self) -> dict:  # type: ignore[type-arg]
        return {
            "run_id": self.run_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "test_name": self.test_name,
            "test_file": self.test_file,
            "framework": self.framework,
            "error_message": self.error_message,
            "failure_type": self.failure_type,
            "status": self.status,
            "retries": self.retries,
            "error": self.error,
            "selector_before": self.selector_before,
            "selector_after": self.selector_after,
            "confidence": self.confidence,
            "jira_ticket": self.jira_ticket,
            "pr_url": self.pr_url,
            "commit_sha": self.git_commit_sha,
            "time_saved_minutes": self.time_saved_minutes,
            "ci_build_url": self.ci_build_url,
            "branch": self.branch,
        }
