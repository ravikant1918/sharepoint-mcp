"""Unit tests for folder_service."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _patch_deps(mock_settings, mock_sp_context):
    """Auto-use settings + context mocks for every test in this file."""
    yield


def _make_folder(name: str, url: str) -> MagicMock:
    f = MagicMock()
    f.name = name
    f.properties = {
        "ServerRelativeUrl": url,
        "TimeCreated": None,
        "TimeLastModified": None,
    }
    return f


class TestListFolders:
    def test_returns_empty_list_when_no_subfolders(self, mock_sp_context):
        folder_mock = MagicMock()
        folder_mock.folders.top = MagicMock(return_value=[])
        mock_sp_context.web.get_folder_by_server_relative_url.return_value = folder_mock

        from mcp_sharepoint.services.folder_service import list_folders
        result = list_folders()

        assert isinstance(result, list)
        assert result == []

    def test_returns_folder_entries(self, mock_sp_context):
        # Patch the office365-specific implementation directly to avoid
        # relying on the heavy ClientContext mocking internals.
        with patch(
            "mcp_sharepoint.services.folder_service_office365.list_folders",
            return_value=[{"name": "reports", "url": "/sites/test/Shared Documents/mcp_server/reports"}],
        ):
            from mcp_sharepoint.services.folder_service import list_folders
            result = list_folders()

        assert result, "Expected at least one folder entry"
        assert any("reports" in (item.get("url") or "") for item in result)


class TestCreateFolder:
    def test_rejects_duplicate_folder(self, mock_sp_context):
        from mcp_sharepoint.services.folder_service import create_folder

        # The office365 implementation calls the office365-specific
        # list_folders function, so patch that module directly.
        with patch(
            "mcp_sharepoint.services.folder_service_office365.list_folders",
            return_value=[{"name": "already_exists"}],
        ): 
            result = create_folder("already_exists")

        assert result["success"] is False
        assert "already exists" in result["message"]
