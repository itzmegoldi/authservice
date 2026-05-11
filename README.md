# Auth Service

Keycloak-inspired authentication service scaffolded with FastAPI, Alembic, SQLite, Kafka, Redis, and a small local frontend.

## Stack

- FastAPI for local login, registration, JWT issuing, JWT verification, JWKS, RBAC, and ABAC policy checks.
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
curl -s http://localhost:8080/api/v1/auth/.well-known/jwks.json
```

```bash
curl -s -X POST http://localhost:8080/api/v1/authorize \
  -H 'content-type: application/json' \
  -H "authorization: Bearer $TOKEN" \
  -d '{"realm":"master","resource":"integration","action":"verify","context":{}}'
```

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
