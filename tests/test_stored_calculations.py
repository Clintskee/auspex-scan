import pytest
from tests.api_client import JsonAPIClient

client = JsonAPIClient()


def create_unit(name: str, invulnerable_save: int | None = None) -> int:
    """Create a calculation test unit and return its identifier."""
    response = client.post(
        "/v1/units",
        json={
            "name": name,
            "faction": "Calculation Test Faction",
            "movement": 6,
            "toughness": 4,
            "save": 3,
            "invulnerable_save": invulnerable_save,
            "wounds": 2,
            "leadership": 6,
            "objective_control": 2,
            "minimum_model_count": 5,
            "maximum_model_count": 10,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_weapon(unit_id: int) -> int:
    """Create a calculation test weapon and return its identifier."""
    response = client.post(
        f"/v1/units/{unit_id}/weapons",
        json={
            "name": "Stored calculation weapon",
            "weapon_type": "ranged",
            "range_inches": 24,
            "attacks": 2,
            "skill": 3,
            "strength": 5,
            "armour_penetration": -4,
            "damage": 2,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_calculate_damage_with_stored_profiles() -> None:
    attacker_id = create_unit("Stored Calculation Attacker")
    defender_id = create_unit("Stored Calculation Defender", 4)
    weapon_id = create_weapon(attacker_id)

    response = client.post(
        "/v1/calculations/expected-damage",
        json={
            "weapon_profile_id": weapon_id,
            "defender_unit_id": defender_id,
            "weapon_count": 5,
            "defender_model_count": 10,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["attacking_unit"]["id"] == attacker_id
    assert body["weapon"]["id"] == weapon_id
    assert body["defender"]["id"] == defender_id
    assert body["result"]["expected_hits"] == pytest.approx(10 * (2 / 3))
    assert body["result"]["save_used"] == "invulnerable"


def test_stored_calculation_rejects_illegal_defender_size() -> None:
    attacker_id = create_unit("Defender Size Attacker")
    defender_id = create_unit("Defender Size Defender")
    weapon_id = create_weapon(attacker_id)

    response = client.post(
        "/v1/calculations/expected-damage",
        json={
            "weapon_profile_id": weapon_id,
            "defender_unit_id": defender_id,
            "weapon_count": 1,
            "defender_model_count": 4,
        },
    )

    assert response.status_code == 422


def test_stored_calculation_rejects_inactive_weapon() -> None:
    attacker_id = create_unit("Inactive Weapon Attacker")
    defender_id = create_unit("Inactive Weapon Defender")
    weapon_id = create_weapon(attacker_id)
    client.delete(f"/v1/units/{attacker_id}/weapons/{weapon_id}")

    response = client.post(
        "/v1/calculations/expected-damage",
        json={
            "weapon_profile_id": weapon_id,
            "defender_unit_id": defender_id,
            "weapon_count": 1,
            "defender_model_count": 5,
        },
    )

    assert response.status_code == 409
