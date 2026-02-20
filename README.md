<div align="center">

<!-- mcp-name: io.github.ravikant1918/sharepoint-mcp -->

# 🗂️ sharepoint-mcp

### **The MCP Server that gives your AI agent a brain for Microsoft SharePoint**

[![CI](https://github.com/ravikant1918/sharepoint-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/ravikant1918/sharepoint-mcp/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/sharepoint-mcp.svg)](https://pypi.org/project/sharepoint-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/sharepoint-mcp.svg)](https://pypi.org/project/sharepoint-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://github.com/ravikant1918/sharepoint-mcp#-docker)
[![MCP](https://img.shields.io/badge/MCP-compatible-blueviolet)](https://modelcontextprotocol.io)

A production-grade **Model Context Protocol (MCP) server** for **Microsoft SharePoint**.  
Connect **Claude Desktop**, **VS Code Copilot**, **Cursor**, **Continue**, or any MCP-compatible AI agent  
to your SharePoint — read files, manage folders, and reason over your organisation's knowledge.

[📚 Docs](docs/) · [🗺️ Roadmap](docs/roadmap.md) · [🐛 Bugs](https://github.com/ravikant1918/sharepoint-mcp/issues) · [💡 Features](https://github.com/ravikant1918/sharepoint-mcp/issues/new?template=feature_request.yml)

</div>

---

## 📑 Table of Contents

- [Why sharepoint-mcp?](#-why-sharepoint-mcp)
- [What Your Agent Can Do](#-what-your-agent-can-do)
- [Features](#-features)
- [Quickstart](#-quickstart)
- [Docker](#-docker)
- [Transport Modes](#-transport-modes)
- [Integrations](#-integrations) — Claude Desktop · VS Code Copilot · Cursor
- [All 13 Tools](#️-all-13-tools)
- [Configuration Reference](#️-full-configuration-reference)
- [Limitations](#️-limitations)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [Security](#-security)

---

## 🧠 Why sharepoint-mcp?

> Most AI agents only know what's in their training data.  
> **sharepoint-mcp** gives your agent *live access* to your organisation's real knowledge.

| Without sharepoint-mcp | With sharepoint-mcp |
|---|---|
| 🤷 Agent guesses or hallucinates | Agent reads the actual document |
| 📋 You copy-paste content manually | Agent fetches files automatically |
| 🔒 Knowledge locked in SharePoint | Knowledge flows into your AI workflow |
| 🐌 Static, one-shot answers | Agent reasons, rewrites, and saves back |

---

## 🚀 What Your Agent Can Do

### 📖 Understand Any Document
```
You: "Summarise the Q3 report in the Finance folder"
Agent: → Get_Document_Content("Finance", "Q3_Report.pdf")
       → Reads full extracted text
       → Returns a sharp, accurate summary
```

### ✏️ Read → Reason → Write
```
You: "Translate the proposal to French and save it"
Agent: → Get_Document_Content → translate → Upload_Document
```

### 🗂️ Navigate Your Library
```
You: "What files are in the Legal/Contracts folder?"
Agent: → List_SharePoint_Documents("Legal/Contracts")
```

### 📊 Supported File Formats

| 📄 Format | 🤖 What the Agent Gets |
|---|---|
| **PDF** | Full text from every page |
| **Word** `.docx` `.doc` | Complete document content |
| **Excel** `.xlsx` `.xls` | All sheets as structured text |
| **Text, JSON, Markdown, HTML, YAML, Python** | Raw content as-is |
| **Images, ZIP, binaries** | File type + Base64 |

---

## ✨ Features

| | Feature | Description |
|---|---|---|
| 📁 | **Folder Management** | List, create, delete, get full recursive tree |
| 📄 | **Document Management** | Upload, download, update, delete, read content |
| 🏷️ | **Metadata Management** | Read and update SharePoint list-item fields |
| 🔍 | **Smart Parsing** | Auto-detects PDF / Word / Excel / text |
| 🔁 | **Auto-Retry** | Exponential backoff on SharePoint 429/503 throttling |
| 🚀 | **Dual Transport** | `stdio` for desktop · `http` for Docker/remote |
| 🪵 | **Structured Logging** | JSON in production · coloured console in dev |
| 🐳 | **Docker-Ready** | Single command: `docker compose up -d` |
| 🛡️ | **Non-Root Container** | Runs as unprivileged user inside Docker |
| 🤖 | **CI/CD** | Tested on Python 3.10 · 3.11 · 3.12 · 3.13 |

---

## ⚡ Quickstart

### 1️⃣ Install

```bash
pip install sharepoint-mcp
```

Or from source:
```bash
git clone https://github.com/ravikant1918/sharepoint-mcp.git
cd sharepoint-mcp && pip install -e .
```

### 2️⃣ Configure

```bash
cp .env.example .env
# Open .env and fill in your Azure AD credentials
```

```env
SHP_ID_APP=your-azure-app-client-id
SHP_ID_APP_SECRET=your-azure-app-secret
SHP_TENANT_ID=your-tenant-id
SHP_SITE_URL=https://your-tenant.sharepoint.com/sites/your-site
```

> 🔑 **New to Azure AD?** Follow the [step-by-step guide →](docs/azure-setup.md)

### 3️⃣ Run

```bash
# 🔍 Interactive testing with MCP Inspector
npx @modelcontextprotocol/inspector -- sharepoint-mcp

# ▶️ Run directly
sharepoint-mcp
```

---

## 🐳 Docker

The fastest way to deploy for remote or cloud use:

```bash
cp .env.example .env        # fill in your credentials
docker compose up -d        # start HTTP server on port 8000
```

> **Using Podman?** Just replace `docker` with `podman` — fully compatible.

### Docker Environment Variables

| Variable | Default | Description |
|---|---|---|
| `TRANSPORT` | `http` | `stdio` or `http` |
| `HTTP_HOST` | `0.0.0.0` | Bind address |
| `HTTP_PORT` | `8000` | Port |
| `LOG_FORMAT` | `json` | `json` or `console` |

---

## 🔌 Transport Modes

| Mode | Best For | Set With |
|---|---|---|
| `stdio` | Claude Desktop, Cursor, MCP Inspector | `TRANSPORT=stdio` *(default)* |
| `http` | Docker, remote agents, VS Code Copilot, REST clients | `TRANSPORT=http` |

---

## 🔗 Integrations

### 🤖 Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sharepoint": {
      "command": "sharepoint-mcp",
      "env": {
        "SHP_ID_APP": "your-app-id",
        "SHP_ID_APP_SECRET": "your-app-secret",
        "SHP_SITE_URL": "https://your-tenant.sharepoint.com/sites/your-site",
        "SHP_TENANT_ID": "your-tenant-id",
        "SHP_DOC_LIBRARY": "Shared Documents/your-folder"
      }
    }
  }
}
```

### 💻 VS Code Copilot (Agent Mode)

1. Start the server via Docker or `TRANSPORT=http sharepoint-mcp`
2. Create `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "sharepoint": {
      "url": "http://localhost:8000/mcp/",
      "type": "http"
    }
  }
}
```

3. Open Copilot Chat → switch to **Agent mode** → your 13 SharePoint tools are available.

> ⚠️ **Trailing slash matters** — the URL must end with `/mcp/` (not `/mcp`).

### ⌨️ Cursor / Continue

Add to your MCP config (uses stdio transport):

```json
{
  "mcpServers": {
    "sharepoint": {
      "command": "sharepoint-mcp",
      "env": {
        "SHP_ID_APP": "your-app-id",
        "SHP_ID_APP_SECRET": "your-app-secret",
        "SHP_SITE_URL": "https://your-tenant.sharepoint.com/sites/your-site",
        "SHP_TENANT_ID": "your-tenant-id"
      }
    }
  }
}
```

---

## 🛠️ All 13 Tools

### 📁 Folder Management

| Tool | What It Does |
|---|---|
| `List_SharePoint_Folders` | 📋 List all sub-folders in a directory |
| `Get_SharePoint_Tree` | 🌳 Get full recursive folder + file tree |
| `Create_Folder` | ➕ Create a new folder |
| `Delete_Folder` | 🗑️ Delete an empty folder |

### 📄 Document Management

| Tool | What It Does |
|---|---|
| `List_SharePoint_Documents` | 📋 List all files with metadata |
| `Get_Document_Content` | 📖 Read & parse file content (PDF/Word/Excel/text) |
| `Upload_Document` | ⬆️ Upload file as string or Base64 |
| `Upload_Document_From_Path` | 📂 Upload a local file directly |
| `Update_Document` | ✏️ Overwrite existing file content |
| `Delete_Document` | 🗑️ Permanently delete a file |
| `Download_Document` | ⬇️ Download file to local filesystem |

### 🏷️ Metadata Management

| Tool | What It Does |
|---|---|
| `Get_File_Metadata` | 🔍 Get all SharePoint list-item fields |
| `Update_File_Metadata` | ✏️ Update metadata fields |

---

## ⚙️ Full Configuration Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `SHP_ID_APP` |  | `12345678-1234-1234-1234-123456789012` | Azure AD app client ID |
| `SHP_ID_APP_SECRET` |  | `your-app-secret` | Azure AD client secret |
| `SHP_TENANT_ID` |  | `your-tenant-id` | Microsoft tenant ID |
| `SHP_SITE_URL` |  | `https://your-tenant.sharepoint.com/sites/your-site` | SharePoint site URL |
| `SHP_DOC_LIBRARY` | | `Shared Documents/mcp_server` | Library path |
| `SHP_MAX_DEPTH` | | `15` | Max tree depth |
| `SHP_MAX_FOLDERS_PER_LEVEL` | | `100` | Folders per batch |
| `SHP_LEVEL_DELAY` | | `0.5` | Delay (s) between tree levels |
| `TRANSPORT` | | `stdio` | `stdio` or `http` |
| `HTTP_HOST` | | `0.0.0.0` | HTTP bind host |
| `HTTP_PORT` | | `8000` | HTTP port |
| `LOG_LEVEL` | | `INFO` | `DEBUG` `INFO` `WARNING` `ERROR` |
| `LOG_FORMAT` | | `console` | `console` or `json` |

---

## ⚠️ Limitations

| Limitation | Details |
|---|---|
| **Single site** | Connects to one SharePoint site per server instance (multi-site planned for v2.0) |
| **Sync client** | Uses synchronous SharePoint REST API calls (async client planned for v1.3) |
| **No search** | Full-text search not yet available (planned for v1.1) |
| **No sharing** | Cannot create sharing links yet (planned for v1.1) |
| **Large files** | Very large files may hit memory limits during content extraction |
| **Rate limits** | SharePoint throttling (429/503) is handled with auto-retry, but sustained bulk operations may be slow |

---

## 🔧 Troubleshooting

### Authentication Errors

**Problem:** `Missing or invalid SharePoint credentials`  
**Solution:** Verify all 4 required environment variables are set:
```bash
echo $SHP_ID_APP $SHP_ID_APP_SECRET $SHP_TENANT_ID $SHP_SITE_URL
```

### Connection Issues (HTTP Transport)

**Problem:** Agent can't connect to the MCP server  
**Solution:**
1. Ensure the server is running: `curl http://localhost:8000/mcp/`
2. Check the URL ends with `/mcp/` (trailing slash required)
3. Verify the port is not blocked by a firewall

### Docker Container Unhealthy

**Problem:** `podman ps` / `docker ps` shows `(unhealthy)`  
**Solution:** Check container logs for errors:
```bash
docker logs sharepoint-mcp
```

### Debug Logging

Enable verbose output by setting `LOG_LEVEL=DEBUG`:
```bash
LOG_LEVEL=DEBUG sharepoint-mcp
```

For Docker, add to your `.env` file or `docker-compose.yml`:
```env
LOG_LEVEL=DEBUG
LOG_FORMAT=console
```

### Permission Errors

**Problem:** `Access denied` from SharePoint  
**Solution:**
1. Verify the Azure AD app has the required API permissions
2. Ensure admin consent has been granted (if required by your org)
3. Confirm `SHP_SITE_URL` points to a site your app has access to

---

## 🧪 Development

```bash
git clone https://github.com/ravikant1918/sharepoint-mcp.git
cd sharepoint-mcp
pip install -e ".[dev]"

make test      # run all tests
make inspect   # 🔍 launch MCP Inspector
make check     # quick import sanity check
make clean     # 🧹 remove caches
```

---

## 📚 Documentation

| 📄 Doc | 📝 Description |
|---|---|
| [⚡ Getting Started](docs/getting-started.md) | Full setup guide |
| [⚙️ Configuration](docs/configuration.md) | All environment variables |
| [🛠️ Tools Reference](docs/tools-reference.md) | Detailed tool parameters |
| [🏛️ Architecture](docs/architecture.md) | Design and layer diagram |
| [🔑 Azure Setup](docs/azure-setup.md) | Azure AD app registration guide |
| [🗺️ Roadmap](docs/roadmap.md) | Planned features |
| [📅 Changelog](docs/changelog.md) | Version history |

---

## 🤝 Contributing

Contributions are welcome! Please read [docs/contributing.md](docs/contributing.md) and our [Code of Conduct](CODE_OF_CONDUCT.md).

1. 🍴 Fork the repo
2. 🌿 Create a branch: `git checkout -b feat/my-tool`
3. ✅ Add tests: `make test`
4. 📬 Open a Pull Request

---

## 🔒 Security

Found a vulnerability? Please **do not** open a public issue.  
Report privately via [GitHub Security Advisories](https://github.com/ravikant1918/sharepoint-mcp/security/advisories/new) or see [SECURITY.md](SECURITY.md).

---

<div align="center">

**MIT License © 2026 [Ravi Kant](https://github.com/ravikant1918)**

⭐ If this project helps you, please star it on GitHub!

</div>