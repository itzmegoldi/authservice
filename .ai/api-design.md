# API Design and Versioning

## Resource and route design

- Keep externally visible routes under the established `/v1/api` prefix. A
  new breaking version should use a new, explicit prefix rather than changing
  the existing route contract.
- Use nouns for resources and HTTP methods for actions. Use an action route
  only when the operation is not naturally represented as resource state.
- Use consistent lowercase path segments, stable field names, and predictable
  pagination/filtering conventions.
- Keep request and response DTOs explicit. Never expose database models or
  provider-specific payloads directly.

## Contracts

- Validate request bodies, query parameters, and path parameters at the
  boundary.
- Return appropriate, stable HTTP status codes and a consistent error shape.
  Do not expose stack traces, SQL, secret material, or upstream internals.
- Document authentication, authorization, required claims, idempotency, and
  side effects for each protected or mutating endpoint. The authentication
  middleware currently protects every route other than its explicit public
  path allowlist; add public endpoints to that allowlist deliberately.
- Make create/update/delete semantics and nullability explicit. Avoid silently
  changing the meaning of an existing field.

## Compatibility and versioning

Treat response fields, required request fields, status codes, error codes, and
authentication behavior as public contracts. Prefer additive, backward-
compatible changes: optional response fields, new endpoints, or new optional
request fields with safe defaults. Do not rename/remove fields, change field
types, tighten validation, or change authorization behavior without assessing
clients and documenting the migration.

Use a new API version for an intentional breaking contract change. Keep old
versions stable during the supported deprecation window and state the
replacement and removal plan. Update frontend callers, README examples, and
tests when an API contract changes.

## Operational behavior

Mutating endpoints should be safe to retry where feasible. Use idempotency
keys or conflict semantics when duplicate requests could create credentials,
users, clients, or integrations. Set sensible request size, pagination, and
timeout limits. Preserve correlation/request identifiers in redacted logs.
