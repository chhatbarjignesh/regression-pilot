"""
Selenium adapter — wraps Selenium WebDriver for DOM inspection.
"""
from __future__ import annotations
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from adapters.base import BrowserAdapter


class SeleniumAdapter(BrowserAdapter):
    def __init__(self, headless: bool = True) -> None:
        self._headless = headless
        self._driver: webdriver.Chrome | None = None

    def start(self) -> None:
        options = Options()
        if self._headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        service = Service(ChromeDriverManager().install())
        self._driver = webdriver.Chrome(service=service, options=options)

    def stop(self) -> None:
        if self._driver:
            self._driver.quit()

    def navigate(self, url: str) -> None:
        assert self._driver, "Adapter not started"
        self._driver.get(url)

    def get_page_html(self) -> str:
        assert self._driver, "Adapter not started"
        return self._driver.page_source

    def find_similar_selectors(self, broken_selector: str) -> list[str]:
        assert self._driver, "Adapter not started"
        candidates: list[str] = []

        try:
            els = self._driver.find_elements(By.CSS_SELECTOR, "[data-testid]")
            candidates += [
                f"[data-testid='{e.get_attribute('data-testid')}']"
                for e in els[:5]
            ]
        except Exception:
            pass

        try:
            els = self._driver.find_elements(By.CSS_SELECTOR, "[aria-label]")
            candidates += [
                f"[aria-label='{e.get_attribute('aria-label')}']"
                for e in els[:5]
            ]
        except Exception:
            pass

        # ID-based selectors (very stable)
        try:
            els = self._driver.find_elements(By.CSS_SELECTOR, "[id]")
            candidates += [f"#{e.get_attribute('id')}" for e in els[:5] if e.get_attribute("id")]
        except Exception:
            pass

        return list(dict.fromkeys(candidates))
