# Auspex Scan

Auspex Scan is a Warhammer 40,000 11th-edition matchup calculator built with:

- Django and Django REST Framework
- drf-spectacular for OpenAPI, Swagger UI, and ReDoc
- Pydantic for calculation-domain validation
- PostgreSQL
- SvelteKit
- Gunicorn and WhiteNoise

The existing `/v1` contract and calculator behavior are preserved, including unit and weapon CRUD, soft deletion, and stored or inline calculations.

## Run with Docker Compose

```powershell
docker compose up --build
```

Open the app at http://127.0.0.1:8000/. API documentation is available at `/docs`, ReDoc at `/redoc`, the schema at `/openapi.json`, and health at `/health`.

The web container runs migrations before Gunicorn starts. PostgreSQL data persists in the `postgres_data` Docker volume.

## Local development

Start PostgreSQL, then configure the connection shown in `.env.example`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
$env:DATABASE_URL = "postgresql://auspex:auspex@localhost:5432/auspex_scan"
python manage.py migrate
python manage.py runserver
```

Run SvelteKit in a second terminal:

```powershell
cd frontend
pnpm install
pnpm dev
```

Vite proxies `/v1` and `/health` to Django on port 8000.

## Production build

```powershell
cd frontend
pnpm install
pnpm build
cd ..
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

Use Docker to run Gunicorn on Windows; Gunicorn targets Unix-like production environments.

## Verification

```powershell
python -m pytest -q
cd frontend
pnpm check
pnpm build
```

API tests use an isolated in-memory SQLite database for speed. Runtime configuration uses PostgreSQL through `DATABASE_URL`.

## Structure

```text
api/                 Django models, serializers, views, URLs, migrations
app/                 Pydantic models, rules, and calculator engine
config/              Django settings, URLs, and WSGI entry point
frontend/            SvelteKit client
tests/               Calculator and Django/DRF API tests
docker-compose.yml   PostgreSQL and production web service
Dockerfile           Svelte build and Django/Gunicorn runtime
```

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Service health |
| `POST/GET` | `/v1/units` | Create or list units |
| `GET/PATCH/DELETE` | `/v1/units/{id}` | Read, update, or deactivate a unit |
| `POST/GET` | `/v1/units/{id}/weapons` | Create or list weapons |
| `GET/PATCH/DELETE` | `/v1/units/{id}/weapons/{weapon_id}` | Manage a weapon |
| `POST` | `/v1/calculations/expected-damage` | Calculate stored profiles |
| `POST` | `/v1/expected-damage` | Calculate inline profiles |

Use `?include_inactive=true` on list endpoints to include soft-deleted records.
