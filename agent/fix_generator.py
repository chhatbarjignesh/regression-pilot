"""
AI Fix Generator
Uses Claude to analyse the DOM diff and rewrite the broken selector or
test step. Returns a FixProposal with a confidence score so downstream
agents can decide whether to auto-commit or route to human review.
"""
from __future__ import annotations
import json
import logging
import re

from anthropic import Anthropic

from config.settings import settings
from agent.models import DOMDiff, FixProposal, TestFailure

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a senior QA automation engineer specialising in Playwright and Selenium.
Your job is to fix broken test selectors caused by UI changes.

Rules:
- Prefer stable selectors: data-testid > aria roles > text content > CSS class > XPath
- Never change test logic — only fix the broken locator/selector
- Output ONLY valid JSON, no markdown fences, no explanation outside the JSON
- Confidence is a float 0.0–1.0 representing how certain you are the fix is correct

JSON schema:
{
  "original_code": "the broken line(s) as-is",
  "fixed_code": "the corrected line(s)",
  "selector_before": "the old selector string",
  "selector_after": "the new selector string",
  "explanation": "one sentence describing what changed and why",
  "confidence": 0.95
}"""


class FixGenerator:
    def __init__(self) -> None:
        self._client = Anthropic(api_key=settings.anthropic_api_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        failure: TestFailure,
        dom_diff: DOMDiff,
        test_source: str,
    ) -> FixProposal:
        """Generate a fix proposal for the broken test step."""
        broken_lines = self._extract_broken_lines(test_source, dom_diff.broken_line)

        prompt = self._build_prompt(failure, dom_diff, broken_lines)
        raw = self._call_claude(prompt)
        proposal = self._parse_response(raw, broken_lines)

        proposal.needs_human_review = proposal.confidence < settings.confidence_threshold
        logger.info(
            f"[fix-gen] confidence={proposal.confidence:.2f} "
            f"needs_review={proposal.needs_human_review}"
        )
        return proposal

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_broken_lines(self, source: str, line_no: int, context: int = 5) -> str:
        lines = source.splitlines()
        if line_no == 0 or line_no > len(lines):
            return source[:2000]
        start = max(0, line_no - context - 1)
        end = min(len(lines), line_no + context)
        numbered = [f"{i+1:>4}: {line}" for i, line in enumerate(lines[start:end], start)]
        return "\n".join(numbered)

    def _build_prompt(
        self,
        failure: TestFailure,
        dom_diff: DOMDiff,
        broken_lines: str,
    ) -> str:
        candidates = "\n".join(f"  - {s}" for s in dom_diff.suggested_selectors[:5])
        return f"""Framework: {failure.framework.value}
Test file: {failure.test_file}
Error: {failure.error_message}

Broken selector: {dom_diff.broken_selector}

Broken code (with line numbers):
{broken_lines}

Old HTML context (before UI change):
{dom_diff.old_html_snippet[:1500]}

New HTML context (current DOM):
{dom_diff.new_html_snippet[:1500]}

Candidate selectors found in new DOM:
{candidates or '  (none found — infer from new HTML)'}

Fix the broken selector. Return JSON only."""

    def _call_claude(self, prompt: str) -> str:
        response = self._client.messages.create(
            model=settings.ai_model,
            max_tokens=1000,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        block = response.content[0]
        return block.text.strip()  # type: ignore[union-attr]

    def _parse_response(self, raw: str, fallback_original: str) -> FixProposal:
        # Strip accidental markdown fences
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        try:
            data = json.loads(clean)
            return FixProposal(
                original_code=data.get("original_code", fallback_original),
                fixed_code=data["fixed_code"],
                explanation=data.get("explanation", ""),
                confidence=float(data.get("confidence", 0.5)),
                selector_before=data.get("selector_before", ""),
                selector_after=data.get("selector_after", ""),
            )
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning(f"[fix-gen] JSON parse failed: {exc} — low confidence fallback")
            return FixProposal(
                original_code=fallback_original,
                fixed_code=raw,
                explanation="Could not parse structured response — manual review required",
                confidence=0.1,
                needs_human_review=True,
            )
