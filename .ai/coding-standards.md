# Coding Standards

## General principles

Write code that is correct, explicit, easy to review, and easy to remove.
Prefer the simplest design that satisfies the requirement. Follow PEP 8 and
use the repository's existing formatting and naming patterns consistently.

## Naming and structure

- Use `snake_case` for modules, functions, methods, and variables; `PascalCase`
  for classes and Pydantic models; `UPPER_SNAKE_CASE` for constants.
- Name functions after actions and classes after responsibilities. Avoid
  vague names such as `helper`, `manager`, `data`, or `process` when a precise
  name is possible.
- Keep one primary responsibility per module and class.
- Use type annotations for public functions, service boundaries, and complex
  values. Prefer concrete types and narrow unions over `Any`.
- Use Pydantic models for external input/output and explicit domain types for
  internal boundaries.

## Readability and errors

- Prefer guard clauses and shallow control flow.
- Make side effects visible from function names and call sites.
- Do not silently swallow exceptions. Catch only what can be handled, add
  useful context, and preserve the original cause with exception chaining.
- Convert internal exceptions to stable API errors at the API boundary; do not
  expose stack traces, SQL, tokens, or provider details to clients.
- Use structured logging and stable event names. Never use `print` in service
  code.

## SOLID and clean code

- Single Responsibility: separate transport, business policy, persistence,
  and external integration.
- Open/Closed: add a client or strategy behind an existing interface where
  variation is expected; avoid speculative abstractions.
- Liskov Substitution: implementations of a client/repository interface must
  preserve its documented behavior and error semantics.
- Interface Segregation: keep interfaces narrow and use-case-oriented.
- Dependency Inversion: services depend on interfaces or injected factories,
  not on concrete Redis, database, or OAuth setup.

Avoid premature abstractions, deeply generic utilities, and unnecessary
indirection. Refactor only as part of a clearly scoped change.

## Configuration and dependencies

Load configuration through the existing configuration layer. Do not read
environment variables throughout business code. Pin or update dependencies in
the project manifest deliberately and document security or compatibility
impact.
