"""Retry decorator for SharePoint API calls.

Uses tenacity to handle Microsoft Graph / SharePoint throttling (HTTP 429)
and transient failures (HTTP 503) with exponential backoff.
"""
from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable, TypeVar

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

_F = TypeVar("_F", bound=Callable[..., Any])


class SharePointThrottleError(Exception):
    """Raised when SharePoint returns a 429 / 503 response."""


def sp_retry(func: _F) -> _F:
    """Decorator: retry a SharePoint call up to 3 times with exponential backoff.

    Handles:
    - ``SharePointThrottleError`` (429 Too Many Requests)
    - Generic ``Exception`` from transient network issues

    Waits: 2s → 8s → 30s (max) between attempts.
    """
    @retry(
        retry=retry_if_exception_type((SharePointThrottleError, ConnectionError, TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
