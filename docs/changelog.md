# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.1.0-rc] — Unreleased

### Added

- `Search_SharePoint` — full-text search using SharePoint KQL

### Fixed

- **Security:** Added Local File Inclusion (LFI) protection to `Upload_Document_From_Path` to restrict AI agents from reading sensitive local paths.
- **Robustness:** Applied explicit return type hints (`-> dict[str, Any]` and `-> list[dict[str, Any]]`) to all 8 MCP document tools to strengthen static analysis and protocol reliability.
- **Documentation:** Added comprehensive PEP-257 docstrings to all tool entry points for better intellisenense and internal maintainability.

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
