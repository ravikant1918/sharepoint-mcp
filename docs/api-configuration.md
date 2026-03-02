# API Configuration Guide

## Overview

SharePoint MCP now supports **both Office365 REST API and Microsoft Graph API**, giving you flexibility based on your organization's SharePoint configuration.

## Supported APIs

### 1. Office365 REST API (Default)

- **Best for**: Traditional SharePoint Online deployments
- **Auth method**: Client Credentials (App ID + Secret)
- **Protocol**: REST API
- **Stability**: Mature, widely deployed

### 2. Microsoft Graph API

- **Best for**: Organizations using GraphQL-based SharePoint access
- **Auth method**: MSAL with Client Credentials
- **Protocol**: Microsoft Graph REST API (GraphQL-compatible)
- **Benefits**: Modern API, better integration with Microsoft 365 ecosystem

## Configuration

### Environment Variable

Add this environment variable to choose your API:

```bash
# Use Office365 REST API (default)
SHP_API_TYPE=office365

# OR use Microsoft Graph API
SHP_API_TYPE=graph
```

### Complete Configuration Example

#### For Office365 REST API

```.env
# Required
SHP_ID_APP=your-app-id
SHP_ID_APP_SECRET=your-app-secret
SHP_SITE_URL=https://yourtenant.sharepoint.com/sites/yoursite
SHP_TENANT_ID=your-tenant-id

# API Type
SHP_API_TYPE=office365

# Optional
SHP_DOC_LIBRARY=Shared Documents/mcp_server
```

#### For Microsoft Graph API

```.env
# Required
SHP_ID_APP=your-app-id
SHP_ID_APP_SECRET=your-app-secret
SHP_SITE_URL=https://yourtenant.sharepoint.com/sites/yoursite
SHP_TENANT_ID=your-tenant-id

# API Type
SHP_API_TYPE=graph

# Optional
SHP_DOC_LIBRARY=Shared Documents/mcp_server
```

## App Registration & Permissions

### Office365 REST API Permissions

In Azure AD, grant your app:

```
SharePoint Application Permissions:
- Sites.FullControl.All
- Sites.Read.All
- Sites.ReadWrite.All
```

### Microsoft Graph API Permissions

In Azure AD, grant your app:

```
Microsoft Graph Application Permissions:
- Sites.FullControl.All
- Sites.Read.All
- Sites.ReadWrite.All
- Files.ReadWrite.All
```

## How It Works

The SharePoint MCP server uses an **adapter pattern** that automatically routes requests to the appropriate API implementation based on your `SHP_API_TYPE` setting:

```
User Request
    ↓
Unified Service Layer (document_service.py, folder_service.py, etc.)
    ↓
    ├─→ Office365 Implementation (if SHP_API_TYPE=office365)
    │   └─→ document_service_office365.py
    │
    └─→ Graph Implementation (if SHP_API_TYPE=graph)
        └─→ document_service_graph.py
```

## Switching Between APIs

You can switch between APIs at any time by changing the `SHP_API_TYPE` environment variable and restarting the server:

```bash
# Update .env file
SHP_API_TYPE=graph

# Restart the server
sharepoint-mcp
```

## Feature Compatibility

All 14 MCP tools work identically with both APIs:

| Feature              | Office365 API | Graph API |
| -------------------- | ------------- | --------- |
| List Documents       | ✅            | ✅        |
| Get Document Content | ✅            | ✅        |
| Upload Document      | ✅            | ✅        |
| Update Document      | ✅            | ✅        |
| Delete Document      | ✅            | ✅        |
| Download Document    | ✅            | ✅        |
| List Folders         | ✅            | ✅        |
| Create Folder        | ✅            | ✅        |
| Delete Folder        | ✅            | ✅        |
| Get Folder Tree      | ✅            | ✅        |
| Search Documents     | ✅            | ✅        |
| Get File Metadata    | ✅            | ✅        |
| Update File Metadata | ✅            | ✅        |
| Upload from Path     | ✅            | ✅        |

## Troubleshooting

### Office365 API Issues

**Error: "Failed to create Office365 client"**

- Verify `SHP_ID_APP` and `SHP_ID_APP_SECRET` are correct
- Ensure app has SharePoint permissions (not Graph permissions)
- Check `SHP_SITE_URL` is accessible

### Graph API Issues

**Error: "Failed to acquire access token"**

- Verify app has Microsoft Graph permissions (not just SharePoint)
- Check `SHP_TENANT_ID` is correct
- Ensure MSAL authentication is configured properly

**Error: "Cannot determine site ID"**

- Verify `SHP_SITE_URL` format: `https://tenant.sharepoint.com/sites/sitename`
- Check app has `Sites.Read.All` Graph API permission

### General Issues

**How do I know which API I'm using?**

Check the server logs on startup:

```
# Office365 API
INFO: Using Office365 REST API client
INFO: Office365 client context initialized for https://...

# Graph API
INFO: Using Microsoft Graph API client
INFO: Microsoft Graph API client initialized for https://...
```

**Can I use both APIs simultaneously?**

No, you must choose one API type per server instance. However, you can run multiple server instances with different configurations.

## Performance Considerations

- **Office365 API**: Generally faster for bulk operations, direct REST calls
- **Graph API**: Better for complex queries, integrated Microsoft 365 workflows
- Both APIs support retry logic and error handling

## Migration Guide

### From Office365 to Graph

1. Update Azure AD app registration to include Graph API permissions
2. Grant admin consent for Graph permissions
3. Update `.env`: `SHP_API_TYPE=graph`
4. Restart server
5. Test critical workflows

### From Graph to Office365

1. Ensure Azure AD app has SharePoint application permissions
2. Grant admin consent
3. Update `.env`: `SHP_API_TYPE=office365`
4. Restart server
5. Test critical workflows

## Best Practices

1. **Test both APIs** in development before production deployment
2. **Document your choice** in your deployment documentation
3. **Monitor logs** for API-specific errors
4. **Keep credentials secure** - both APIs use sensitive client secrets
5. **Use environment variables** - never hardcode API type or credentials

## Support

For API-specific issues:

- Office365 API: [Office365 REST Python Client](https://github.com/vgrem/Office365-REST-Python-Client)
- Graph API: [Microsoft Graph Documentation](https://docs.microsoft.com/en-us/graph/)
- SharePoint MCP: [GitHub Issues](https://github.com/ravikant1918/sharepoint-mcp/issues)
