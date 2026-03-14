"""Tests for the retry decorator in utils/retry.py."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from mcp_sharepoint.utils.retry import SharePointThrottleError, sp_retry


def test_sp_retry_succeeds_after_transient_errors(monkeypatch):
    """A decorated function that fails a couple of times then succeeds."""
    # Prevent actual sleeping during retries
    monkeypatch.setattr("time.sleep", lambda _t: None)

    calls = {"n": 0}

    @sp_retry
    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise SharePointThrottleError("throttled")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 3


def test_sp_retry_raises_after_max_attempts(monkeypatch):
    """If the function keeps failing, the decorator should reraise the last error."""
    monkeypatch.setattr("time.sleep", lambda _t: None)

    @sp_retry
    def always_fail() -> None:
        raise ConnectionError("network down")

    with pytest.raises(ConnectionError):
        always_fail()
