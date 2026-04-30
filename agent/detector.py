"""
Failure Detector Agent
Listens for CI webhook payloads and classifies each failure as:
  - ui_change  → selector broke due to a DOM update (RegressionPilot heals it)
  - real_bug   → actual functional regression (file Jira bug)
  - flaky      → non-deterministic / environment issue (quarantine)
  - unknown    → escalate to human review
"""
from __future__ import annotations
import logging
import re
from anthropic import Anthropic

from config.settings import settings
from agent.models import FailureType, Framework, TestFailure

logger = logging.getLogger(__name__)

# Heuristic patterns that strongly suggest a selector / locator issue
_SELECTOR_PATTERNS = [
    r"element not found",
    r"no such element",
    r"locator\..*not visible",
    r"strict mode violation",
    r"selector.*did not match",
    r"waiting for selector",
    r"element is not attached",
    r"stale element reference",
    r"unable to locate element",
    r"NoSuchElementException",
    r"ElementNotInteractableException",
    r"TimeoutError.*locator",
]

_FLAKY_PATTERNS = [
    r"net::ERR_CONNECTION",
    r"timeout of \d+ms exceeded",
    r"ECONNRESET",
    r"socket hang up",
    r"Navigation timeout",
]


class FailureDetector:
    def __init__(self) -> None:
        self._client = Anthropic(api_key=settings.anthropic_api_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(self, failure: TestFailure) -> FailureType:
        """
        Two-stage classification:
        1. Fast heuristic check (no API call)
        2. Claude-backed deep classification for ambiguous cases
        """
        fast = self._fast_classify(failure)
        if fast != FailureType.UNKNOWN:
            logger.info(f"[detector] Fast classify → {fast.value} for {failure.test_name}")
            return fast

        logger.info(f"[detector] Ambiguous, using Claude for {failure.test_name}")
        return self._ai_classify(failure)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fast_classify(self, failure: TestFailure) -> FailureType:
        combined = f"{failure.error_message}\n{failure.stack_trace}".lower()

        for pattern in _SELECTOR_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                return FailureType.UI_CHANGE

        for pattern in _FLAKY_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                return FailureType.FLAKY

        return FailureType.UNKNOWN

    def _ai_classify(self, failure: TestFailure) -> FailureType:
        prompt = f"""You are a QA engineer analysing a test failure. Classify it into exactly one category.

Categories:
- ui_change: The test broke because a UI element (selector, locator, text) changed in the DOM
- real_bug: The test correctly detected a functional regression in the application
- flaky: The test is non-deterministic (network, timing, environment issues)
- unknown: Cannot determine with confidence

Test name: {failure.test_name}
Framework: {failure.framework.value}
Error message:
{failure.error_message}

Stack trace (truncated):
{failure.stack_trace[:1500]}

Respond with ONLY one of: ui_change, real_bug, flaky, unknown
"""
        try:
            response = self._client.messages.create(
                model=settings.ai_model,
                max_tokens=20,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip().lower()
            return FailureType(raw) if raw in FailureType._value2member_map_ else FailureType.UNKNOWN
        except Exception as exc:
            logger.warning(f"[detector] AI classify failed: {exc} — defaulting to UNKNOWN")
            return FailureType.UNKNOWN
