"""Tests for server-level mechanisms and routes."""
import json

import pytest

from mcp_sharepoint.server import health_check


@pytest.mark.asyncio
async def test_health_check_success(mock_sp_context):
    """Test the /health endpoint when SharePoint connectivity succeeds."""
    # The mock_sp_context fixture automatically mocks get_sp_context.
    # By default, executing query on it will do nothing and succeed.
    
    response = await health_check(None)
    
    assert response.status_code == 200
    
    data = json.loads(response.body.decode("utf-8"))
    assert data["status"] == "ok"
    assert data["sharepoint"] == "connected"
    assert data["tools"] == 14
    assert "sharepoint_error" not in data

@pytest.mark.asyncio
async def test_health_check_failure(mock_sp_context):
    """Test the /health endpoint when SharePoint connectivity fails."""
    # Force the mock to raise on execute_query
    mock_sp_context.execute_query.side_effect = Exception("Simulated connection timeout")
    
    response = await health_check(None)
    
    assert response.status_code == 503
    
    data = json.loads(response.body.decode("utf-8"))
    assert data["status"] == "degraded"
    assert data["sharepoint"] == "disconnected"
    assert "Simulated connection timeout" in data["sharepoint_error"]
