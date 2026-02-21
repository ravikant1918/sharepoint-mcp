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
    def test_returns_empty_list_when_no_subfolders(self):
        from unittest.mock import MagicMock, patch

        ctx = MagicMock()
        folder_mock = MagicMock()
        folder_mock.folders.top = MagicMock(return_value=[])
        ctx.web.get_folder_by_server_relative_url.return_value = folder_mock

        settings_mock = MagicMock()
        settings_mock.shp_doc_library = "Shared Documents/mcp_server"

        ctx_patch = patch(
            "mcp_sharepoint.services.folder_service.get_sp_context",
            return_value=ctx,
        )
        settings_patch = patch(
            "mcp_sharepoint.services.folder_service.get_settings",
            return_value=settings_mock,
        )
        with ctx_patch, settings_patch:
            from mcp_sharepoint.services.folder_service import list_folders
            result = list_folders()

        assert isinstance(result, list)
        assert result == []

    def test_returns_folder_entries(self):
        from unittest.mock import MagicMock, patch

        sub = _make_folder("reports", "/sites/test/Shared Documents/mcp_server/reports")
        ctx = MagicMock()
        folder_mock = MagicMock()
        folder_mock.folders.top = MagicMock(return_value=[sub])
        ctx.web.get_folder_by_server_relative_url.return_value = folder_mock

        settings_mock = MagicMock()
        settings_mock.shp_doc_library = "Shared Documents/mcp_server"

        ctx_patch = patch(
            "mcp_sharepoint.services.folder_service.get_sp_context",
            return_value=ctx,
        )
        settings_patch = patch(
            "mcp_sharepoint.services.folder_service.get_settings",
            return_value=settings_mock,
        )
        with ctx_patch, settings_patch:
            from mcp_sharepoint.services.folder_service import list_folders
            result = list_folders()

        assert any(item["name"] == "reports" for item in result)


class TestCreateFolder:
    def test_rejects_duplicate_folder(self, mock_sp_context):
        from mcp_sharepoint.services.folder_service import create_folder

        with patch(
            "mcp_sharepoint.services.folder_service.list_folders",
            return_value=[{"name": "already_exists"}],
        ):
            result = create_folder("already_exists")

        assert result["success"] is False
        assert "already exists" in result["message"]
