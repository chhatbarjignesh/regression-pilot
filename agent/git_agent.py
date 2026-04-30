"""
Git Agent
Commits the healed test file to a new branch and opens a Pull Request
on GitHub with full context: what broke, what changed, and why.
"""
from __future__ import annotations
import logging
from datetime import datetime
from pathlib import Path

import git
import httpx

from config.settings import settings
from agent.models import FixProposal, TestFailure

logger = logging.getLogger(__name__)

_GH_API = "https://api.github.com"


class GitAgent:
    def __init__(self) -> None:
        self._headers = {
            "Authorization": f"Bearer {settings.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def commit_and_pr(self, failure: TestFailure, fix: FixProposal) -> tuple[str, str]:
        """
        Commit the fixed test file and open a PR.
        Returns (commit_sha, pr_url).
        """
        repo = git.Repo(failure.repo_path)
        branch_name = self._branch_name(failure)

        # Create and checkout heal branch
        if branch_name in [b.name for b in repo.branches]:
            repo.git.checkout(branch_name)
        else:
            repo.git.checkout("-b", branch_name)

        # Stage and commit
        test_path = Path(failure.repo_path) / failure.test_file
        repo.index.add([str(test_path)])
        commit_message = self._commit_message(failure, fix)
        commit = repo.index.commit(commit_message)
        commit_sha = commit.hexsha[:8]
        logger.info(f"[git] Committed fix: {commit_sha} on {branch_name}")

        # Push
        origin = repo.remote("origin")
        origin.push(refspec=f"{branch_name}:{branch_name}", set_upstream=True)
        logger.info(f"[git] Pushed branch {branch_name}")

        # Open PR
        pr_url = self._open_pr(failure, fix, branch_name)
        return commit_sha, pr_url

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _branch_name(self, failure: TestFailure) -> str:
        safe_name = failure.test_name.lower().replace(" ", "-")[:40]
        ts = datetime.utcnow().strftime("%Y%m%d%H%M")
        return f"regression-pilot/heal-{safe_name}-{ts}"

    def _commit_message(self, failure: TestFailure, fix: FixProposal) -> str:
        return (
            f"fix(test): self-heal broken selector in {failure.test_file}\n\n"
            f"Test: {failure.test_name}\n"
            f"Framework: {failure.framework.value}\n"
            f"Before: {fix.selector_before}\n"
            f"After:  {fix.selector_after}\n"
            f"Confidence: {fix.confidence:.0%}\n\n"
            f"Reason: {fix.explanation}\n\n"
            f"Auto-healed by RegressionPilot 🤖"
        )

    def _open_pr(self, failure: TestFailure, fix: FixProposal, branch: str) -> str:
        body = f"""## 🤖 RegressionPilot — Auto-healed test

**Test:** `{failure.test_name}`
**File:** `{failure.test_file}`
**Framework:** {failure.framework.value}
**Confidence:** {fix.confidence:.0%}

### What changed
{fix.explanation}

### Selector diff
| | Selector |
|---|---|
| Before | `{fix.selector_before}` |
| After | `{fix.selector_after}` |

### CI build
{failure.ci_build_url}

---
*This PR was opened automatically by [RegressionPilot](https://github.com/{settings.github_repo}).
Please review the change and merge if it looks correct.*
"""
        payload = {
            "title": f"[RegressionPilot] Heal broken selector: {failure.test_name}",
            "body": body,
            "head": branch,
            "base": settings.github_default_branch,
            "draft": fix.needs_human_review,
        }
        with httpx.Client(headers=self._headers, timeout=30) as client:
            resp = client.post(
                f"{_GH_API}/repos/{settings.github_repo}/pulls",
                json=payload,
            )
            resp.raise_for_status()
            pr_url = resp.json().get("html_url", "")
            logger.info(f"[git] PR opened: {pr_url}")
            return pr_url
