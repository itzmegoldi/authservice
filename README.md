# Auth Service

Keycloak-inspired authentication service scaffolded with FastAPI, Alembic, SQLite, Kafka, Redis, and a small local frontend.

## Stack

- FastAPI identity provider for JWT issuing, JWKS discovery, OAuth client
  authentication, RBAC claims, and rotating refresh-token sessions.
- Python worker that consumes integration verification jobs from Kafka.
- Alembic migrations with SQLite for the first persistence layer.
- Boilerplate-style YAML settings in `backend/config/default.yaml` plus `backend/config/{APP_ENV}.yaml`.
- Redis and Kafka on the same Docker Compose network.
- Static frontend console at `http://localhost:3000`.

## Run

```bash
docker compose up --build
```

API: `http://localhost:8080`

Frontend: `http://localhost:3000`

Default admin:

```text
realm: master
email: admin@example.com
password: ChangeMe123!
```

## Useful Endpoints

```bash
curl -s http://localhost:8080/actuator/health
```

```bash
curl -s -X POST http://localhost:8080/api/v1/auth/login \
  -H 'content-type: application/json' \
  -d '{"realm":"master","email":"admin@example.com","password":"ChangeMe123!"}'
```

```bash
curl -s http://localhost:8080/v1/api/.well-known/openid-configuration
```

```bash
curl -s http://localhost:8080/v1/api/oauth/jwks.json
```

## Integrating a service

Create a client in the administration console and enable only the grant types
that service needs. A backend that acts on behalf of a user exchanges the
user's credentials at the token endpoint; a machine-to-machine backend uses
the `client_credentials` grant:

```bash
curl -s -X POST http://localhost:8080/v1/api/oauth/token \
  -u "$CLIENT_ID:$CLIENT_SECRET" \
  -H 'content-type: application/x-www-form-urlencoded' \
  -d 'grant_type=client_credentials&realm=master'
```

Resource services should fetch the discovery document once, cache the JWKS by
`kid`, and verify every access token's RS256 signature, `iss`, `exp`, `typ`,
`realm`, and `aud`. For user tokens, authorize using
`resource_access[client_id].roles`; for service tokens, require `typ=client`
and allow only explicitly granted scopes. Never accept a token for another
client audience.

Set `AUTH_KEYS_SECRET` to the PEM-encoded RSA private key and
`AUTH_KEYS_PUBLIC` to its public key in the deployment secret store. These
keys are mandatory and must be identical on every API/worker replica.

## Notes

SQLite runs embedded inside the backend containers and is persisted through the `auth-db` Docker volume. API and worker are separate Compose services using the same backend image and shared network.

Backend source follows the `ms-boilerplate` layout:

```text
backend/src/api
backend/src/builder
backend/src/config
backend/src/pkg
backend/src/repositories
backend/src/services
backend/src/worker
```

## Local Backend Development

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8080
```

Set `APP_ENV` to choose the environment file. For example, `APP_ENV=local` loads `backend/config/default.yaml` and then overlays `backend/config/local.yaml`. Docker Compose uses `APP_ENV=docker`.
