# Instructions for AI Coding Agents

## Scope

This file applies to the `auth-backend` service. Read the relevant files in
`.ai/` before changing code, and follow the narrower rule when local guidance
and a general rule differ.

## Service context

- Python 3.12+ service using FastAPI, Pydantic, SQLAlchemy, Alembic, JWT, and
  `structlog`. PostgreSQL is the configured persistence backend.
- `src/api` contains HTTP application and versioned routes.
- `src/services` contains use-case orchestration; `src/repositories` owns
  persistence; `src/clients` integrates with external systems; `src/models`
  contains persistence/domain models; `src/dto` contains request/response
  schemas; `src/worker` is reserved for background entry points.
- `src/builder` assembles dependencies and stores the configured service and
  client bundles for the process. Application startup calls
  `fetch_config_and_build_services()` before request handling; keep
  composition there rather than hiding it in route handlers.
- `src/pkg` contains cross-cutting concerns such as configuration, logging,
  middleware, security, and database access.
- Redis configuration is defined in `src/config/config.py`. Keep Redis access
  behind a client or infrastructure boundary rather than introducing it into
  route handlers or services directly.

## Before editing

1. Inspect the relevant route, service, repository, DTO/model, and client.
2. Check `git status --short`; preserve unrelated user changes.
3. Search for existing patterns before introducing a new abstraction.
4. Identify security, migration, API compatibility, and worker implications.

## Implementation rules

- Keep route handlers thin: validate input, authorize, call a service, and
  translate the result to the API contract.
- Do not let repositories contain business policy or let clients leak into
  routes.
- Use the existing builders and FastAPI dependencies. The current application
  resolves services through the builder registry after startup; do not create
  a second configuration or service lifecycle in a route handler.
- Never log passwords, access/refresh tokens, private keys, authorization
  headers, or complete OAuth responses.
- Treat authentication and authorization changes as security-sensitive and
  add tests for denial paths as well as success paths.
- Add or update Alembic migrations for schema changes; do not edit an applied
  migration.
- Keep public API behavior backward-compatible unless the change explicitly
  requires a versioned contract change.
- Prefer small, focused changes. Do not reformat unrelated files.

## Verification

At minimum, run the most focused available checks, then broaden them when the
change warrants it. The repository does not yet define a test runner or
formatter, so do not claim these checks exist without adding their tooling.
Always available source validation includes:

```bash
python -m compileall src
```

For migrations, use `alembic upgrade head` against a disposable PostgreSQL
database with the required `DATABASE_*` environment variables. When a test
suite is introduced, run its focused tests and the full suite. For API
changes, also verify the application imports and exercise the changed route.

Report what was changed, what was verified, and any checks that could not be
run. Do not claim a check passed unless it was actually run.

## Change hygiene

- Use imperative, focused commit messages; follow `.ai/git-workflow.md`.
- Do not commit secrets, local `.env` files, generated databases, virtual
  environments, or build artifacts.
- Do not make destructive repository or database changes without explicit
  approval.
