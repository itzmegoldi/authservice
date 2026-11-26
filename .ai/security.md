# Security Requirements

Authentication code is security-critical. Prefer explicit rejection and
fail-closed behavior whenever a security decision cannot be made safely.

## Secrets and sensitive data

- Never commit or print passwords, JWTs, refresh tokens, OAuth codes, private
  keys, database credentials, or production configuration.
- Read secrets from the configured environment/secret mechanism. Do not add
  fallback production credentials or hard-code signing material.
- Redact sensitive fields in structured logs, exceptions, debug output, and
  test failure messages.
- Use constant-time comparisons for secrets or security tokens where relevant.

## Authentication and authorization

- Verify JWT signature, algorithm, issuer, expiration, not-before, and
  required claims before trusting any claim. This service currently issues
  RS256 tokens with an issuer and no audience claim; if an audience is added,
  validate it on every consuming path.
- Validate refresh-token rotation/revocation and bind tokens to the intended
  realm/client/user according to the existing contract.
- Enforce authorization on every protected operation, including worker or
  internal paths that can be invoked without a browser.
- Default to deny when a role, policy, tenant/realm, or resource is missing.
- Do not use client-controlled context as proof of permission.

## HTTP and data handling

- Validate all external input with Pydantic and impose sensible length,
  format, and pagination limits.
- Prevent SQL injection by using parameterized ORM/query APIs; never build SQL
  from request strings.
- Avoid account-enumeration leaks in login, registration, and recovery flows.
- Keep CORS origins explicit. The current local origins are development-only;
  production origins must be configuration-driven and reviewed. Set secure
  cookie flags, transport security, and rate limiting for the deployment
  environment.
- Return generic public errors and log detailed diagnostic context only in a
  controlled, redacted form.

## Changes and review

For every security-sensitive change, add tests for invalid tokens, missing
claims, wrong realm/client, insufficient permissions, expired credentials,
and malformed input as applicable. Review dependency and migration changes
for secret exposure and privilege escalation. Security fixes should be
documented without publishing exploit details or credentials.
