"""
Tests for the failure detector — uses mocked Claude responses.
"""
import pytest
from unittest.mock import MagicMock, patch

from agent.detector import FailureDetector
from agent.models import FailureType, Framework, TestFailure


def _make_failure(error: str, stack: str = "") -> TestFailure:
    return TestFailure(
        test_name="test_login",
        test_file="tests/test_login.py",
        framework=Framework.PLAYWRIGHT,
        error_message=error,
        stack_trace=stack,
        repo_path="/tmp/repo",
        branch="main",
        commit_sha="abc123",
    )


class TestFailureDetector:
    def setup_method(self):
        self.detector = FailureDetector()

    def test_classifies_selector_error_as_ui_change(self):
        failure = _make_failure("element not found: #submit-btn")
        result = self.detector._fast_classify(failure)
        assert result == FailureType.UI_CHANGE

    def test_classifies_stale_element_as_ui_change(self):
        failure = _make_failure("stale element reference: element is not attached to the page")
        result = self.detector._fast_classify(failure)
        assert result == FailureType.UI_CHANGE

    def test_classifies_network_error_as_flaky(self):
        failure = _make_failure("net::ERR_CONNECTION_REFUSED")
        result = self.detector._fast_classify(failure)
        assert result == FailureType.FLAKY

    def test_classifies_timeout_as_flaky(self):
        failure = _make_failure("timeout of 30000ms exceeded")
        result = self.detector._fast_classify(failure)
        assert result == FailureType.FLAKY

    def test_returns_unknown_for_ambiguous_errors(self):
        failure = _make_failure("AssertionError: expected 'Hello' to equal 'World'")
        result = self.detector._fast_classify(failure)
        assert result == FailureType.UNKNOWN

    @patch("agent.detector.Anthropic")
    def test_ai_classify_called_for_unknown(self, mock_anthropic):
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value.content = [
            MagicMock(text="real_bug")
        ]
        detector = FailureDetector()
        failure = _make_failure("AssertionError: total is 0 but expected 100")
        result = detector.classify(failure)
        assert result == FailureType.REAL_BUG
        mock_client.messages.create.assert_called_once()

    @patch("agent.detector.Anthropic")
    def test_ai_classify_handles_invalid_response(self, mock_anthropic):
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value.content = [
            MagicMock(text="gibberish")
        ]
        detector = FailureDetector()
        failure = _make_failure("some ambiguous error")
        result = detector.classify(failure)
        assert result == FailureType.UNKNOWN
