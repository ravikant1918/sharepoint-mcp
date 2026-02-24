"""File metadata operations against the SharePoint REST API."""
from __future__ import annotations

import logging
import posixpath
from typing import Any

from ..config import get_settings
from ..core import get_sp_context
from ..utils.retry import sp_retry

logger = logging.getLogger(__name__)


def _sp_path(sub_path: str = "") -> str:
    library = get_settings().shp_doc_library
    clean_path = posixpath.normpath(f"/{sub_path}").lstrip("/") if sub_path else ""
    if clean_path.startswith(".."):
        raise ValueError(f"Invalid path traversal attempt: {sub_path}")
    return f"{library}/{clean_path}".rstrip("/")


@sp_retry
def get_file_metadata(folder_name: str, file_name: str) -> dict[str, Any]:
    """Return all list-item properties for *file_name*."""
    ctx = get_sp_context()
    file_path = _sp_path(f"{folder_name}/{file_name}")
    logger.info("Getting metadata for '%s'", file_path)

    file_obj = ctx.web.get_file_by_server_relative_url(file_path)
    list_item = file_obj.listItemAllFields
    ctx.load(list_item)
    ctx.execute_query()

    metadata = {
        k: str(v)
        for k, v in list_item.properties.items()
        if v is not None
    }
    return {
        "success": True,
        "message": f"Metadata retrieved for '{file_name}'",
        "metadata": metadata,
        "file": {"name": file_name, "path": file_path},
    }


@sp_retry
def update_file_metadata(
    folder_name: str,
    file_name: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Update list-item *metadata* fields for *file_name*."""
    ctx = get_sp_context()
    file_path = _sp_path(f"{folder_name}/{file_name}")
    logger.info("Updating metadata for '%s'", file_path)

    file_obj = ctx.web.get_file_by_server_relative_url(file_path)
    list_item = file_obj.listItemAllFields

    form_values: dict[str, str] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, bool):
            form_values[key] = "1" if value else "0"
        elif isinstance(value, list):
            form_values[key] = ";".join(str(v) for v in value)
        else:
            form_values[key] = str(value)

    if not form_values:
        return {"success": True, "message": "No fields to update"}

    list_item.validate_update_list_item(form_values, new_document_update=True)
    ctx.execute_query()
    return {
        "success": True,
        "message": f"Updated {len(form_values)} field(s) for '{file_name}'",
    }
