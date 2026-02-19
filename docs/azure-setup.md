# Azure AD App Registration Guide

This guide shows how to register an Azure AD (Microsoft Entra) application to grant the mcp-sharepoint server access to your SharePoint site.

---

## Step 1 — Register the Application

1. Go to [portal.azure.com](https://portal.azure.com)
2. Navigate to **Microsoft Entra ID** → **App registrations** → **New registration**
3. Fill in:
   - **Name:** `mcp-sharepoint-server` (or any name)
   - **Supported account types:** `Accounts in this organizational directory only`
   - **Redirect URI:** leave blank
4. Click **Register**
5. Copy the **Application (client) ID** → this is your `SHP_ID_APP`
6. Copy the **Directory (tenant) ID** → this is your `SHP_TENANT_ID`

---

## Step 2 — Create a Client Secret

1. In your new app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. Set a description and expiry, then click **Add**
4. **Copy the secret value immediately** (it won't be shown again) → this is your `SHP_ID_APP_SECRET`

---

## Step 3 — Grant SharePoint Permissions

1. Go to **API permissions** → **Add a permission**
2. Select **SharePoint**
3. Choose **Application permissions** (not Delegated)
4. Add the following permissions:

| Permission | Purpose |
|---|---|
| `Sites.ReadWrite.All` | Read and write files and folders |
| `Sites.Manage.All` | Create and delete folders |

5. Click **Add permissions**
6. Click **Grant admin consent for [your tenant]** — requires a Global Administrator

---

## Step 4 — Get Your SharePoint Site URL

1. Navigate to your SharePoint site in a browser
2. The URL format is: `https://your-tenant.sharepoint.com/sites/your-site-name`
3. Copy this — it becomes your `SHP_SITE_URL`

---

## Step 5 — Verify

Set your `.env` file with all the values collected above and run:

```bash
make inspect
```

Click **Connect** in the MCP Inspector. If the connection succeeds, all 12 tools will appear in the **Tools** tab.

---

## Troubleshooting

| Error | Likely Cause | Fix |
|---|---|---|
| `401 Unauthorized` | Wrong client ID or secret | Double-check `SHP_ID_APP` and `SHP_ID_APP_SECRET` |
| `403 Forbidden` | Missing admin consent | Grant admin consent in Azure Portal |
| `404 Not Found` | Wrong site URL or library path | Verify `SHP_SITE_URL` and `SHP_DOC_LIBRARY` |
| `SHP_SITE_URL not set` | Missing `.env` file | Copy `.env.example` to `.env` |
