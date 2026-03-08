# OPIntegration

Integration between **OpenProject**, **GitHub Actions**, and **GCP Cloud Run** (via Cloud Build).

## Architecture

- **OpenProject** — project management, task tracking (BI Feature / BI Task)
- **GitHub Actions** — CI (tests, OP status updates), triggers Cloud Build on merge
- **GCP Cloud Build** — Docker build, push to Artifact Registry, deploy to Cloud Run
- **OpenProject instance**: https://aidevs4seba2.openproject.com

## Branch Naming Convention

All automation depends on this naming pattern:

```
feature/OP-{ID}-short-name    # for BI Feature
task/OP-{ID}-short-name       # for BI Task
fix/OP-{ID}-short-name        # for bugs from CI
```

Examples:
```
feature/OP-42-user-authentication
task/OP-87-implement-oauth2
fix/OP-103-token-expiry-bug
```

Never commit directly to `main`. Always create a branch and PR.

## Commit Message Format

```
feat(OP-42): description of change
fix(OP-103): description of fix
task(OP-87): description of technical task
```

## Automation Flow

1. Developer creates branch with `OP-{ID}` → push triggers status **In Progress** in OpenProject
2. Tests run on push/PR → failing tests create **Bug** work packages in OpenProject
3. PR opened → status changes to **In Testing**
4. PR merged to main → status changes to **Tested** + Cloud Build deploys to Cloud Run
5. PR closed without merge → status changes to **Rejected**

## Documentation

Full configuration guide: [docs/OpenProject_GitHub_GCP_Config_Guide.md](docs/OpenProject_GitHub_GCP_Config_Guide.md)
