# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.1.0-rc] — Unreleased

### Added

- `Search_SharePoint` — full-text search using SharePoint KQL
- **Config:** `SHP_LIBRARY_NAME` environment variable — specifies the SharePoint document library name (defaults to `"Shared Documents"`). Only used by Office365 REST API; Graph API auto-detects the default drive via `drive/root`.

### Changed

- **Config:** `SHP_DOC_LIBRARY` is now **subfolder-scope only** (e.g., `mcp_server`). Previously it expected the full path including the library name (e.g., `Shared Documents/mcp_server`), which caused double-path issues on Graph API. When left empty, the server operates on the entire library root.
- **Config:** Default for `SHP_DOC_LIBRARY` changed from `"Shared Documents/mcp_server"` (hardcoded) to `""` (empty = full library access). Users who need to scope to a subfolder set only the subfolder name.
- **Robustness:** Enhanced the `/health` endpoint to perform a live `execute_query` check against SharePoint. Now returns HTTP 503 instead of false-positive 200s if the SP connection is failing.

### Fixed

- **Critical (Graph API):** Fixed 404 errors caused by double library-name in Graph API paths. The Graph API's `drive/root` already **is** the document library, so prepending the library name produced invalid paths like `drive/root:/Shared Documents/Shared Documents:/children`. All three Graph service files (`folder_service_graph.py`, `document_service_graph.py`, `metadata_service_graph.py`) now use a `_drive_item_url()` helper that correctly handles:
  - **Root access:** `drive/root/children` (when no subfolder scope is set)
  - **Nested access:** `drive/root:/subfolder:/children` (when `SHP_DOC_LIBRARY` is set)
- **Config:** Office365 REST API path builder now correctly constructs `library_name/scope/sub_path`, filtering out empty segments to avoid double slashes.
- **Security:** Added Local File Inclusion (LFI) protection to `Upload_Document_From_Path` to restrict AI agents from reading sensitive local paths.
- **Robustness:** Applied explicit return type hints (`-> dict[str, Any]` and `-> list[dict[str, Any]]`) to all 8 MCP document tools to strengthen static analysis and protocol reliability.
- **Documentation:** Added comprehensive PEP-257 docstrings to all tool entry points for better intellisenense and internal maintainability.

### Files Changed

| File                                                        | What changed                                                                                                                               |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `src/mcp_sharepoint/config/settings.py`                     | Added `shp_library_name` field; changed `shp_doc_library` default from `"Shared Documents/mcp_server"` to `""` (empty); updated `__repr__` |
| `src/mcp_sharepoint/server.py`                              | Log message now distinguishes scoped vs full-library mode, includes `library_name`                                                         |
| `src/mcp_sharepoint/services/folder_service_graph.py`       | Replaced `_normalize_path` (no library prefix); added `_drive_item_url()` helper; updated all endpoint construction                        |
| `src/mcp_sharepoint/services/document_service_graph.py`     | Same as above — `_normalize_path` + `_drive_item_url()`, updated all ~10 endpoint calls                                                    |
| `src/mcp_sharepoint/services/metadata_service_graph.py`     | Same as above — `_normalize_path` + `_drive_item_url()`, updated get/update metadata endpoints                                             |
| `src/mcp_sharepoint/services/folder_service_office365.py`   | `_sp_path` now builds from `library_name + scope + sub_path` (filters empty parts)                                                         |
| `src/mcp_sharepoint/services/document_service_office365.py` | Same `_sp_path` fix                                                                                                                        |
| `src/mcp_sharepoint/services/metadata_service_office365.py` | Same `_sp_path` fix                                                                                                                        |
| `.env`                                                      | `SHP_DOC_LIBRARY=` (empty); added commented `SHP_LIBRARY_NAME`                                                                             |
| `.env.example`                                              | Updated docs and defaults; `SHP_DOC_LIBRARY` commented out; added `SHP_LIBRARY_NAME`                                                       |
| `docker-compose.yml`                                        | Added `SHP_LIBRARY_NAME` env var; `SHP_DOC_LIBRARY` defaults to empty                                                                      |

### Migration Guide (from previous config)

**Before:**

```env
SHP_DOC_LIBRARY=Shared Documents/mcp_server
```

**After:**

```env
# Library name (only needed for Office365 REST API; Graph auto-detects)
# SHP_LIBRARY_NAME=Shared Documents

# Subfolder scope (empty = full library, just the subfolder name)
SHP_DOC_LIBRARY=mcp_server
```

If you were using Graph API (`SHP_API_TYPE=graphql` or `graph`), only `SHP_DOC_LIBRARY` matters — set it to the subfolder name alone, or leave empty for full access.

### Planned

