# Tools Reference

Complete reference for all **13 MCP tools** provided by this server.

---

## 📁 Folder Management

### `List_SharePoint_Folders`
List all sub-folders in a directory (or the library root).

| Parameter | Type | Required | Description |
|---|---|---|---|
| `parent_folder` | string | No | Relative path from library root. Omit for root. |

**Returns:** Array of `{ name, url, created, modified }`

---

### `Get_SharePoint_Tree`
Get a recursive tree view of folders and files.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `parent_folder` | string | No | Starting folder. Omit for root. |

**Returns:** Nested tree `{ name, path, type, created, modified, children: [...] }`

> Tree depth and batch size are controlled by `SHP_MAX_DEPTH` and `SHP_MAX_FOLDERS_PER_LEVEL`.

---

### `Create_Folder`
Create a new folder.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `folder_name` | string | **Yes** | Name of the folder to create |
| `parent_folder` | string | No | Parent path. Omit for library root. |

**Returns:** `{ success, message, folder: { name, url } }`

---

### `Delete_Folder`
Delete an **empty** folder (fails if it contains files or sub-folders).

| Parameter | Type | Required | Description |
|---|---|---|---|
| `folder_path` | string | **Yes** | Relative path of the folder to delete |

**Returns:** `{ success, message }`

---

## 📄 Document Management

### `List_SharePoint_Documents`
List all files in a folder with metadata.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `folder_name` | string | **Yes** | Relative path of the folder |

**Returns:** Array of `{ name, url, size, created, modified }`

---

### `Get_Document_Content`
Retrieve and decode file content. Automatically parses PDF, Word, Excel, and text files.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `folder_name` | string | **Yes** | Folder containing the file |
| `file_name` | string | **Yes** | Name of the file |

**Returns (text files):** `{ name, content_type: "text", content, size, ... }`  
**Returns (binary):** `{ name, content_type: "binary", content_base64, size }`

Supported formats: `.pdf`, `.docx`, `.doc`, `.xlsx`, `.xls`, `.txt`, `.json`, `.xml`, `.html`, `.md`, `.py`, `.js`, `.css`, `.yaml`

---

### `Upload_Document`
Upload a new file by passing content directly.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `folder_name` | string | **Yes** | Destination folder |
| `file_name` | string | **Yes** | Name for the uploaded file |
| `content` | string | **Yes** | File content (UTF-8 string or Base64) |
| `is_base64` | boolean | No | Set `true` if `content` is Base64-encoded |

**Returns:** `{ success, message, file: { name, url } }`

---

### `Upload_Document_From_Path`
Upload a local file directly from the filesystem (no Base64 needed).

| Parameter | Type | Required | Description |
|---|---|---|---|
| `folder_name` | string | **Yes** | Destination folder in SharePoint |
| `file_path` | string | **Yes** | Absolute local path to the file |
| `new_file_name` | string | No | Override the file name on SharePoint |

**Returns:** `{ success, message, file: { name, url } }`

---

### `Update_Document`
Overwrite an existing file's content.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `folder_name` | string | **Yes** | Folder containing the file |
| `file_name` | string | **Yes** | Name of the file to update |
| `content` | string | **Yes** | New content |
| `is_base64` | boolean | No | Set `true` if content is Base64-encoded |

**Returns:** `{ success, message, file: { name, url } }`

---

### `Delete_Document`
Permanently delete a file.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `folder_name` | string | **Yes** | Folder containing the file |
| `file_name` | string | **Yes** | Name of the file to delete |

**Returns:** `{ success, message }`

---

### `Download_Document`
Download a file to the local filesystem.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `folder_name` | string | **Yes** | Source folder in SharePoint |
| `file_name` | string | **Yes** | File to download |
| `local_path` | string | **Yes** | Full local path to save the file |

**Returns:** `{ success, path, size, method }` — `method` is `"primary"` or `"fallback"` (`./downloads/`)

---

## 🏷️ Metadata Management

### `Get_File_Metadata`
Retrieve all SharePoint list-item metadata fields for a file.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `folder_name` | string | **Yes** | Folder containing the file |
| `file_name` | string | **Yes** | File to inspect |

**Returns:** `{ success, metadata: { field: value, ... }, file: { name, path } }`

---

### `Update_File_Metadata`
Update one or more list-item metadata fields.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `folder_name` | string | **Yes** | Folder containing the file |
| `file_name` | string | **Yes** | File to update |
| `metadata` | object | **Yes** | Key-value pairs to set (booleans and lists supported) |

**Returns:** `{ success, message }`


---

## 🩺 Operational Endpoint (HTTP/SSE)

While not an MCP tool, the server also exposes a health endpoint for runtime checks:

- `GET /health` → `{ status, version, transport, tools }`

This is useful for Docker health checks, load balancers, and uptime monitoring.
