"""
Playwright adapter — wraps playwright sync API for DOM inspection.
"""
from __future__ import annotations
import re
from playwright.sync_api import sync_playwright, Browser, Page

from adapters.base import BrowserAdapter


class PlaywrightAdapter(BrowserAdapter):
    def __init__(self, headless: bool = True) -> None:
        self._headless = headless
        self._pw = None
        self._browser: Browser | None = None
        self._page: Page | None = None

    def start(self) -> None:
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self._headless)
        self._page = self._browser.new_page()

    def stop(self) -> None:
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    def navigate(self, url: str) -> None:
        assert self._page, "Adapter not started"
        self._page.goto(url, wait_until="networkidle", timeout=30_000)

    def get_page_html(self) -> str:
        assert self._page, "Adapter not started"
        return self._page.content()

    def find_similar_selectors(self, broken_selector: str) -> list[str]:
        """
        Try to find stable replacements:
        1. data-testid attributes
        2. aria-label attributes
        3. role attributes
        4. Elements with similar text content
        """
        assert self._page, "Adapter not started"
        candidates: list[str] = []

        try:
            # data-testid selectors (most stable)
            testids = self._page.eval_on_selector_all(
                "[data-testid]",
                "els => els.map(e => e.getAttribute('data-testid'))",
            )
            candidates += [f"[data-testid='{tid}']" for tid in testids[:5]]
        except Exception:
            pass

        try:
            # aria-label selectors
            aria = self._page.eval_on_selector_all(
                "[aria-label]",
                "els => els.map(e => e.getAttribute('aria-label'))",
            )
            candidates += [f"[aria-label='{a}']" for a in aria[:5]]
        except Exception:
            pass

        # Text-based: extract text from broken selector if it looks like a CSS class
        text_hint = re.sub(r'[.#\[\]"\'=]', ' ', broken_selector).strip()
        if text_hint:
            try:
                matches = self._page.eval_on_selector_all(
                    f"*:text-matches('{text_hint[:30]}', 'i')",
                    "els => els.map(e => e.tagName.toLowerCase() + (e.id ? '#' + e.id : ''))",
                )
                candidates += matches[:3]
            except Exception:
                pass

        return list(dict.fromkeys(candidates))  # deduplicate, preserve order
