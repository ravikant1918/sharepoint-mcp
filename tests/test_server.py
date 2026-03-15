"""Tests for server-level mechanisms and routes."""
import asyncio
import json

from mcp_sharepoint.server import health_check


def test_health_check_success(mock_sp_context):
    """Test the /health endpoint when SharePoint connectivity succeeds."""
    response = asyncio.run(health_check(None))

    assert response.status_code == 200

    data = json.loads(response.body.decode("utf-8"))
    assert data["status"] == "ok"
    assert data["sharepoint"] == "connected"
    assert data["tools"] == 14
    assert "sharepoint_error" not in data


def test_health_check_failure(mock_sp_context):
    """Test the /health endpoint when SharePoint connectivity fails."""
    # Force the mock to raise on execute_query
    # Health check calls `client.ctx.execute_query()` for Office365 clients
    # so set the side effect on that attribute.
    mock_sp_context.ctx.execute_query.side_effect = Exception("Simulated connection timeout")

    response = asyncio.run(health_check(None))

    assert response.status_code == 503

    data = json.loads(response.body.decode("utf-8"))
    assert data["status"] == "degraded"
    assert data["sharepoint"] == "disconnected"
    assert "Simulated connection timeout" in data["sharepoint_error"]
