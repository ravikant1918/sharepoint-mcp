# Getting Started

## Prerequisites

- Python 3.10+
- A Microsoft 365 / SharePoint Online tenant
- An Azure AD app registration with SharePoint permissions (see [azure-setup.md](azure-setup.md))

## 1. Clone & Install

```bash
git clone https://github.com/ravikant1918/mcp-sharepoint.git
cd mcp-sharepoint

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# Install the package (editable mode)
pip install -e .
```

Or with `make`:

```bash
make install
```

## 2. Configure Environment

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Open `.env` and set the required values:

```env
SHP_ID_APP=your-azure-app-client-id
SHP_ID_APP_SECRET=your-azure-app-client-secret
SHP_TENANT_ID=your-microsoft-tenant-id
SHP_SITE_URL=https://your-tenant.sharepoint.com/sites/your-site
SHP_DOC_LIBRARY=Shared Documents/mcp_server
```

See [configuration.md](configuration.md) for all options.

## 3. Run the Server

### With MCP Inspector (recommended for testing)

```bash
make inspect
# or
npx @modelcontextprotocol/inspector -- python -m mcp_sharepoint
```

Open the URL printed in the terminal to test all 12 tools interactively.

### Directly (stdio mode)

```bash
make run
# or
python -m mcp_sharepoint
```

## 4. Integrate with Claude Desktop

Add this to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sharepoint": {
      "command": "mcp-sharepoint",
      "env": {
        "SHP_ID_APP": "your-app-id",
        "SHP_ID_APP_SECRET": "your-app-secret",
        "SHP_SITE_URL": "https://your-tenant.sharepoint.com/sites/your-site",
        "SHP_DOC_LIBRARY": "Shared Documents/your-folder",
        "SHP_TENANT_ID": "your-tenant-id"
      }
    }
  }
}
```

## 5. Run Tests

```bash
make install-dev    # installs pytest extras
make test           # runs all 15 tests
```
