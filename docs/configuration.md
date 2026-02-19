# Configuration Reference

All configuration is done via environment variables. Copy `.env.example` to `.env` and populate the values.

## Required Variables

| Variable | Description | Example |
|---|---|---|
| `SHP_ID_APP` | Azure AD application (client) ID | `a1b2c3d4-...` |
| `SHP_ID_APP_SECRET` | Azure AD client secret value | `your~secret~here` |
| `SHP_TENANT_ID` | Microsoft Entra tenant ID | `f1e2d3c4-...` |
| `SHP_SITE_URL` | Full URL of the SharePoint site | `https://contoso.sharepoint.com/sites/mysite` |

> **Note:** The server raises `SharePointConfigError` at startup if any required variable is missing.

## Optional Variables

| Variable | Default | Description |
|---|---|---|
| `SHP_DOC_LIBRARY` | `Shared Documents/mcp_server` | Path to the document library (relative to site) |
| `SHP_MAX_DEPTH` | `15` | Max folder depth for `Get_SharePoint_Tree` |
| `SHP_MAX_FOLDERS_PER_LEVEL` | `100` | Folders processed per batch level in tree operations |
| `SHP_LEVEL_DELAY` | `0.5` | Seconds to wait between depth levels (avoids throttling) |
| `LOG_LEVEL` | `INFO` | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

## Example `.env`

```env
# Azure AD
SHP_ID_APP=a1b2c3d4-e5f6-7890-abcd-ef1234567890
SHP_ID_APP_SECRET=your~super~secret~value~here
SHP_TENANT_ID=f1e2d3c4-b5a6-9870-dcba-fe9876543210

# SharePoint
SHP_SITE_URL=https://contoso.sharepoint.com/sites/engineering
SHP_DOC_LIBRARY=Shared Documents/mcp_server

# Tree limits
SHP_MAX_DEPTH=10
SHP_MAX_FOLDERS_PER_LEVEL=50
SHP_LEVEL_DELAY=0.3

# Logging
LOG_LEVEL=INFO
```

## Settings Implementation

Settings are loaded once at startup via `mcp_sharepoint.config.settings.get_settings()` (an `lru_cache`-backed singleton). All service modules call `get_settings()` directly — there are no global module-level variables.
