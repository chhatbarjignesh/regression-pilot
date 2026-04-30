"""
Test Runner Agent
Applies a FixProposal to the test file on disk, executes the specific
test using the correct framework, and returns pass/fail with output.
Supports retry up to settings.max_fix_retries.
"""
from __future__ import annotations
import logging
import re
import subprocess
from pathlib import Path

from config.settings import settings
from agent.models import FixProposal, Framework, TestFailure

logger = logging.getLogger(__name__)


class TestRunner:
    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply_and_run(
        self,
        failure: TestFailure,
        fix: FixProposal,
        attempt: int = 1,
    ) -> tuple[bool, str]:
        """
        Apply the fix to the test file and run it.
        Returns (passed: bool, output: str).
        """
        test_path = Path(failure.repo_path) / failure.test_file
        original_source = test_path.read_text(encoding="utf-8")

        patched_source = self._apply_fix(original_source, fix)
        if patched_source == original_source:
            logger.warning("[runner] Patch produced no change — fix may be malformed")
            return False, "Patch produced no changes in test file"

        # Write patched file
        test_path.write_text(patched_source, encoding="utf-8")
        logger.info(f"[runner] Attempt {attempt}/{settings.max_fix_retries} — running {failure.test_name}")

        try:
            passed, output = self._execute_test(failure, test_path)
        except Exception as exc:
            # Restore original on unexpected error
            test_path.write_text(original_source, encoding="utf-8")
            return False, str(exc)

        if not passed:
            # Restore original so next retry starts clean
            test_path.write_text(original_source, encoding="utf-8")

        return passed, output

    def read_test_source(self, failure: TestFailure) -> str:
        test_path = Path(failure.repo_path) / failure.test_file
        return test_path.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_fix(self, source: str, fix: FixProposal) -> str:
        """Simple string replacement of original_code → fixed_code."""
        original = fix.original_code.strip()
        if original in source:
            return source.replace(original, fix.fixed_code.strip(), 1)

        # Fallback: selector-level replacement
        if fix.selector_before and fix.selector_after:
            return source.replace(fix.selector_before, fix.selector_after, 1)

        logger.warning("[runner] Could not locate original code in source for patch")
        return source

    def _execute_test(
        self,
        failure: TestFailure,
        test_path: Path,
    ) -> tuple[bool, str]:
        cmd = self._build_command(failure, test_path)
        logger.debug(f"[runner] Command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=settings.test_timeout_seconds,
            cwd=failure.repo_path,
        )
        output = result.stdout + result.stderr
        passed = result.returncode == 0
        logger.info(f"[runner] Exit code: {result.returncode}")
        return passed, output

    def _build_command(self, failure: TestFailure, test_path: Path) -> list[str]:
        if failure.framework == Framework.PLAYWRIGHT:
            return [
                "npx", "playwright", "test",
                str(test_path),
                "--reporter=line",
                f"--grep={re.escape(failure.test_name)}",
            ]
        elif failure.framework == Framework.SELENIUM:
            return [
                "python", "-m", "pytest",
                str(test_path),
                f"-k={failure.test_name}",
                "--tb=short",
                "-q",
            ]
        else:
            raise ValueError(f"Unsupported framework: {failure.framework}")
