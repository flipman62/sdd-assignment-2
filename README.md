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

The in-memory applications do not yet use SQL Server or migrations. Their data is reset whenever
the containers restart.

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

## Initial image CI

The workflow in `.github/workflows/images.yml` builds both service images on every push and pull
request. On pushes to `main`, it also publishes them to GHCR using the commit SHA as the image
tag. Pull requests and pushes to other branches build the images without publishing them.