- `Get_Recent_Files` — list recently modified documents
- `Find_Files_By_Type` — filter by extension
- `Create_Sharing_Link` — shareable links with expiry and permission level
- `Get_File_Permissions` — list access permissions on files/folders
- `Remove_Sharing` — revoke shared access
- `List_Items` — read items from SharePoint lists
- `Create_List_Item` — add new list items
- `Update_List_Item` — update list item fields
- `Delete_List_Item` — remove list items
- `List_Sites` — browse available SharePoint sites
- `List_Libraries` — list document libraries in a site
- `Move_Document` — move files between folders
- `Copy_Document` — copy files to another folder
- `Rename_Document` — rename files in-place
- `Get_File_Versions` — view document version history
- `Restore_Version` — restore a previous file version
- `/health` endpoint for Docker and load balancer health checks

---

## [1.0.1] — 2026-02-21

### Added

- **CI/CD:** GitHub Actions workflow for automated DockerHub publishing on version tags
- **CI/CD:** Multi-platform Docker builds (linux/amd64, linux/arm64) with GitHub Actions cache
- **Docker:** Environment variable support for custom image and version (`SHAREPOINT_MCP_IMAGE`, `SHAREPOINT_MCP_VERSION`)
- **Documentation:** Enhanced Docker section in README with pull vs build usage patterns
- **Documentation:** Added custom image/version examples for flexible deployment

### Changed

- **Docker:** Updated `docker-compose.yml` to support both DockerHub pulls and local builds
- **Docker:** Default image now uses `ravikant1918/sharepoint-mcp:latest` from DockerHub
- **Docker:** Build context retained for local development with `--build` flag

### Fixed

- **Security:** Resolved critical path traversal vulnerability in SharePoint directory handling
- **Performance:** Fixed asyncio event loop blocking by wrapping remote operations in `asyncio.to_thread`
- **Performance:** Added `.top(500)` pagination limiting to prevent SharePoint list view threshold crashes
- **Resiliency:** Applied `@sp_retry` decorator to handle Graph API rate limits (HTTP 429) across all services
- **CI/CD:** Enforced lowercase Docker image names in GitHub Actions publish workflow
- **Robustness:** Switched file download fallback from local directory to secure system temporary directory

---

## [1.0.0] — 2026-02-20

### Added

- README: Table of Contents with anchor navigation
- README: VS Code Copilot (Agent Mode) integration guide
- README: Cursor / Continue integration guide
- README: Limitations section
- README: Troubleshooting section (auth, connection, debug logging, permissions)
- README: Podman compatibility note in Docker section
- Non-root container security feature in Docker
- Roadmap v1.1.0 with 18 planned features across 6 categories

### Changed

- Bumped version to `1.0.0` (production-stable)
- Fixed tool count: "12 Tools" → "13 Tools" in README
- Fixed Docker healthcheck: replaced non-existent `/health` endpoint with TCP socket check
- Removed stale `curl /health` reference from Docker quickstart
- Improved SEO: added "Model Context Protocol" and "VS Code Copilot" keywords
- Renamed "Claude Desktop Integration" → "Integrations" (covers Claude, VS Code, Cursor)
- Updated `docker-compose.yml` healthcheck to match Dockerfile fix

## [0.2.0] — 2026-02-19

### Added

- `docs/` directory with full documentation (getting-started, configuration, tools-reference, architecture, azure-setup, contributing, changelog)
- `exceptions.py` — `SharePointConfigError`, `SharePointConnectionError`, `SharePointOperationError`
- `config/settings.py` — validated settings via env vars with fail-fast startup
- `core/client.py` — `get_sp_context()` singleton factory with `lru_cache`
- `services/folder_service.py` — isolated folder business logic
- `services/document_service.py` — isolated document business logic
- `services/metadata_service.py` — isolated metadata business logic
- `tools/folder_tools.py`, `tools/document_tools.py`, `tools/metadata_tools.py` — thin `@mcp.tool()` wrappers
- `utils/parsers.py` — lazy-import file parsers (PDF, Excel, Word, detect type)
- `tests/` — pytest suite with 15 tests (folder service + parsers)
- `Makefile` — `install`, `install-dev`, `run`, `inspect`, `test`, `check`, `clean` targets
- `[project.optional-dependencies]` dev extras in `pyproject.toml`

### Changed

- Refactored from flat 4-file layout to domain-driven sub-package structure
- `server.py` now owns the shared `FastMCP` instance and bootstrap logic
- Entry point updated to `mcp_sharepoint:run`
- Bumped version to `0.2.0`

### Removed

- `common.py` (replaced by `config/settings.py` + `core/client.py`)
- `resources.py` (replaced by `services/` + `utils/parsers.py`)
- `tools.py` (replaced by `tools/` sub-package)
- `AZURE_PORTAL_GUIDE.md` (moved to `docs/azure-setup.md`)
