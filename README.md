# Habit Tracker — Assignment 2

This repository evolves the Assignment 1 habit tracker into two services:

- `services/habits/` owns habit lifecycle data.
- `services/completions/` owns completion history and streak data.

The original Assignment 1 application, root Dockerfile, root dependency manifest, and
Assignment 1 contract checker have been removed because they are replaced by the per-service
structure required for Assignment 2. The Assignment 1 decisions and AI disclosure remain in
[ADR.md](ADR.md) and [AI_USAGE.md](AI_USAGE.md).

## Services

Each service contains:

- `app.py` with domain routes and a database-aware health endpoint;
- a pinned `requirements.txt`;
- a dedicated non-root `Dockerfile`;
- versioned SQL migrations;
- focused service tests.

## Run the local system

Start the habits service, completions service, and static UI together:

```bash
cp .env.example .env
docker compose up --build
```

Local endpoints:

| Component | URL |
|---|---|
| Static UI | http://localhost:8080 |
| Habits service | http://localhost:8001 |
| Completions service | http://localhost:8002 |

The UI calls both services through the browser. The completions service also calls the habits
service over the Compose network using `HABITS_URL=http://habits:8000`.

The stack includes one SQL Server container holding separate `habits_db` and
`completions_db` databases. Habits and completions use separate database logins. SQL Server data
is kept in the `sqlserver-data` named volume, so it survives container recreation.

## Database migrations

Each service applies numbered migrations from its own `migrations/` directory at startup.
Applied migrations are recorded in `schema_migrations`, so repeated boots apply nothing twice.

The habits database includes:

- `001_init.sql`: creates the habits table.
- `002_add_due_date.sql`: adds a due-date column to a table that may already contain data.

The completions database includes:

- `001_init.sql`: creates the completions table.
- `002_add_source.sql`: adds a source column to existing completion records.

Stop the stack without deleting data:

```bash
docker compose down
```

Run a service locally from its directory:

```bash
cd services/habits
python -m pip install -r requirements.txt
PYTHONPATH=. python app.py
```

Run its tests:

```bash
cd services/habits
PYTHONPATH=. pytest -q
```

Use the equivalent commands with `services/completions/`.

## Tests and coverage

Install the development dependencies for a service:

```bash
python -m pip install -r services/habits/requirements-dev.txt
python -m pip install -r services/completions/requirements-dev.txt
```

Run each service suite with coverage:

```bash
cd services/habits
PYTHONPATH=. pytest -q --cov=app --cov-report=term-missing

cd ../completions
PYTHONPATH=. pytest -q --cov=app --cov-report=term-missing
```

Run the cross-seam integration stub from the repository root:

```bash
PYTHONPATH=services/habits:services/completions pytest -q tests/test_cross_seam.py
```

## Request logging

Both services write one stdout line for every HTTP request:

```text
method=POST path=/habits status=201 duration_ms=1.23
```

No database credentials or request payloads are included in these log lines.

## System and API documentation

The repository includes machine-readable system and API descriptions:

- `services/habits/openapi.yaml`
- `services/completions/openapi.yaml`
- `system.schema.json`
- `system.yaml`

Validate them locally:

```bash
python -m pip install -r requirements-ci.txt
python scripts/validate_documents.py
```

## Continuous integration

The reusable `.github/workflows/ci.yml` workflow runs on pushes to non-main branches,
pull requests, and calls from the main-branch deployment workflow:

- validates `system.yaml` and both OpenAPI documents;
- lints and tests each service;
- fails below 70% core coverage;
- runs the cross-seam integration test;
- builds both Docker images.

The `.github/workflows/deploy.yml` workflow calls CI on pushes to `main`. It publishes both
images to GHCR with the commit SHA tag and `provenance: false`. Pull requests and other branch
pushes build but do not publish images.

## Azure setup and deployment

This project follows the individual Azure for Students setup in the course guide. The existing
resource group is `rg-gmahler-ieu2024` in `spaincentral`; **do not create or replace it**. The
current subscription policy allows `spaincentral`, `francecentral`, `uksouth`, `norwayeast`,
and `swedencentral`. The Container Apps environment, Log Analytics workspace, and UI Storage
account use the resource-group region. Azure SQL uses `francecentral`, because the guide says
the SQL free offer isn't available in `spaincentral`. Before deployment, confirm in Azure that
the SQL free offer is available in the selected region; if it isn't, stop and choose another
allowed region rather than switching to a billable tier:

```bash
az account set --subscription <Azure-for-Students-subscription-id>
az group show --name rg-gmahler-ieu2024 --query '{name:name,location:location}' -o table
```

