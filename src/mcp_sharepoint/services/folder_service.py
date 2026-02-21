"""Folder operations against the SharePoint REST API."""
from __future__ import annotations

import logging
import posixpath
import time
from typing import Any

from ..config import get_settings
from ..core import get_sp_context
from ..utils.retry import sp_retry

logger = logging.getLogger(__name__)


def _sp_path(sub_path: str | None = None) -> str:
    library = get_settings().shp_doc_library
    clean_path = posixpath.normpath(f"/{sub_path}").lstrip("/") if sub_path else ""
    if clean_path.startswith(".."):
        raise ValueError(f"Invalid path traversal attempt: {sub_path}")
    return f"{library}/{clean_path}".rstrip("/")


@sp_retry
def _load_items(path: str, item_type: str) -> list[dict[str, Any]]:
    """Generic loader for folders or files from a SharePoint path."""
    ctx = get_sp_context()
    folder = ctx.web.get_folder_by_server_relative_url(path)
    items = getattr(folder, item_type).top(500)
    props = ["ServerRelativeUrl", "Name", "TimeCreated", "TimeLastModified"] + (
        ["Length"] if item_type == "files" else []
    )
    ctx.load(items, props)
    ctx.execute_query()

    result = []
    for item in items:
        entry: dict[str, Any] = {
            "name": item.name,
            "url": item.properties.get("ServerRelativeUrl"),
            "created": (
                item.properties["TimeCreated"].isoformat()
                if item.properties.get("TimeCreated")
                else None
            ),
            "modified": (
                item.properties["TimeLastModified"].isoformat()
                if item.properties.get("TimeLastModified")
                else None
            ),
        }
        if item_type == "files":
            entry["size"] = item.properties.get("Length")
        result.append(entry)
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_folders(parent_folder: str | None = None) -> list[dict[str, Any]]:
    """List sub-folders in *parent_folder* (or library root if omitted)."""
    logger.info("Listing folders in %s", parent_folder or "root")
    return _load_items(_sp_path(parent_folder), "folders")


@sp_retry
def create_folder(folder_name: str, parent_folder: str | None = None) -> dict[str, Any]:
    """Create *folder_name* inside *parent_folder* (or library root)."""
    ctx = get_sp_context()
    parent_path = _sp_path(parent_folder)
    logger.info("Creating folder '%s' in '%s'", folder_name, parent_path)

    # Guard: folder already exists?
    if any(f["name"] == folder_name for f in list_folders(parent_folder)):
        return {"success": False, "message": f"Folder '{folder_name}' already exists"}

    parent = ctx.web.get_folder_by_server_relative_url(parent_path)
    new_folder = parent.folders.add(folder_name)
    ctx.execute_query()
    return {
        "success": True,
        "message": f"Folder '{folder_name}' created successfully",
        "folder": {"name": new_folder.name, "url": new_folder.serverRelativeUrl},
    }


@sp_retry
def delete_folder(folder_path: str) -> dict[str, Any]:
    """Delete the empty folder at *folder_path*."""
    ctx = get_sp_context()
    full_path = _sp_path(folder_path)
    logger.info("Deleting folder: %s", full_path)

    folder = ctx.web.get_folder_by_server_relative_url(full_path)
    ctx.load(folder)
    ctx.load(folder.files)
    ctx.load(folder.folders)
    ctx.execute_query()

    if not getattr(folder, "exists", True):
        return {"success": False, "message": f"Folder '{folder_path}' does not exist"}
    if len(folder.files) > 0:
        return {"success": False, "message": f"Folder contains {len(folder.files)} file(s)"}
    if len(folder.folders) > 0:
        return {"success": False, "message": f"Folder contains {len(folder.folders)} sub-folder(s)"}

    folder.delete_object()
    ctx.execute_query()
    return {"success": True, "message": f"Folder '{folder_path}' deleted successfully"}


@sp_retry
def get_folder_tree(parent_folder: str | None = None) -> dict[str, Any]:
    """Return a recursive tree of folders and files starting at *parent_folder*."""
    cfg = get_settings()
    ctx = get_sp_context()
    root_path = _sp_path(parent_folder)
    logger.info("Building folder tree for '%s'", parent_folder or "root")

    try:
        root = ctx.web.get_folder_by_server_relative_url(root_path)
        ctx.load(root, ["Name", "ServerRelativeUrl", "TimeCreated", "TimeLastModified"])
        ctx.execute_query()
    except Exception as exc:
        logger.error("Cannot access root folder '%s': %s", root_path, exc)
        return {
            "name": root_path.split("/")[-1],
            "path": root_path,
            "type": "folder",
            "error": "Could not access folder",
            "children": [],
        }

    tree_nodes: dict[str, list] = {}
    pending = [parent_folder or ""]

    for level in range(cfg.shp_max_depth):
        if not pending:
            break
        logger.info("Tree level %d: %d folder(s)", level + 1, len(pending))
        current, pending = pending.copy(), []

        while current:
            batch, current = (
                current[: cfg.shp_max_folders_per_level],
                current[cfg.shp_max_folders_per_level :],
            )
            for fp in batch:
                try:
                    sub_folders = [f["name"] for f in list_folders(fp)]
                    files = _load_items(_sp_path(fp), "files")
                    tree_nodes[fp] = [
                        {"name": n, "type": "folder", "children": []} for n in sub_folders
                    ] + [
                        {
                            "name": f["name"],
                            "path": f["url"],
                            "type": "file",
                            **{k: v for k, v in f.items() if k not in ("name", "url")},
                        }
                        for f in files
                    ]
                    pending.extend(
                        f"{fp}/{n}".strip("/") for n in sub_folders
                    )
                except Exception:
                    logger.warning("Failed to process folder: %s", fp)
            if current:
                time.sleep(0.1)

        if level < cfg.shp_max_depth - 1:
            time.sleep(cfg.shp_level_delay)

    def _build(path: str) -> list[dict]:
        children = tree_nodes.get(path, [])
        for child in children:
            if child["type"] == "folder":
                child["children"] = _build(f"{path}/{child['name']}".strip("/"))
        return children

    return {
        "name": root.name,
        "path": root.properties.get("ServerRelativeUrl"),
        "type": "folder",
        "created": (
            root.properties["TimeCreated"].isoformat()
            if root.properties.get("TimeCreated")
            else None
        ),
        "modified": (
            root.properties["TimeLastModified"].isoformat()
            if root.properties.get("TimeLastModified")
            else None
        ),
        "children": _build(parent_folder or ""),
    }
