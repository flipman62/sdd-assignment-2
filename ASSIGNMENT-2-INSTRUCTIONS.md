# Individual Assignment 2

## Split, Ship and Operate Your Application: Services, Containers, CI/CD and Azure

The rules of Assignment 1 continue to apply. AI use is allowed and expected, but a passing
pipeline and a responding URL are not sufficient evidence of understanding. Decisions must be
defensible during the comprehension check.

No infrastructure is provided. Write the Dockerfiles, Compose file, pipeline, deployment, and
supporting configuration. Any line may be discussed during the comprehension check.

## Objective

Starting from the Assignment 1 monolith:

1. Split it into services along the Assignment 1 seam, with one service per feature domain,
   each with its own container and data.
2. Run the system locally with `docker compose up`.
3. Evolve the database using versioned, data-preserving migrations.
4. Test every push and deploy every merge to `main` automatically to Azure.
5. Serve the UI as a static site on Azure Static Web Apps, calling both services.
6. Make each service observable through its own health endpoint.

The repository and use case remain the same. No new features are required.

## 1. Scope and architecture constraints

### 1a. Hard requirements

- Exactly two service containers, one per feature domain. Each service is its own process, folder,
  Dockerfile, and container.
- The static UI lives in `ui/` and is deployed to one Azure Static Web App per student,
  `<prefix>-ui`. It calls both services over HTTPS. Service base URLs are deploy-time
  configuration, not hardcoded values.
- Each service restricts CORS to the UI origin.
- Locally, Compose serves the same UI files with a stock web-server image such as
  `nginx:alpine` and a mounted folder. The UI container is not a service container and must not
  have a custom Dockerfile.
- Each service owns its own serverless SQL database and login. A service must not connect to the
  other service's database; cross-domain data is obtained over HTTP.
- Services locate one another through environment variables such as
  `CATALOG_URL=http://catalog:8000`. Hostnames and ports must not be hardcoded.
- Azure uses Azure SQL Database serverless. Locally, one SQL Server container holds one database
  per service:
  `mcr.microsoft.com/mssql/server:2022-latest`.
- On Apple Silicon, enable Rosetta emulation in Docker Desktop for the SQL Server image.
- Each service reads its database connection string from `DATABASE_URL`.
- Local databases and logins are created by an idempotent `db/init.sql` run by a one-off Compose
  service. Azure logins are created during initial setup.
- Each service has its own dependency manifest under `services/<name>/`.
- Commit an OpenAPI document for each service and `system.yaml` at the repository root.
- Use your own Dockerfiles. They must not use `COPY . .`, include secrets or `.env` files, use
  pinned dependencies, and run as a non-root user.
- Provide a root `docker-compose.yml` that starts the whole system with
  `docker compose up --build` from a clean clone.
- Put CI/CD in `.github/workflows/`.
- Deploy services to Azure Container Apps on the Consumption plan, scaling to zero when idle.
- Do not commit secrets to source, workflows, Compose, or Git history. Handle any committed
  secret as an incident according to the CI/CD requirements below.

### 1b. Decisions to justify in `ADR.md`

- Where the cross-seam flow lives: server-side service call or UI calls both services. At least
  one user-visible flow must cross the seam server-side.
- What happens when the other service is unavailable: fail, degrade, cache, or retry.
- The migration approach: numbered SQL files with a custom runner or a migration tool.
- Infrastructure definition: Azure CLI in the workflow or Bicep/Terraform IaC.
- Registry choice: GHCR is the free default; Azure Container Registry has a fixed monthly cost
  and must be justified.
- Dependencies: keep to approximately 12 third-party packages or fewer per service.

### 1c. Out of scope

Do not use always-on compute, VMs, App Service plans, dedicated Container Apps workload
profiles, permanently running Container Instances, Kubernetes/AKS, message brokers, background
job runners, additional databases, service meshes, or a third container such as a frontend or
gateway. If something would benefit the design, document it as the deliberately unbuilt item in
ADR-10.

### 1d. Stack

Use the same language and stack as Assignment 1. Do not rewrite the services in a new language.

## 2. Changes from Assignment 1

