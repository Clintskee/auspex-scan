# 40K Expected Damage API

A small REST API proof of concept for calculating the average raw damage caused by
one Warhammer 40,000 11th-edition weapon profile against one defender profile.

The current version supports the normal hit, wound, armour-save, and fixed-damage
sequence. It intentionally does not support rerolls, keywords, modifiers,
invulnerable saves, Feel No Pain, variable characteristics, mortal wounds, or
mixed-profile units. Expected model destruction does account for fixed-damage
overkill being lost between otherwise identical models.

In 11th edition, save rolls are grouped by models sharing the same Wounds, Save,
and Invulnerable Save characteristics, with separate groups for Characters. This
POC uses one homogeneous defender profile, so that allocation sequence does not
change the raw expected-damage result yet.

Unit profiles can be stored in the local SQLite database through the `/v1/units`
CRUD endpoints. Deleting a unit is a soft delete that marks it inactive.
Unit identity is the case-insensitive combination of faction, name, and edition;
the API rejects duplicate active or inactive records with HTTP `409 Conflict`.
Fixed weapon profiles can be attached to units through nested CRUD endpoints at
`/v1/units/{unit_id}/weapons`. Weapon names, alternate profile names, and weapon
types form a case-insensitive identity within each unit.

Stored profiles can be calculated through
`POST /v1/calculations/expected-damage`. The request selects a weapon profile,
the number of identical weapons, a defending unit, and its model count. The
calculator automatically uses an invulnerable save when it is better than the
armour save after AP.

## Documentation conventions

Python code follows PEP 8 for style, PEP 20 for design, and PEP 257 for
docstrings. Comments explain non-obvious reasoning rather than restating code.
Public API behavior is documented through endpoint metadata, docstrings, and
Pydantic field descriptions rendered automatically in `/docs` and `/redoc`.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation.
Open `http://127.0.0.1:8000/` for the lightweight matchup calculator.

## Example request

```powershell
$body = @{
  weapon = @{
    name = "Example gun"
    attacks = 6
    skill = 3
    strength = 5
    armour_penetration = -1
    damage = 2
  }
  defender = @{
    name = "Example target"
    toughness = 4
    save = 3
    wounds = 2
    model_count = 5
  }
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/v1/expected-damage `
  -ContentType application/json `
  -Body $body
```

For this example, the expected damage is `2.6667` and the expected models
destroyed is `1.3332`: six attacks hit on 3+, wound on 3+, defeat a 4+ modified
save, and inflict two damage each against two-wound models.

## Test

```powershell
pytest
```
