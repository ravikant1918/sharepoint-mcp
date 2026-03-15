# 🎯 Using SharePoint MCP Server in VS Code & Chat Clients

This guide shows how to integrate the SharePoint MCP server with various chat clients.

## 🚀 Quick Start

```bash
# Run the automated setup
./setup-mcp.sh
```

---

## 📋 Manual Setup Instructions

### 1️⃣ For VS Code (GitHub Copilot Chat)

#### Prerequisites

- VS Code installed
- GitHub Copilot extension installed
- MCP support in Copilot (check for latest updates)

#### Setup Steps

**Option A: User Settings (Recommended)**

1. Open VS Code
2. Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
3. Type: `Preferences: Open User Settings (JSON)`
4. Add this configuration:

```json
{
  "mcp.servers": {
    "sharepoint": {
      "command": "python3",
      "args": ["-m", "mcp_sharepoint"],
      "cwd": "/Users/b0272302/Projects/sharepoint-mcp",
      "env": {
        "SHP_API_TYPE": "graphql",
        "TRANSPORT": "stdio"
      }
    }
  },
  "github.copilot.chat.mcp.enabled": true
}
```

5. Save and restart VS Code
6. Open Copilot Chat and try: "@sharepoint list all tools"

**Option B: Workspace Settings**

1. Open your workspace folder
2. Create `.vscode/settings.json`
3. Copy contents from `vscode-mcp-config.json`
4. Restart VS Code

---

### 2️⃣ For Claude Desktop

#### Prerequisites

- Claude Desktop app installed
- Python 3.10+ installed

#### Setup Steps

