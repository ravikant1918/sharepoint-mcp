"""Unified metadata service supporting both Office365 and Graph APIs."""
from __future__ import annotations

import logging
from typing import Any

from ..core import get_sp_context

logger = logging.getLogger(__name__)


def get_file_metadata(folder_name: str, file_name: str) -> dict[str, Any]:
    """Return all list-item properties for *file_name*."""
    client = get_sp_context()
    
    if client.api_type in ("graph", "graphql"):
        from . import metadata_service_graph
        return metadata_service_graph.get_file_metadata(folder_name, file_name)
    else:
        from . import metadata_service_office365
        return metadata_service_office365.get_file_metadata(folder_name, file_name)


def update_file_metadata(
    folder_name: str,
    file_name: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Update list-item *metadata* fields for *file_name*."""
    client = get_sp_context()
    
    if client.api_type in ("graph", "graphql"):
        from . import metadata_service_graph
        return metadata_service_graph.update_file_metadata(folder_name, file_name, metadata)
    else:
        from . import metadata_service_office365
        return metadata_service_office365.update_file_metadata(folder_name, file_name, metadata)
