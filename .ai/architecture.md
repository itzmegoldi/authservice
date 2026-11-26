# Architecture and Module Boundaries

## Application composition

FastAPI starts through `src/api/main.py`. Its lifespan function calls
`src.builder.helper.fetch_config_and_build_services()`, which loads the
environment-specific YAML file from `config/`, builds database/JWT/Google
clients and repositories, builds services, then registers those bundles in
`src.builder`. Routes resolve services through FastAPI dependencies that read
that registry.

Keep this lifecycle intact. New dependencies should be added to the relevant
builder and injected into the service that owns the use case. Do not load
configuration, build database handlers, or instantiate clients in a route.

## Dependency direction

The preferred dependency direction is:

```text
API -> services -> repositories / clients -> models and pkg infrastructure
```

`src/dto` is shared at transport/service boundaries and must not import API
routes. Composition in `src/builder` is the deliberate exception that wires
concrete implementations together. A lower-level module must not import an
API route to call upward into a higher layer.

## Responsibilities

- `src/api`: FastAPI app setup, middleware registration, route grouping, HTTP
  status codes, authentication dependencies, and request/response mapping.
  Current versioned routes are mounted at `/v1/api`.
- `src/services`: business use cases, transaction orchestration, policy
  decisions, and coordination of repositories/clients.
- `src/repositories`: database queries and persistence mapping. Repositories
  do not decide authorization policy or format HTTP responses.
- `src/clients`: external protocols such as Google OAuth, JWT/JWKS, and
  Redis. Encapsulate provider-specific behavior and normalize errors.
- `src/models`: database/domain persistence models and relationships.
- `src/dto`: validated transport schemas. Do not return ORM objects directly.
- `src/worker`: reserved for background entry points. It is currently a
  no-op scaffold; when implementing background processing, keep
  deserialization, retry, and error handling there and delegate business
  logic to services.
- `src/pkg`: reusable infrastructure and cross-cutting concerns. Avoid
  turning it into an unowned miscellaneous package.
- `alembic`: versioned schema migrations only.

## Boundaries and transactions

Keep database session/transaction ownership explicit. The current repository
pattern acquires a synchronous SQLAlchemy session from `IHandler` with a
context manager and commits within each mutating repository method. Preserve
that convention for focused changes. If a use case needs an atomic operation
across repositories, introduce an explicit unit-of-work refactor rather than
silently nesting independent repository commits. Ensure future worker retries
are safe and operations are idempotent where duplicate delivery is possible.

Cross-module changes should preserve interfaces where possible. If a boundary
must change, update all callers, tests, API documentation, and migration or
deployment assumptions in the same change.

## Adding modules

Before adding a new layer, check whether an existing service, repository,
client, or builder already owns the responsibility. New external integrations
belong in `src/clients`; new persistence access belongs in
`src/repositories`; new business workflows belong in `src/services`. Add
database schema models to `src/models/user.py` until the model area is split;
update Alembic metadata imports if creating a new model module.