The SQL template configures both service databases for the [Azure SQL free tier](https://learn.microsoft.com/en-us/azure/azure-sql/database/free-tier?view=azuresql)
and `AutoPause` when monthly free limits are reached. The current offer permits up to ten free
General Purpose databases per subscription; it is not the unsupported Azure for Students
Starter offer. Supporting resources such as Container Apps and Log Analytics can still use
Azure for Students credits. Review usage and costs in the portal.

### One-time Azure and GitHub setup

1. Sign in with the Azure for Students account, select that subscription, and verify that the
   existing resource group is visible. Register the providers used by this deployment:

   ```bash
   for provider in Microsoft.App Microsoft.OperationalInsights Microsoft.Sql Microsoft.Storage Microsoft.ManagedIdentity; do
     az provider register --namespace "$provider" --wait
   done
   ```
2. Preview and create the GitHub Actions user-assigned managed identity. It is named
   `gmahler-ieu2024-github`, has Contributor and Storage Blob Data Contributor access scoped
   to this resource group, and trusts the `main` branch through both the readable and immutable
   GitHub OIDC subject formats:

   ```bash
   az deployment group what-if \
     --resource-group rg-gmahler-ieu2024 \
     --template-file infra/identity.bicep \
     --parameters \
       prefix=gmahler-ieu2024 \
       repoOwner=flipman62 \
       repoName=sdd-assignment-2 \
       repoOwnerId=182077556 \
       repoId=1454105521

   az deployment group create \
     --resource-group rg-gmahler-ieu2024 \
     --template-file infra/identity.bicep \
     --parameters \
       prefix=gmahler-ieu2024 \
       repoOwner=flipman62 \
       repoName=sdd-assignment-2 \
       repoOwnerId=182077556 \
       repoId=1454105521 \
     --query properties.outputs -o json
   ```

3. Add these repository Actions variables:

   | Variable | Value |
   |---|---|
   | `PREFIX` | `gmahler-ieu2024` |
   | `RESOURCE_GROUP` | `rg-gmahler-ieu2024` |
   | `UI_STORAGE` | `gmahlerieu2024ui` |
   | `SQL_LOCATION` | `francecentral` |

   `gmahlerieu2024ui` was available when checked; Storage account names are globally unique,
   so recheck availability if it is taken before deployment.
4. Add these repository Actions secrets. Obtain the identity client ID from the deployment
   output, and the tenant and subscription IDs from `az account show`. Generate strong,
   unique SQL passwords and store them only in GitHub:

   | Secret | Purpose |
   |---|---|
   | `AZURE_CLIENT_ID` | Client ID output by `infra/identity.bicep` |
   | `AZURE_TENANT_ID` | Tenant ID of the Azure for Students subscription |
   | `AZURE_SUBSCRIPTION_ID` | Azure for Students subscription ID |
   | `SQL_ADMIN_PASSWORD` | SQL Server administrator password |
   | `HABITS_DB_PASSWORD` | Contained user password for the habits database |
   | `COMPLETIONS_DB_PASSWORD` | Contained user password for the completions database |

   No client secret, Static Web Apps token, or GHCR pull token is used. Azure login uses GitHub
   OIDC; the Container Apps pull public GHCR images, and the workflow uploads the UI using
   Azure RBAC. The SQL passwords are URL-encoded for the application connection strings and
   escaped before they are used in SQL.

### First image publish and deployment

The first push to `main` runs CI and publishes both SHA-tagged GHCR packages. Azure deployment
is intentionally gated until their visibility and credentials are configured:

1. Merge the CI/deployment change through a pull request. Confirm the main-branch CI run is
   green and both service packages exist in GHCR.
2. Set both GHCR packages to **Public** in GitHub Packages.
3. Set the repository Actions variable `AZURE_DEPLOY_ENABLED` to `true`, then rerun the
   successful main-branch workflow from GitHub Actions. The deployment job uses OIDC, previews
   each Bicep deployment with `what-if`, creates SQL users, provisions the UI Storage static
   website and both Container Apps, uploads `ui/config.js` and the UI, and checks both service
   `/health` endpoints.
4. After deployment succeeds, copy the static website endpoint from the workflow summary into
   `public_url` in `system.yaml` and the live URL below.

The workflow temporarily adds the GitHub runner's current IP to the SQL firewall only while it
creates the contained database users, then removes that rule. The deployment never creates or
modifies a resource group.

Live URL: **pending first successful Azure deployment**.

If `az login` or deployment fails, first check `az account show` and verify the selected
subscription ID and tenant. If Azure reports `ResourceGroupNotFound`, verify that the selected
subscription contains `rg-gmahler-ieu2024`; do not create a replacement group.

## Image publishing

The `images` job in `.github/workflows/ci.yml` builds both service images on every push and pull
request. On pushes to `main`, it also publishes them to GHCR using the commit SHA as the image
tag. Pull requests and pushes to other branches build the images without publishing them.
