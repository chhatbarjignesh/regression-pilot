"""
Jira Agent
Two responsibilities:
  1. Log a maintenance entry when RegressionPilot heals a UI test
  2. File a proper bug ticket when the detector classifies a real regression
"""
from __future__ import annotations
import logging
from base64 import b64encode

import httpx

from config.settings import settings
from agent.models import FailureType, FixProposal, HealResult, TestFailure

logger = logging.getLogger(__name__)


class JiraAgent:
    def __init__(self) -> None:
        token = b64encode(
            f"{settings.jira_email}:{settings.jira_api_token}".encode()
        ).decode()
        self._headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._base = settings.jira_base_url.rstrip("/")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_maintenance(self, result: HealResult) -> str:
        """Create a Jira story recording the auto-heal event. Returns issue key."""
        fix = result.fix
        summary = f"[RegressionPilot] Auto-healed: {result.failure.test_name}"
        description = self._maintenance_description(result)
        key = self._create_issue(
            summary=summary,
            description=description,
            issue_type="Story",
            labels=["regression-pilot", "test-maintenance", "auto-healed"],
            priority="Low",
        )
        logger.info(f"[jira] Maintenance logged: {key}")
        return key

    def file_bug(self, failure: TestFailure, output: str) -> str:
        """Create a Jira bug ticket for a real regression. Returns issue key."""
        summary = f"[RegressionPilot] Real regression detected: {failure.test_name}"
        description = self._bug_description(failure, output)
        key = self._create_issue(
            summary=summary,
            description=description,
            issue_type="Bug",
            labels=["regression-pilot", "real-bug"],
            priority="High",
        )
        logger.info(f"[jira] Bug filed: {key}")
        return key

    def mark_flaky(self, failure: TestFailure) -> str:
        """Create a Jira task to track a quarantined flaky test. Returns issue key."""
        summary = f"[RegressionPilot] Flaky test quarantined: {failure.test_name}"
        description = self._flaky_description(failure)
        key = self._create_issue(
            summary=summary,
            description=description,
            issue_type="Task",
            labels=["regression-pilot", "flaky-test"],
            priority="Medium",
        )
        logger.info(f"[jira] Flaky task created: {key}")
        return key

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_issue(
        self,
        summary: str,
        description: str,
        issue_type: str,
        labels: list[str],
        priority: str,
    ) -> str:
        payload = {
            "fields": {
                "project": {"key": settings.jira_project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}],
                        }
                    ],
                },
                "issuetype": {"name": issue_type},
                "labels": labels,
                "priority": {"name": priority},
            }
        }
        with httpx.Client(headers=self._headers, timeout=30) as client:
            resp = client.post(f"{self._base}/rest/api/3/issue", json=payload)
            resp.raise_for_status()
            return resp.json()["key"]

    def _maintenance_description(self, result: HealResult) -> str:
        fix = result.fix
        if not fix:
            return "RegressionPilot detected a UI change but could not generate a fix."
        return (
            f"RegressionPilot automatically healed a broken UI test.\n\n"
            f"Test: {result.failure.test_name}\n"
            f"File: {result.failure.test_file}\n"
            f"Framework: {result.failure.framework.value}\n"
            f"Selector before: {fix.selector_before}\n"
            f"Selector after:  {fix.selector_after}\n"
            f"Confidence: {fix.confidence:.0%}\n"
            f"Reason: {fix.explanation}\n\n"
            f"Pull request: {result.pr_url}\n"
            f"Commit: {result.commit_sha}\n"
            f"Estimated time saved: {result.time_saved_minutes:.0f} minutes"
        )

    def _bug_description(self, failure: TestFailure, output: str) -> str:
        return (
            f"RegressionPilot detected a real functional regression.\n\n"
            f"Test: {failure.test_name}\n"
            f"File: {failure.test_file}\n"
            f"Framework: {failure.framework.value}\n"
            f"Branch: {failure.branch}\n"
            f"Commit: {failure.commit_sha}\n"
            f"CI build: {failure.ci_build_url}\n\n"
            f"Error:\n{failure.error_message}\n\n"
            f"Test output (truncated):\n{output[:1000]}"
        )

    def _flaky_description(self, failure: TestFailure) -> str:
        return (
            f"RegressionPilot quarantined a flaky test.\n\n"
            f"Test: {failure.test_name}\n"
            f"File: {failure.test_file}\n"
            f"Framework: {failure.framework.value}\n"
            f"Error: {failure.error_message}\n\n"
            f"Action required: investigate environment / timing dependency."
        )
