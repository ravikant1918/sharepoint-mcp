# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 1.x |  Yes |

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Report vulnerabilities privately via:
1. **GitHub Security Advisories** — [Report a vulnerability](https://github.com/ravikant1918/sharepoint-mcp/security/advisories/new)
2. **Email** — `developerrk1918@gmail.com` (encrypt with PGP if possible)

### What to include
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response timeline
- **Acknowledgement:** within 48 hours
- **Initial assessment:** within 7 days
- **Fix & disclosure:** coordinated with the reporter

### Scope
The following areas are in scope:
- Credential exposure (SharePoint tokens, Azure secrets)
- Path traversal in file operations
- Injection vulnerabilities in SharePoint queries
- Dependencies with known CVEs