- Tables move so each table belongs to exactly one service.
- A foreign key crossing the seam becomes a plain ID, with integrity enforced in code or
  deliberately not enforced.
- Server-rendered pages become static UI pages that fetch JSON from services.
- Joins become HTTP requests plus application code.
- Seed data moves with its owning table and remains idempotent.
- SQLite becomes SQL Server. Port raw SQL types and syntax, or use an ORM/provider for SQL
  Server.
- Moving the seam is allowed, but ADR-6 must explain why.

## 3. Required behaviour

- Both domains work end to end through the UI.
- At least one user-visible flow crosses the seam and requires data from the other service.
- When one service is stopped with `docker compose stop <service>`, the other still serves its
  own domain. Cross-seam behaviour must fail clearly, degrade, or use a documented cache; it
  must not expose a stack trace or hang.
- Every outbound service call has a timeout.
- Every service provides `GET /health` returning JSON:
  - HTTP 200, for example
    `{"status":"ok","db":"ok","version":"<git sha>"}`, when it can read and write its own DB.
  - HTTP 503 otherwise.
- Health reflects only the service's own state, not the other service.
- Logs go to stdout and include at least one line per request with method, path, status, and
  duration.

## 4. Database migrations

Assignment 1 created the schema on first boot. Assignment 2 must change an existing database in
place without recreating it.

1. Define the schema with committed, versioned migrations such as
   `migrations/001_init.sql` and `002_add_due_date.sql`.
2. Apply migrations automatically and in order at startup.
3. Record applied migrations in the database, and run each migration exactly once.
4. Include at least one migration that changes a table containing existing data, such as adding
   a column with a default or backfilling a value.
5. Forward-only migrations are acceptable. ADR-7 must state the production recovery plan for a
   bad migration.
6. Never edit an applied migration. Corrections go in a new migration.
7. Provide Azure evidence that data existed before the data-changing migration and remained
   afterwards. Include the deployment run, startup migration log, and before/after data.

Never drop tables on boot, recreate the database during deployment, or delete the volume to
redeploy.

## 5. CI/CD

Use one or more GitHub Actions workflows.

### CI on every push and pull request

- Install, lint, and test each service.
- Validate `system.yaml` against `system.schema.json`.
- Validate every OpenAPI document against the OpenAPI specification.
- Measure coverage per service and fail below 70% for either service's core logic.
- Build every Docker image; a failed build fails CI.
- Run tests against a SQL Server container or the Compose stack.
- Include at least one cross-seam integration test, using the Compose stack or a justified stub.
- CI must never connect to Azure SQL.

### CD on pushes to `main`

- Push every service image to a registry, tagged with the commit SHA, not only `latest`.
- Deploy those images to Azure only after CI passes on the same commit.
- Build the UI and deploy it to the Static Web App using a GitHub secret deployment token.
- Inject the deployed service URLs into UI configuration.
- Call each deployed `/health` endpoint and fail if it does not return 200 within the allowed
  time.

### Secrets and leaked credentials

Store the professor-provided service principal, service database passwords, and other secrets as
GitHub Actions secrets. Pass them to Container Apps as secrets, never plain environment
variables.

A secret is compromised as soon as it is pushed. Within 24 hours:

- Revoke or rotate credentials you created and update the replacement GitHub secret.
- Notify the professor if the leaked credential was the shared class service principal.
- Remove the secret from current code and record the incident in the README.

Rewriting history is optional after revocation. A final submission containing an unrevoked,
unreported leaked credential is capped at 40/100.

## 6. Process deliverables

### `ADR.md`

Keep entries 1-5 unchanged unless a decision changed; mark changed entries as superseded.
Add exactly five new entries, 6-10, in the same format:

6. The split: seam, crossing data, and whether ADR-2 held.
7. Data and migrations: data movement, lost cross-database integrity, compensation, and bad
   migration recovery.
8. Serverless Azure hosting: resources, cost model, scale-to-zero consequences, cold starts,
   paused database retries, startup migrations, single-replica rationale, and changes needed at
   100x traffic.
9. Pipeline and testing: CI gates, cross-seam test, and deliberate test omissions.
10. One deliberately unbuilt feature from the out-of-scope list and when it would be worthwhile.

