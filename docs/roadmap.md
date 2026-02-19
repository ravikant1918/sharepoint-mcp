# Roadmap

This document outlines planned features and improvements for future versions of **sharepoint-mcp**.

> Items are organised by priority. Community contributions are welcome — see [contributing.md](contributing.md).

---

## v1.1.0 — Search & Discovery

- [ ] **`Search_SharePoint`** tool — full-text search across files and folders using SharePoint KQL
- [ ] **`Get_Recent_Files`** tool — list recently modified documents across the library
- [ ] **`Find_Files_By_Type`** tool — filter by extension (`.pdf`, `.docx`, etc.)

---

## v1.2.0 — Permissions & Sharing

- [ ] **`Get_File_Permissions`** tool — list who has access to a file/folder
- [ ] **`Share_File`** tool — create a shareable link with configurable expiry and permissions
- [ ] **`Remove_Sharing`** tool — revoke access to a shared file

---

## v1.3.0 — MCP Resources Support

- [ ] Expose SharePoint folders as **MCP Resources** (not just tools)
- [ ] Allow AI agents to *browse* the document library via resource URIs
- [ ] Support streaming large file content via resources

---

## v1.4.0 — Async SharePoint Client

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
