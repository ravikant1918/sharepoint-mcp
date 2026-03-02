"""Unified folder service supporting both Office365 and Graph APIs."""
from __future__ import annotations

import logging
from typing import Any

from ..core import get_sp_context

logger = logging.getLogger(__name__)


def list_folders(parent_folder: str | None = None) -> list[dict[str, Any]]:
    """List sub-folders in *parent_folder* (or library root if omitted)."""
    client = get_sp_context()
    
    if client.api_type in ("graph", "graphql"):
        from . import folder_service_graph
        return folder_service_graph.list_folders(parent_folder)
    else:
        from . import folder_service_office365
        return folder_service_office365.list_folders(parent_folder)


def create_folder(folder_name: str, parent_folder: str | None = None) -> dict[str, Any]:
    """Create *folder_name* inside *parent_folder* (or library root)."""
    client = get_sp_context()
    
    if client.api_type in ("graph", "graphql"):
        from . import folder_service_graph
        return folder_service_graph.create_folder(folder_name, parent_folder)
    else:
        from . import folder_service_office365
        return folder_service_office365.create_folder(folder_name, parent_folder)


def delete_folder(folder_path: str) -> dict[str, Any]:
    """Delete the empty folder at *folder_path*."""
    client = get_sp_context()
    
    if client.api_type in ("graph", "graphql"):
        from . import folder_service_graph
        return folder_service_graph.delete_folder(folder_path)
    else:
        from . import folder_service_office365
        return folder_service_office365.delete_folder(folder_path)


def get_folder_tree(parent_folder: str | None = None) -> dict[str, Any]:
    """Return a recursive tree of folders and files starting at *parent_folder*."""
    client = get_sp_context()
    
    if client.api_type in ("graph", "graphql"):
        from . import folder_service_graph
        return folder_service_graph.get_folder_tree(parent_folder)
    else:
        from . import folder_service_office365
        return folder_service_office365.get_folder_tree(parent_folder)
