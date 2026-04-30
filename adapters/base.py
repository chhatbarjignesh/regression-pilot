"""
Base adapter interface. All browser adapters must implement this.
"""
from __future__ import annotations
from abc import ABC, abstractmethod


class BrowserAdapter(ABC):
    @abstractmethod
    def start(self) -> None:
        """Launch the browser."""

    @abstractmethod
    def stop(self) -> None:
        """Close the browser."""

    @abstractmethod
    def navigate(self, url: str) -> None:
        """Navigate to a URL."""

    @abstractmethod
    def get_page_html(self) -> str:
        """Return the full page HTML."""

    @abstractmethod
    def find_similar_selectors(self, broken_selector: str) -> list[str]:
        """
        Given a broken selector, return candidate replacement selectors
        found in the current DOM (e.g. same tag, same aria role, nearby text).
        """
