# Auspex Scan

Auspex Scan is a Warhammer 40,000 11th-edition matchup calculator proof of
concept. It combines a FastAPI REST API, a local SQLite profile database, and a
lightweight web interface for comparing stored weapons against stored units.

## Current capabilities

- Store homogeneous unit profiles in SQLite.
- Attach fixed ranged and melee weapon profiles to units.
- Create, read, update, and soft delete units and weapons through the API.
- Prevent duplicate unit and weapon identities.
- Calculate one or more identical weapons into a selected defending unit.
- Apply normal hit, wound, armour-save, invulnerable-save, and fixed-damage
  rules.
- Report expected hits, wounds, unsaved attacks, damage, and models destroyed.
- Account for fixed-damage overkill being lost between identical models.
- Explore matchups through a responsive single-page web interface.

The current POC does not support rerolls, keywords, hit or wound modifiers,
Feel No Pain, variable attacks or damage, mortal wounds, mixed defensive
profiles, attached leaders, or weapon abilities.

## Run locally

From PowerShell in the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

Keep the terminal open while using the application.

## Local pages

- [Matchup calculator](http://127.0.0.1:8000/)
- [Swagger UI](http://127.0.0.1:8000/docs)
- [ReDoc](http://127.0.0.1:8000/redoc)
- [OpenAPI schema](http://127.0.0.1:8000/openapi.json)
- [Health check](http://127.0.0.1:8000/health)

These links work while the local API is running.

## Typical workflow

1. Open Swagger UI at `http://127.0.0.1:8000/docs`.
2. Create an attacking unit with `POST /v1/units`.
3. Create a defending unit with `POST /v1/units`.
4. Attach a weapon with `POST /v1/units/{unit_id}/weapons`.
5. Open the matchup calculator at `http://127.0.0.1:8000/`.
6. Select the weapon, target, weapon count, and target model count.

The page recalculates automatically when a selection changes.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Confirm the API is responding |
| `POST` | `/v1/units` | Create a unit |
| `GET` | `/v1/units` | List units |
| `GET` | `/v1/units/{unit_id}` | Get one unit |
| `PATCH` | `/v1/units/{unit_id}` | Update a unit |
| `DELETE` | `/v1/units/{unit_id}` | Deactivate a unit |
| `POST` | `/v1/units/{unit_id}/weapons` | Create a weapon profile |
| `GET` | `/v1/units/{unit_id}/weapons` | List a unit's weapons |
| `GET` | `/v1/units/{unit_id}/weapons/{weapon_id}` | Get one weapon |
| `PATCH` | `/v1/units/{unit_id}/weapons/{weapon_id}` | Update a weapon |
| `DELETE` | `/v1/units/{unit_id}/weapons/{weapon_id}` | Deactivate a weapon |
| `POST` | `/v1/calculations/expected-damage` | Calculate stored profiles |
| `POST` | `/v1/expected-damage` | Calculate inline profiles |

Soft-deleted records are excluded from list endpoints by default. Add
`?include_inactive=true` to include them.

## Stored calculation example

After creating units and a weapon profile, submit their returned identifiers:

```json
{
  "weapon_profile_id": 1,
  "defender_unit_id": 2,
  "weapon_count": 5,
  "defender_model_count": 10
}
```

Send the request to:

```text
POST /v1/calculations/expected-damage
```

For five A2, BS 3+, S4, AP -1, D1 weapons into ten T4, Sv 3+, W1 models,
an abridged response would be:

```json
{
  "attacking_unit": {
    "id": 1,
    "name": "Intercessor Squad"
  },
  "weapon": {
    "id": 1,
    "name": "Bolt rifle",
    "profile_name": "default"
  },
  "defender": {
    "id": 2,
    "name": "Example Target"
  },
  "weapon_count": 5,
  "defender_model_count": 10,
  "result": {
    "expected_hits": 6.6667,
    "expected_wounds": 3.3333,
    "expected_unsaved_attacks": 1.6667,
    "expected_damage": 1.6667,
    "expected_models_destroyed": 1.6667
  }
}
```

Swagger UI shows the complete response schema, probability stages, validation
rules, and editable request examples.

## Local database

Application data is stored in:

```text
auspex_scan.db
```

The SQLite file is created automatically in the directory where the API starts
and is excluded from Git. Unit identity is the case-insensitive combination of
faction, name, and edition. Weapon identity is the case-insensitive combination
of owning unit, weapon name, profile name, and weapon type.

Database writes should be performed through the API so Pydantic and database
constraints remain enforced.

## Tests

Run the complete test suite with:

```powershell
python -m pytest -q
```

Tests use a separate in-memory SQLite database and do not modify local profile
data.

## Project structure

```text
app/
├── calculator.py             # Core expected-damage calculations
├── database.py               # SQLite engine and sessions
├── db_models.py              # SQLAlchemy database models
├── main.py                   # FastAPI application
├── routers/                  # Unit, weapon, and calculation endpoints
├── rules/                    # Centralized game constraints
├── static/                   # Single-page web interface
├── unit_schemas.py           # Unit request and response validation
└── weapon_schemas.py         # Weapon request and response validation
```

## Development conventions

Python code follows PEP 8 for style, PEP 20 for design, and PEP 257 for
docstrings. Comments explain non-obvious reasoning rather than restating code.
FastAPI endpoint metadata, docstrings, and Pydantic field descriptions generate
the interactive API documentation.
