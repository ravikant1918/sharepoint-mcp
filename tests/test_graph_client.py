"""Unit tests for the GraphClient wrapper in core/client.py."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import requests

import sys
import types

# Provide lightweight stubs for heavy external dependencies so tests
# can import the module without installing them.
if "msal" not in sys.modules:
    sys.modules["msal"] = types.ModuleType("msal")

for mod in [
    "office365",
    "office365.runtime",
    "office365.runtime.auth",
    "office365.runtime.auth.client_credential",
    "office365.sharepoint",
    "office365.sharepoint.client_context",
]:
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)

# Provide minimal classes used by imports
sys.modules["office365.runtime.auth.client_credential"].ClientCredential = lambda *a, **k: None
class _DummyCtx:
    def with_credentials(self, *_a, **_k):
        return self
    base_url = "https://example.com"
sys.modules["office365.sharepoint.client_context"].ClientContext = lambda url: _DummyCtx()

from mcp_sharepoint.core.client import GraphClient
from mcp_sharepoint.exceptions import SharePointConnectionError


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, content=b"", text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.content = content
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"{self.status_code} error")

    def json(self):
        return self._json


def make_client():
    return GraphClient("token", "https://example.com/sites/test")


def test_get_post_put_delete_and_download_upload(monkeypatch):
    client = make_client()

    # _get_site_id should call requests.get and cache the result
    def fake_get_site(url, headers=None, params=None, timeout=None):
        return DummyResponse(json_data={"id": "SITE123"})

    monkeypatch.setattr("requests.get", fake_get_site)
    site_id = client._get_site_id()
    assert site_id == "SITE123"

    # Test get() returns parsed json
    def fake_get(url, headers=None, params=None, timeout=None):
        return DummyResponse(json_data={"value": 1})

    monkeypatch.setattr("requests.get", fake_get)
    assert client.get("some/endpoint") == {"value": 1}

    # Test post() returns parsed json
    def fake_post(url, headers=None, json=None, timeout=None):
        return DummyResponse(json_data={"ok": True})

    monkeypatch.setattr("requests.post", fake_post)
    assert client.post("some/endpoint", {"a": 1}) == {"ok": True}

    # Test put() with empty content returns {}
    def fake_put(url, headers=None, json=None, timeout=None):
        return DummyResponse(status_code=200, json_data=None, content=b"")

    monkeypatch.setattr("requests.put", fake_put)
    assert client.put("some/endpoint", {"a": 1}) == {}

    # Test delete() returns True on success
    def fake_delete(url, headers=None, timeout=None):
        return DummyResponse(status_code=204)

    monkeypatch.setattr("requests.delete", fake_delete)
    assert client.delete("some/endpoint") is True

    # Test download() returns bytes
    def fake_download(url, headers=None, timeout=None):
        return DummyResponse(status_code=200, content=b"binarydata")

    monkeypatch.setattr("requests.get", fake_download)
    assert client.download("some/content") == b"binarydata"

    # Test upload() returns json
    def fake_upload(url, headers=None, data=None, timeout=None):
        return DummyResponse(status_code=200, json_data={"id": "fileid"})

    monkeypatch.setattr("requests.put", fake_upload)
    assert client.upload("some/endpoint", b"abc") == {"id": "fileid"}


def test_graph_client_error_wrapping(monkeypatch):
    client = make_client()

    def raising_get(url, headers=None, params=None, timeout=None):
        raise requests.exceptions.RequestException("fail")

    monkeypatch.setattr("requests.get", raising_get)

    with pytest.raises(SharePointConnectionError):
        client.get("endpoint")
