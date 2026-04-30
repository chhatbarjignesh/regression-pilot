from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FailureType(str, Enum):
    UI_CHANGE = "ui_change"
    REAL_BUG = "real_bug"
    FLAKY = "flaky"
    UNKNOWN = "unknown"


class Framework(str, Enum):
    PLAYWRIGHT = "playwright"
    SELENIUM = "selenium"


class HealStatus(str, Enum):
    PENDING = "pending"
    HEALING = "healing"
    HEALED = "healed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"
    QUARANTINED = "quarantined"


@dataclass
class TestFailure:
    """Represents an incoming test failure from CI."""
    test_name: str
    test_file: str
    framework: Framework
    error_message: str
    stack_trace: str
    repo_path: str
    branch: str
    commit_sha: str
    ci_build_url: str = ""
    run_id: str = ""


@dataclass
class DOMDiff:
    """The result of comparing old vs new DOM around the broken selector."""
    broken_selector: str
    broken_line: int
    old_html_snippet: str
    new_html_snippet: str
    suggested_selectors: list[str] = field(default_factory=list)
    page_url: str = ""


@dataclass
class FixProposal:
    """AI-generated fix for a broken test step."""
    original_code: str
    fixed_code: str
    explanation: str
    confidence: float          # 0.0 – 1.0
    selector_before: str = ""
    selector_after: str = ""
    needs_human_review: bool = False


@dataclass
class HealResult:
    """Final outcome of a full self-healing cycle."""
    failure: TestFailure
    failure_type: FailureType
    fix: Optional[FixProposal]
    status: HealStatus
    retries: int = 0
    jira_ticket_key: str = ""
    pr_url: str = ""
    commit_sha: str = ""
    time_saved_minutes: float = 0.0
    error: str = ""
