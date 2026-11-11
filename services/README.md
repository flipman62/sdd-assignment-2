# Assignment 2 services

The application is being split along the Assignment 1 seam:

- `habits` owns habit lifecycle data.
- `completions` owns completion history and streak data.

Each service has its own dependency manifest, Dockerfile, tests, and migration directory.
The current endpoints are a runnable scaffold for the initial services commit. Database
connections, migrations, service-to-service calls, and the complete API contracts are added in
the next implementation phases.

Run either service from its directory:

```bash
PYTHONPATH=. python app.py
```

Run its tests from the service directory:

```bash
PYTHONPATH=. pytest -q
```