1. **Find Claude config location:**
   - **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`

2. **Edit the config file:**

```json
{
  "mcpServers": {
    "sharepoint": {
      "command": "python3",
      "args": ["-m", "mcp_sharepoint"],
      "cwd": "/Users/b0272302/Projects/sharepoint-mcp",
      "env": {
        "SHP_API_TYPE": "graphql",
        "SHP_DOC_LIBRARY": "Shared Documents/mcp_server",
        "TRANSPORT": "stdio",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

3. **Restart Claude Desktop**

4. **Test in chat:**
   - "What MCP tools are available?"
   - "List files in my SharePoint"
   - "@sharepoint list all folders"

---

### 3️⃣ For Cursor IDE

#### Setup Steps

1. Open Cursor Settings (`Cmd+,` or `Ctrl+,`)
2. Search for "MCP" in settings
3. Add MCP server configuration:

```json
{
  "mcp.servers": {
    "sharepoint": {
      "command": "python3",
      "args": ["-m", "mcp_sharepoint"],
      "env": {
        "SHP_API_TYPE": "graphql"
      }
    }
  }
}
```

4. Restart Cursor
5. In Cursor Chat: "@sharepoint search for documents"

---

### 4️⃣ For Cline (VSCode Extension)

#### Setup Steps

1. Install Cline extension in VS Code
2. Open Cline settings
3. Add MCP server:

```json
{
  "mcp.servers.sharepoint": {
    "command": "python3",
    "args": ["-m", "mcp_sharepoint"],
    "cwd": "/Users/b0272302/Projects/sharepoint-mcp"
  }
}
```

4. Restart VS Code
5. Open Cline and use SharePoint tools

---

### 5️⃣ For HTTP/SSE Mode (Remote Access)

If you want to access the server remotely (Docker, cloud, etc.):

#### Start Server in SSE Mode

```bash
# Edit .env
TRANSPORT=sse
HTTP_HOST=0.0.0.0
HTTP_PORT=8000

# Start server
python3 -m mcp_sharepoint
```

#### Connect from Client

```json
{
  "mcpServers": {
    "sharepoint": {
      "url": "http://localhost:8000/mcp",
      "transport": "sse"
    }
  }
}
```

---

## 🧪 Testing Your Setup

### Test 1: Verify Server Health

```bash
curl http://localhost:8000/health | python3 -m json.tool
```

Expected output:

```json
{
  "status": "ok",
  "tools": 14,
  "sharepoint": "connected"
}
```

### Test 2: Run MCP Client Test

```bash
python3 test_mcp_client.py
```

Expected: List of 14 available tools

### Test 3: Test in Chat

Try these commands in your chat client:

1. **List available tools:**
   - "What SharePoint tools are available?"
   - "@sharepoint list all tools"

2. **List documents:**
   - "List all documents in SharePoint"
   - "@sharepoint list documents in Shared Documents/mcp_server"

3. **Search:**
   - "Search SharePoint for files containing 'report'"
   - "@sharepoint search for \*.xlsx files"

4. **Get folder tree:**
   - "Show me the SharePoint folder structure"
   - "@sharepoint get folder tree"

---

## 📊 Available Tools (14 Total)

### Document Operations

1. `List_SharePoint_Documents` - List files with metadata
2. `Search_SharePoint` - KQL search
3. `Get_Document_Content` - Read file content
4. `Upload_Document` - Upload new files
5. `Upload_Document_From_Path` - Upload from local path
6. `Update_Document` - Update file content
7. `Delete_Document` - Delete files
8. `Download_Document` - Download files

### Folder Operations

9. `List_SharePoint_Folders` - List subfolders
10. `Get_SharePoint_Tree` - Recursive tree view
11. `Create_Folder` - Create folders
12. `Delete_Folder` - Delete folders

### Metadata Operations

13. `Get_File_Metadata` - Get file properties
14. `Update_File_Metadata` - Update properties

---

## 🔧 Troubleshooting

### Issue: "MCP server not found"

**Solution:**

```bash
# Verify Python installation
python3 -m mcp_sharepoint --help

# Check if module is installed
pip3 list | grep mcp

# Reinstall if needed
cd /Users/b0272302/Projects/sharepoint-mcp
pip3 install -e .
```

### Issue: "SharePoint connection failed"

**Solution:**

```bash
# Verify .env file has correct credentials
cat .env | grep SHP_

# Test connection manually
python3 -c "from src.mcp_sharepoint.core import get_sp_context; client = get_sp_context(); print('✅ Connected')"
```

### Issue: "Tools not showing in chat"

**Solution:**

1. Verify MCP config syntax is valid JSON
2. Restart the chat application completely
3. Check chat application supports MCP protocol
4. View logs: `tail -f /tmp/mcp-server.log`

### Issue: "GraphQL errors"

**Solution:**

```bash
# Switch to Office365 API temporarily
export SHP_API_TYPE=office365

# Or update .env file
echo "SHP_API_TYPE=office365" >> .env
```

---

## 📚 Example Chat Interactions

### Example 1: List Files

```
You: "List all documents in my SharePoint"
Assistant: *calls List_SharePoint_Documents*
Result: Shows list of files with metadata
```

### Example 2: Upload File

```
You: "Upload report.pdf to SharePoint folder Reports"
Assistant: *calls Upload_Document_From_Path*
Result: File uploaded successfully
```

### Example 3: Search

```
You: "Find all Excel files modified this week"
Assistant: *calls Search_SharePoint with KQL query*
Result: Shows matching files
```

---

## 🎯 Next Steps

1. ✅ Verify server is running: `curl http://localhost:8000/health`
2. ✅ Add to your chat client using config above
3. ✅ Restart the chat application
4. ✅ Test with: "What SharePoint tools are available?"
5. ✅ Start using SharePoint in natural language!

---

## 📖 Additional Resources

- [MCP Protocol Docs](https://modelcontextprotocol.io/)
- [SharePoint MCP README](../README.md)
- [Configuration Guide](../docs/configuration.md)
- [API Reference](../docs/tools-reference.md)

---

## 🆘 Need Help?

- Check logs: `tail -f /tmp/mcp-server.log`
- Run diagnostics: `./setup-mcp.sh`
- Test client: `python3 test_mcp_client.py`
- View health: `curl http://localhost:8000/health`
