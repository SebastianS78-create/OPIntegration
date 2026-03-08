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

Each step auto-updates the OP work package status **and** writes a comment to the Activity tab:

1. Developer creates branch with `OP-{ID}` → push triggers status **In Progress** + commit info comment
2. Tests run on push/PR → failing tests create **Bug** WP + comment on parent WP with link
3. PR opened → status changes to **In Testing** + PR link comment
4. PR merged to main → status changes to **Tested** + merge comment + Cloud Build deploys to Cloud Run + deploy comment
5. PR closed without merge → status changes to **Rejected** + comment

## Prerequisites

Before the automation works for a project in OpenProject:

- **Workflow transitions** must be configured in Administration > Workflows:
  New > In progress > In testing > Tested, plus In progress/In testing > Rejected
- **Bug type** must be enabled in Project Settings > Types
- **API user** needs "Edit work packages" permission in each project

## Documentation

- Full configuration guide: [docs/OpenProject_GitHub_GCP_Config_Guide.md](docs/OpenProject_GitHub_GCP_Config_Guide.md)
- Daily workflow guide (PM, Developer, Tester): [docs/daily-workflow-guide.md](docs/daily-workflow-guide.md)
