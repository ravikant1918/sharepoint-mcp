"""Pytest fixtures shared across all tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import mcp_sharepoint.config.settings
import mcp_sharepoint.core.client


@pytest.fixture
def mock_settings(monkeypatch):
    """Provide a dummy Settings object so tests never need real credentials."""
    dummy = MagicMock(spec=mcp_sharepoint.config.settings.Settings)
    dummy.shp_doc_library = "Shared Documents/mcp_server"
    dummy.shp_max_depth = 3
    dummy.shp_max_folders_per_level = 10
    dummy.shp_level_delay = 0.0

    with patch("mcp_sharepoint.config.settings.get_settings", return_value=dummy):
        with patch("mcp_sharepoint.config.get_settings", return_value=dummy):
            yield dummy


@pytest.fixture
def mock_sp_context():
    """Provide a mock SharePoint ClientContext so no network calls are made."""
    ctx = MagicMock()
    with patch("mcp_sharepoint.core.client.get_sp_context", return_value=ctx):
        with patch("mcp_sharepoint.core.get_sp_context", return_value=ctx):
            yield ctx
