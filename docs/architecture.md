# Architecture

## Project Structure

```
mcp-sharepoint/
├── src/
│   └── mcp_sharepoint/
│       ├── __init__.py              Package entry point
│       ├── server.py                Shared FastMCP instance + bootstrap
│       ├── exceptions.py            Custom exception hierarchy
│       │
│       ├── config/
│       │   └── settings.py          Environment variable validation
│       │
│       ├── core/
│       │   └── client.py            SharePoint ClientContext factory
│       │
│       ├── services/                Pure business logic (no MCP knowledge)
│       │   ├── folder_service.py    Folder CRUD + tree building
│       │   ├── document_service.py  File upload/download/read/delete
│       │   └── metadata_service.py  List item metadata read/write
│       │
│       ├── tools/                   MCP tool registrations (thin wrappers)
│       │   ├── folder_tools.py      4 tools → delegates to folder_service
│       │   ├── document_tools.py    7 tools → delegates to document_service
│       │   └── metadata_tools.py    2 tools → delegates to metadata_service
│       │
│       └── utils/
│           └── parsers.py           PDF / Excel / Word content extractors
│
├── tests/
│   ├── conftest.py                  Shared pytest fixtures
│   ├── test_folder_service.py       Folder service unit tests
│   └── test_parsers.py              Parser unit tests (12 parametrised cases)
│
├── docs/                            ← You are here
├── .env.example                     Environment variable template
├── pyproject.toml                   Package metadata + pytest config
└── Makefile                         Developer convenience targets
```

## Layer Diagram

```
┌─────────────────────────────────────────┐
│  MCP Client (Claude, Cursor, etc.)       │
└───────────────────┬─────────────────────┘
                    │ stdio / SSE
┌───────────────────▼─────────────────────┐
│  tools/  (thin @mcp.tool wrappers)       │
│  folder_tools · document_tools ·         │
│  metadata_tools                          │
└───────────────────┬─────────────────────┘
                    │ function calls
┌───────────────────▼─────────────────────┐
│  services/  (business logic)             │
│  folder_service · document_service ·     │
│  metadata_service                        │
└──────────┬────────────────┬─────────────┘
           │                │
┌──────────▼──────┐  ┌──────▼──────────────┐
│  core/client.py │  │  utils/parsers.py    │
│  ClientContext  │  │  PDF/Excel/Word      │
└──────────┬──────┘  └─────────────────────┘
           │
┌──────────▼──────────────────────────────┐
│  Microsoft SharePoint REST API           │
└─────────────────────────────────────────┘
```

## Design Principles

### Separation of Concerns
- **`tools/`** — only knows about MCP (`@mcp.tool`, parameters, return values)
- **`services/`** — only knows about SharePoint operations; zero MCP imports
- **`utils/`** — pure functions, no dependencies on config or SharePoint

### Fail Fast
`get_settings()` is called at server startup from `main()`. If any required env var is missing, `SharePointConfigError` is raised before any tool can be invoked.

### Singletons via `lru_cache`
Both `get_settings()` and `get_sp_context()` are wrapped with `@lru_cache(maxsize=1)` — they are instantiated once per process. This avoids repeated env var lookups and redundant `ClientContext` creation.

### Lazy Imports in Parsers
Heavy libraries (`fitz`, `pandas`, `docx`) are imported **inside** the parser functions. This means the package can load without those libraries being present — only the specific file types fail if their library is missing.

## Exception Hierarchy

```
SharePointError (base)
├── SharePointConfigError    — missing/invalid environment variables
├── SharePointConnectionError — cannot establish ClientContext
└── SharePointOperationError  — SharePoint API call failed
                               └── .operation: str
                               └── .detail: str
```
