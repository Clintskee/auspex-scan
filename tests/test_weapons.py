from tests.api_client import JsonAPIClient

client = JsonAPIClient()

UNIT_PAYLOAD = {
    "name": "Weapon Test Unit",
    "faction": "Test Faction",
    "movement": 6,
    "toughness": 4,
    "save": 3,
    "wounds": 2,
    "leadership": 6,
    "objective_control": 2,
    "minimum_model_count": 5,
    "maximum_model_count": 10,
}

WEAPON_PAYLOAD = {
    "name": "Bolt rifle",
    "profile_name": "default",
    "weapon_type": "ranged",
    "range_inches": 24,
    "attacks": 2,
    "skill": 3,
    "strength": 4,
    "armour_penetration": -1,
    "damage": 1,
}


def create_test_unit(name: str) -> int:
    """Create a unit and return its database identifier."""
    response = client.post(
        "/v1/units",
        json={**UNIT_PAYLOAD, "name": name},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_weapon_crud_lifecycle() -> None:
    unit_id = create_test_unit("Weapon CRUD Unit")
    endpoint = f"/v1/units/{unit_id}/weapons"

    create_response = client.post(endpoint, json=WEAPON_PAYLOAD)
    assert create_response.status_code == 201
    weapon = create_response.json()
    weapon_id = weapon["id"]
    assert weapon["unit_id"] == unit_id

    get_response = client.get(f"{endpoint}/{weapon_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Bolt rifle"

    list_response = client.get(endpoint)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client.patch(
        f"{endpoint}/{weapon_id}",
        json={"damage": 2, "profile_name": "heavy"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["damage"] == 2
    assert update_response.json()["profile_name"] == "heavy"

    delete_response = client.delete(f"{endpoint}/{weapon_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["is_active"] is False
    assert client.get(endpoint).json() == []

    all_weapons = client.get(
        endpoint,
        params={"include_inactive": True},
    ).json()
    assert len(all_weapons) == 1


def test_duplicate_weapon_identity_returns_409() -> None:
    unit_id = create_test_unit("Duplicate Weapon Unit")
    endpoint = f"/v1/units/{unit_id}/weapons"

    first_response = client.post(endpoint, json=WEAPON_PAYLOAD)
    duplicate_response = client.post(
        endpoint,
        json={
            **WEAPON_PAYLOAD,
            "name": "  bolt RIFLE  ",
            "profile_name": "DEFAULT",
        },
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409


def test_ranged_weapon_requires_range() -> None:
    unit_id = create_test_unit("Range Validation Unit")
    endpoint = f"/v1/units/{unit_id}/weapons"

    response = client.post(
        endpoint,
        json={**WEAPON_PAYLOAD, "range_inches": None},
    )

    assert response.status_code == 422


def test_melee_weapon_rejects_range() -> None:
    unit_id = create_test_unit("Melee Validation Unit")
    endpoint = f"/v1/units/{unit_id}/weapons"

    response = client.post(
        endpoint,
        json={
            **WEAPON_PAYLOAD,
            "weapon_type": "melee",
            "range_inches": 1,
        },
    )

    assert response.status_code == 422


def test_weapon_must_belong_to_requested_unit() -> None:
    first_unit_id = create_test_unit("First Weapon Owner")
    second_unit_id = create_test_unit("Second Weapon Owner")
    create_response = client.post(
        f"/v1/units/{first_unit_id}/weapons",
        json=WEAPON_PAYLOAD,
    )
    weapon_id = create_response.json()["id"]

    response = client.get(
        f"/v1/units/{second_unit_id}/weapons/{weapon_id}"
    )

    assert response.status_code == 404
