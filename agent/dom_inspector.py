"""
DOM Inspector Agent
Opens the target page using the appropriate adapter, locates the broken
selector, captures the surrounding HTML before and after the UI change,
and returns a DOMDiff that the fix generator can act on.
"""
from __future__ import annotations
import logging
import re

from agent.models import DOMDiff, Framework, TestFailure
from adapters.base import BrowserAdapter
from adapters.playwright_adapter import PlaywrightAdapter
from adapters.selenium_adapter import SeleniumAdapter

logger = logging.getLogger(__name__)


class DOMInspector:
    def __init__(self) -> None:
        self._adapters: dict[Framework, type[BrowserAdapter]] = {
            Framework.PLAYWRIGHT: PlaywrightAdapter,
            Framework.SELENIUM: SeleniumAdapter,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def inspect(self, failure: TestFailure, page_url: str) -> DOMDiff:
        """
        1. Parse the broken selector from the error / stack trace
        2. Launch browser, navigate to page_url
        3. Capture full DOM around the broken selector's parent
        4. Generate candidate replacement selectors
        """
        broken_selector, broken_line = self._extract_selector(failure)
        logger.info(f"[inspector] Broken selector: {broken_selector!r} at line {broken_line}")

        adapter_cls = self._adapters.get(failure.framework)
        if adapter_cls is None:
            raise ValueError(f"Unsupported framework: {failure.framework}")

        adapter = adapter_cls()
        try:
            adapter.start()
            adapter.navigate(page_url)
            new_html = adapter.get_page_html()
            old_html_snippet = self._extract_context(new_html, broken_selector)
            candidates = adapter.find_similar_selectors(broken_selector)
        finally:
            adapter.stop()

        return DOMDiff(
            broken_selector=broken_selector,
            broken_line=broken_line,
            old_html_snippet=old_html_snippet,
            new_html_snippet=new_html[:4000],   # cap for LLM context
            suggested_selectors=candidates,
            page_url=page_url,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_selector(self, failure: TestFailure) -> tuple[str, int]:
        """Pull selector string and line number from error message / stack."""
        # Playwright: page.locator("...") / getByRole / getByText etc.
        playwright_patterns = [
            r'locator\(["\'](.+?)["\']\)',
            r'getByRole\(["\'](.+?)["\']\)',
            r'getByText\(["\'](.+?)["\']\)',
            r'getByTestId\(["\'](.+?)["\']\)',
            r'getByLabel\(["\'](.+?)["\']\)',
            r'fill\(["\'](.+?)["\']\)',
            r'click\(["\'](.+?)["\']\)',
        ]
        # Selenium: find_element(By.*, "...")
        selenium_patterns = [
            r'find_element\([^,]+,\s*["\'](.+?)["\']\)',
            r'find_elements\([^,]+,\s*["\'](.+?)["\']\)',
            r'By\.(?:CSS_SELECTOR|XPATH|ID|NAME|CLASS_NAME),\s*["\'](.+?)["\']\)',
        ]

        combined = f"{failure.error_message}\n{failure.stack_trace}"

        for pattern in playwright_patterns + selenium_patterns:
            m = re.search(pattern, combined)
            if m:
                selector = m.group(1)
                line = self._find_line_number(failure.stack_trace, selector)
                return selector, line

        # Fallback — return the full error message as selector hint
        return failure.error_message[:200], 0

    def _find_line_number(self, stack_trace: str, selector: str) -> int:
        for i, line in enumerate(stack_trace.splitlines(), 1):
            if selector in line:
                # Try to extract ":NN" line reference from stack
                m = re.search(r':(\d+)(?::\d+)?', line)
                if m:
                    return int(m.group(1))
                return i
        return 0

    def _extract_context(self, html: str, selector: str) -> str:
        """Return a 2000-char window of HTML around where selector appears."""
        idx = html.find(selector)
        if idx == -1:
            return f"<!-- selector '{selector}' not found in current DOM -->"
        start = max(0, idx - 500)
        end = min(len(html), idx + 1500)
        return html[start:end]
