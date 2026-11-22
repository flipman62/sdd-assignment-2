# Habit Tracker — Assignment 2

This repository evolves the Assignment 1 habit tracker into two services:

- `services/habits/` owns habit lifecycle data.
- `services/completions/` owns completion history and streak data.

The original Assignment 1 application, root Dockerfile, root dependency manifest, and
Assignment 1 contract checker have been removed because they are replaced by the per-service
structure required for Assignment 2. The Assignment 1 decisions and AI disclosure remain in
[ADR.md](ADR.md) and [AI_USAGE.md](AI_USAGE.md).

## Current service scaffold

Each service currently contains:

- `app.py` with a health endpoint and initial domain route;
- a pinned `requirements.txt`;
- a dedicated non-root `Dockerfile`;
- a `migrations/` directory;
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

Use the equivalent commands with `services/completions/`. SQL Server migrations,
service testing, and Azure deployment are planned next.

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

## Initial image CI

The workflow in `.github/workflows/images.yml` builds both service images on every push and pull
request. On pushes to `main`, it also publishes them to GHCR using the commit SHA as the image
tag. Pull requests and pushes to other branches build the images without publishing them.
