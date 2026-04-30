"""
Orchestrator
The central agent loop. Called by the FastAPI webhook endpoint or CLI.
Runs the full detect → inspect → fix → verify → commit → log cycle.
"""
from __future__ import annotations
import logging
import time

from config.settings import settings
from agent.models import FailureType, HealResult, HealStatus, TestFailure
from agent.detector import FailureDetector
from agent.dom_inspector import DOMInspector
from agent.fix_generator import FixGenerator
from agent.test_runner import TestRunner
from agent.git_agent import GitAgent
from agent.jira_agent import JiraAgent

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self) -> None:
        self.detector = FailureDetector()
        self.inspector = DOMInspector()
        self.fix_gen = FixGenerator()
        self.runner = TestRunner()
        self.git = GitAgent()
        self.jira = JiraAgent()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def heal(self, failure: TestFailure, page_url: str = "") -> HealResult:
        """
        Full autonomous heal cycle. Returns a HealResult regardless of outcome.
        """
        start = time.time()
        result = HealResult(failure=failure, failure_type=FailureType.UNKNOWN, fix=None, status=HealStatus.PENDING)

        try:
            # ── Stage 1: Classify ────────────────────────────────────────
            result.status = HealStatus.HEALING
            failure_type = self.detector.classify(failure)
            result.failure_type = failure_type
            logger.info(f"[orchestrator] Classified as: {failure_type.value}")

            # ── Branch: Real bug ─────────────────────────────────────────
            if failure_type == FailureType.REAL_BUG:
                result.jira_ticket_key = self.jira.file_bug(failure, failure.error_message)
                result.status = HealStatus.FAILED
                result.error = "Real regression detected — Jira bug filed, no auto-heal"
                return result

            # ── Branch: Flaky ────────────────────────────────────────────
            if failure_type == FailureType.FLAKY:
                result.jira_ticket_key = self.jira.mark_flaky(failure)
                result.status = HealStatus.QUARANTINED
                return result

            # ── Branch: Unknown ──────────────────────────────────────────
            if failure_type == FailureType.UNKNOWN:
                result.status = HealStatus.NEEDS_REVIEW
                result.error = "Could not classify failure — routed to human review"
                return result

            # ── Stage 2: Inspect DOM ─────────────────────────────────────
            dom_diff = self.inspector.inspect(failure, page_url)

            # ── Stage 3: Generate fix (with retries) ─────────────────────
            test_source = self.runner.read_test_source(failure)

            for attempt in range(1, settings.max_fix_retries + 1):
                fix = self.fix_gen.generate(failure, dom_diff, test_source)
                result.fix = fix
                result.retries = attempt

                # Low confidence → skip auto-commit, send for review
                if fix.needs_human_review:
                    logger.info(f"[orchestrator] Low confidence ({fix.confidence:.0%}) — needs review")
                    result.status = HealStatus.NEEDS_REVIEW
                    return result

                # ── Stage 4: Apply & run ─────────────────────────────────
                passed, output = self.runner.apply_and_run(failure, fix, attempt)

                if passed:
                    logger.info(f"[orchestrator] Test passed on attempt {attempt} ✓")

                    # ── Stage 5: Commit & PR ─────────────────────────────
                    commit_sha, pr_url = self.git.commit_and_pr(failure, fix)
                    result.commit_sha = commit_sha
                    result.pr_url = pr_url

                    # ── Stage 6: Log to Jira ─────────────────────────────
                    elapsed_minutes = (time.time() - start) / 60
                    result.time_saved_minutes = max(30.0, elapsed_minutes * 10)
                    result.jira_ticket_key = self.jira.log_maintenance(result)

                    result.status = HealStatus.HEALED
                    return result

                logger.warning(f"[orchestrator] Attempt {attempt} failed — retrying")

            # Exhausted retries
            result.status = HealStatus.FAILED
            result.error = f"Fix did not pass after {settings.max_fix_retries} attempts"
            return result

        except Exception as exc:
            logger.exception(f"[orchestrator] Unexpected error: {exc}")
            result.status = HealStatus.FAILED
            result.error = str(exc)
            return result