Entries 6-10 must span at least three distinct commit dates.

### `AI_USAGE.md`

Use the same columns as Assignment 1. Include infrastructure files produced with AI, including
workflows, Dockerfiles, and IaC, and explain how each works in your own words.

### Commit history

Create at least 12 new commits after the Assignment 1 submission, across at least six calendar
days. No calendar day may contain more than 40% of the commits. Push the commits to GitHub.

## 7. Azure deployment contract

- Use the class's existing resource group: `rg-sdd-3a` or `rg-sdd-3b`.
- Do not create resource groups.
- Use the professor-provided class service principal only through GitHub Actions secrets.
- Create no more than two Container Apps, two serverless SQL databases, and one Static Web App.
- Prefix every resource with the student's username, replacing email dots with hyphens.
- Do not modify or delete another student's resources.

The deployed system must:

1. Use two Azure Container Apps on Consumption and one Static Web App. After initial setup,
   changes happen through the pipeline, not manually in the portal.
2. Give both services public HTTPS ingress for browser calls and restrict CORS to the UI origin.
3. Use one serverless Azure SQL Database per service on one logical server, with General Purpose,
   Gen5, 0.5-1 vCores, auto-pause, maximum 2 GB, locally redundant backups, and one login per
   service with access only to its own database.
4. Set each Container App to zero minimum replicas and one maximum replica.
5. Handle cold starts and SQL error 40613 using connection retries and backoff. Startup
   migrations must complete within the deployment health-check allowance.
6. Use only pay-per-use resources: Container Apps Consumption, serverless Azure SQL, Static Web
   Apps, and GHCR. Justify any fixed-cost resource in ADR-8.
7. Configure the system entirely through pipeline/IaC environment variables and secrets.
8. Keep the public system reachable until grades are published.

## 8. Documentation

### 8a. Machine-readable system description

Each `services/<name>/openapi.yaml` must be OpenAPI 3 and document every endpoint, including
`/health`, methods, parameters, request/response schemas, and status codes. Cross-service
endpoints must have matching shapes in both documents.

Commit `system.schema.json` and `system.yaml` at the root. Start `system.yaml` with:

```yaml
# yaml-language-server: $schema=./system.schema.json
```

`system.yaml` must describe the student, prefix, public URL, UI, Azure resources, every service,
its path, OpenAPI file, port, health endpoint, migrations, environment variables, cross-service
calls, timeouts, failure behaviour, Container App, and SQL database.

Every environment variable read by a service must be listed with its default. Secrets have no
default and use `secret: true`. CI validates this file and every OpenAPI document.

### 8b. Four-to-five-page report

Include:

- Before and after architecture diagrams showing the seam, HTTP calls, and service databases.
- A deployment diagram from GitHub and Actions through the registry to Azure.
- A database diagram for each service matching migrations.
- Azure migration evidence.
- Partial-failure evidence showing the user-visible result when the other service is down.
- A successful CD run link and a failed-then-fixed run link with the cause.
- README instructions for Compose, a single service, tests/coverage, deployment, initial Azure
  setup, and the live URL.
- The required syllabus AI-disclosure statement.

## 9. Version control and final submission

- Use the same individual Git repository as Assignment 1.
- Changes reach `main` through pull requests from branches so CI runs before CD.
- The graded version is the deployed commit tagged `submission` on `main`:

```bash
git tag submission <commit-sha>
git push origin submission
```

The submitted tag and commit SHA must match. If the tag is missing or differs from the submitted
SHA, the last commit on `main` before the deadline is graded. Commits after the tagged commit are
ignored.

## Immediate submission evidence for the image milestone

For the session **Building and Publishing Images in CI**, submit the URL of the commit on
`main` where:

1. The CI workflow has an `images` job that builds every service image on every push and pull
   request, and pushes images to GHCR only on `main`, tagged with the commit SHA.
2. The job was added through a pull request and merged when CI was green.
3. The CI run for that `main` commit is green, and every service has a GHCR package tagged with
   that commit SHA.

Open the commit on GitHub and copy the address-bar URL, in the form:

```text
https://github.com/<user>/<repo>/commit/<sha>
```
