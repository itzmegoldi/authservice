# Testing Standards

Tests should make behavior and security guarantees executable. The repository
does not currently contain a test suite or pytest configuration. Introduce
tests under `tests/` with their runner and fixtures declared in
`pyproject.toml`; new behavior should normally include tests in the same
change, and bug fixes should include a regression test where practical.

## Test layers

- **Unit tests:** test services, policy decisions, DTO validation, and client
  adapters with narrow fakes/mocks. Cover success, validation, exceptions,
  and boundary values.
- **Integration tests:** test repositories with a disposable database and
  API routes with the application wiring, authentication dependencies, and
  serialization. Include migration setup for schema-dependent tests.
- **Redis/integration tests:** test cache, lock, queue, or state behavior
  behind a Redis client boundary. Use fakes for unit tests and a disposable
  Redis instance for integration tests when needed.

Prefer behavior-focused tests over implementation details. Do not assert a
private helper's call sequence when the externally observable result is what
matters.

## Required coverage

At minimum, cover:

- authenticated and unauthenticated requests;
- valid, expired, malformed, and incorrectly scoped tokens;
- authorization denial for missing roles/policies and wrong realm/client;
- invalid request data and stable error responses;
- repository not-found, uniqueness, and transaction failure behavior;
- duplicate delivery, retry, or lock-expiry behavior for future background
  operations;
- migration upgrade behavior for schema changes.

Security-sensitive and authorization code requires both allow and deny-path
tests. Do not lower coverage thresholds or delete tests to make a change pass.

## Test quality

- Keep tests deterministic and isolated. Avoid depending on developer-local
  services, wall-clock timing, or shared mutable state.
- Use factories/fixtures for test data and ensure secrets are fake and scoped
  to tests.
- Assert meaningful status codes, response shapes, state transitions, and
  security properties.
- Run focused tests during development and the complete suite before merge.
- If a test cannot be run because infrastructure is unavailable, report that
  limitation explicitly.
