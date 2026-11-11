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

Use the equivalent commands with `services/completions/`. Compose, SQL Server migrations,
the static UI, service-to-service calls, and CI/CD are planned next.
