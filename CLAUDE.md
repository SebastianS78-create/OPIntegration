# CLAUDE.md — OPintegration Project Rules

## Project Overview
Integration between OpenProject, GitHub Actions, and GCP Cloud Run (via Cloud Build).
- OpenProject instance: https://aidevs4seba2.openproject.com
- GitHub repo: SebastianS78-create/OPIntegration
- GCP Project: `opintegr`, Region: `europe-central2`
- Build: Cloud Build (NOT Docker in GitHub Actions — build happens in GCP)
- Documentation: `docs/OpenProject_GitHub_GCP_Config_Guide.md` (source of truth, updated from original .docx)

## OpenProject API IDs (aidevs4seba2 instance)

### Statuses
| ID | Name           | Automation trigger              |
|----|----------------|---------------------------------|
| 1  | New            | Bug creation from CI            |
| 7  | In progress    | First push on feature branch    |
| 9  | In testing     | PR opened (maps to "In Review") |
| 10 | Tested         | PR merged (maps to "Resolved")  |
| 14 | Rejected       | PR closed without merge         |

### Types
| ID | Name |
|----|------|
| 7  | Bug  |

### Priorities
| ID | Name |
|----|------|
| 9  | High |

## Git Conventions — CRITICAL
Always create branches following this pattern:
```
feature/OP-{ID}-short-name    # for BI Feature
task/OP-{ID}-short-name       # for BI Task
fix/OP-{ID}-short-name        # for bugs
```
Never commit directly to main.

## Commit Message Format
```
feat(OP-42): description of change
fix(OP-103): description of fix
task(OP-87): description of technical task
```

## Pull Request Description Template
Every PR must include:
```
## OP Work Package
Closes OP #<ID>

## What was done
...

## How to test
...
```

## OpenProject API Authentication
- Format: `Authorization: Basic base64(apikey:TOKEN)`
- Token stored as GitHub Secret: `OPENPROJECT_API_TOKEN`

## GitHub Actions Workflows
Three workflow files in `.github/workflows/`:
1. `op-status-update.yml` — auto-updates OP status + adds comment to Activity on push/PR events
2. `tests.yml` — runs tests, creates Bug WP + adds comment to parent WP on failure
3. `deploy.yml` — triggers Cloud Build on merge to main + adds deploy comment to OP

## OpenProject Comment API
Workflows write comments to WP Activity tab via:
- Endpoint: `POST /api/v3/work_packages/{id}/activities`
- Body: `{"comment": {"raw": "markdown text"}}`
- Supports markdown formatting and links

## OpenProject Prerequisites (discovered during testing)
- **Workflow transitions**: Must be configured in Administration > Workflows for each role/type
  - Required: New>In progress, In progress>In testing, In testing>Tested, In progress>Rejected, In testing>Rejected
- **Bug type**: Must be enabled per project in Project Settings > Types
- **API user role**: Must have Edit work packages permission in each project

## Key Files
- `docs/OpenProject_GitHub_GCP_Config_Guide.md` — full config guide with all details
- `docs/OpenProject_GitHub_GCP_Config_Guide.docx` — original document (read-only reference)
- `.github/workflows/` — GitHub Actions automation
- `.github/PULL_REQUEST_TEMPLATE.md` — PR template
- `cloudbuild.yaml` — Cloud Build pipeline (build, push to Artifact Registry, deploy to Cloud Run)
- `Dockerfile` — Python/FastAPI container for Cloud Run
- `app.py` — minimal FastAPI app (health check + monitoring endpoints)
- `README.md` — project overview with branch naming convention

## Rules for AI
- When user mentions OP number (e.g., OP-42), assume it refers to a BI Feature or BI Task in OpenProject
- Always use the correct status/type/priority IDs from the tables above
- Branch names must always include `OP-{ID}` for automation to work
- Do not modify files outside this project directory
