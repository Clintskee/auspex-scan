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

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation.

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
