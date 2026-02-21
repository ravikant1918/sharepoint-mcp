# Roadmap

This document outlines planned features and improvements for future versions of **sharepoint-mcp**.

> Items are organised by priority. Community contributions are welcome — see [contributing.md](contributing.md).

---

## High-Impact Improvements (Recommended Next)

If you want to make this MCP server noticeably better in the next iterations, prioritize these in order:

1. **Search first**: implement `Search_SharePoint` so agents can find relevant files without guessing folder paths.
2. **Document lifecycle**: add move/copy/rename tools so agents can manage files after generation workflows.
3. **Share-safe collaboration**: add sharing-link + permission inspection tools to support real team workflows.
4. **List item CRUD**: unlock non-document SharePoint data (tasks, trackers, inventories) via list tools.
5. **Performance uplift**: move to an async client for faster concurrent tool calls.
6. **MCP resources**: expose browsable resources for better discovery UX in MCP-native clients.

---

## v1.1.0 — Search, Sharing, Lists & Site Management

This release closes every feature gap with competing SharePoint MCP servers and adds powerful new capabilities.

### 🔍 Search & Discovery
- [ ] **`Search_SharePoint`** — full-text search across files and folders using SharePoint KQL
- [ ] **`Get_Recent_Files`** — list recently modified documents across the library
- [ ] **`Find_Files_By_Type`** — filter by extension (`.pdf`, `.docx`, etc.)

### 🔗 Permissions & Sharing
- [ ] **`Create_Sharing_Link`** — generate a shareable link with configurable expiry and permission level (view / edit)
- [ ] **`Get_File_Permissions`** — list who has access to a file or folder
- [ ] **`Remove_Sharing`** — revoke access to a shared file

### 📋 SharePoint Lists
- [ ] **`List_Items`** — read items from any SharePoint list
- [ ] **`Create_List_Item`** — add a new item to a SharePoint list
- [ ] **`Update_List_Item`** — update fields on an existing list item
- [ ] **`Delete_List_Item`** — remove an item from a list

### 🌐 Site & Library Management
- [ ] **`List_Sites`** — browse available SharePoint sites (with optional search)
- [ ] **`List_Libraries`** — list all document libraries in a site

### 📄 Document Operations
- [ ] **`Move_Document`** — move a file between folders
- [ ] **`Copy_Document`** — copy a file to another folder
- [ ] **`Rename_Document`** — rename a file in-place
- [ ] **`Get_File_Versions`** — view version history of a document
- [ ] **`Restore_Version`** — restore a previous version of a file

### 🏥 Server Health
- [ ] **`/health` endpoint** — proper health-check route for Docker and load balancers

---

## v1.2.0 — MCP Resources Support

- [ ] Expose SharePoint folders as **MCP Resources** (not just tools)
- [ ] Allow AI agents to *browse* the document library via resource URIs
- [ ] Support streaming large file content via resources

---

## v1.3.0 — Async SharePoint Client

- [ ] Replace synchronous `office365-rest-python-client` calls with a native async client
- [ ] Reduce latency on concurrent tool calls from AI agents
- [ ] Support connection pooling for multi-user scenarios

---

## v2.0.0 — Multi-Site & Multi-Tenant

- [ ] Support multiple SharePoint sites per server instance
- [ ] Per-tool site routing via tool parameters
- [ ] Microsoft Graph API fallback for features not in SharePoint REST API

---

## Ideas & Community Requests

Have a feature idea? [Open a Feature Request](https://github.com/ravikant1918/sharepoint-mcp/issues/new?template=feature_request.yml).
