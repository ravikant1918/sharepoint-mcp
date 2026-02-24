---
description: Git branching strategy for sharepoint-mcp releases
---

# Branching Strategy

## Branch Types

| Branch | Pattern | Purpose | Merges Into |
|--------|---------|---------|-------------|
| **main** | `main` | Stable production code | — |
| **feature** | `feature/<name>` | New features | `release/vX.Y.Z` |
| **bugfix** | `bugfix/<name>` | Non-urgent bug fixes | `release/vX.Y.Z` |
| **release** | `release/vX.Y.Z` | Collect features for a version | `main` |
| **hotfix** | `hotfix/<name>` | Urgent production fixes | `main` + `release/*` |

## Release Flow

```
feature/search-sharepoint ──┐
feature/sharing-links ───────┤
feature/list-items ──────────┼──▶ release/v1.1.0 ──▶ tag v1.1.0-rc (UAT) ──▶ tag v1.1.0 (prod) ──▶ merge to main
bugfix/fix-tree-depth ───────┘
```

### Step-by-Step

1. **Create feature branch** from `main`:
   ```bash
   git checkout main && git pull
   git checkout -b feature/search-sharepoint
   ```

2. **Develop and commit** on the feature branch:
   ```bash
   git add . && git commit -m "feat: add Search_SharePoint tool"
   git push origin feature/search-sharepoint
   ```

3. **Create release branch** (once, when starting a release cycle):
   ```bash
   git checkout main && git pull
   git checkout -b release/v1.1.0
   git push origin release/v1.1.0
   ```

4. **Merge features into release** via PR or locally:
   ```bash
   git checkout release/v1.1.0
   git merge feature/search-sharepoint
   git push origin release/v1.1.0
   ```

5. **Tag RC for UAT** when release branch is ready for testing:
   ```bash
   git checkout release/v1.1.0
   git tag v1.1.0-rc
   git push origin v1.1.0-rc
   ```

6. **Tag production release** when UAT passes:
   ```bash
   git checkout release/v1.1.0
   git tag v1.1.0
   git push origin v1.1.0
   ```

7. **Merge release into main**:
   ```bash
   git checkout main
   git merge release/v1.1.0
   git push origin main
   ```

### Hotfix Flow

For urgent production bugs:

```bash
git checkout main && git pull
git checkout -b hotfix/fix-critical-auth
# fix the bug, commit
git checkout main && git merge hotfix/fix-critical-auth
git tag v1.0.1
git push origin main v1.0.1
```

## Naming Conventions

- **feature/**: `feature/search-sharepoint`, `feature/sharing-links`
- **bugfix/**: `bugfix/fix-tree-depth`, `bugfix/fix-upload-encoding`
- **hotfix/**: `hotfix/fix-critical-auth`, `hotfix/fix-crash-on-large-file`
- **release/**: `release/v1.1.0`, `release/v2.0.0`
- **Tags (RC)**: `v1.1.0-rc`, `v1.1.0-rc2`
- **Tags (Prod)**: `v1.0.0`, `v1.1.0`, `v2.0.0`
