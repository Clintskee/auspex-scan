from tests.api_client import JsonAPIClient

client = JsonAPIClient()

UNIT_PAYLOAD = {
    "name": "Intercessor Squad",
    "faction": "Adeptus Astartes",
    "movement": 6,
    "toughness": 4,
    "save": 3,
    "invulnerable_save": None,
    "wounds": 2,
    "leadership": 6,
    "objective_control": 2,
    "minimum_model_count": 5,
    "maximum_model_count": 10,
    "points": 80,
}


def test_unit_crud_lifecycle() -> None:
    create_response = client.post("/v1/units", json=UNIT_PAYLOAD)

    assert create_response.status_code == 201
    created_unit = create_response.json()
    unit_id = created_unit["id"]
    assert created_unit["edition"] == 11
    assert created_unit["is_active"] is True

    get_response = client.get(f"/v1/units/{unit_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Intercessor Squad"

    list_response = client.get("/v1/units")
    assert list_response.status_code == 200
    assert any(unit["id"] == unit_id for unit in list_response.json())

    update_response = client.patch(
        f"/v1/units/{unit_id}",
        json={"points": 90, "maximum_model_count": 20},
    )
    assert update_response.status_code == 200
    assert update_response.json()["points"] == 90
    assert update_response.json()["maximum_model_count"] == 20

    delete_response = client.delete(f"/v1/units/{unit_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["is_active"] is False

    active_units = client.get("/v1/units").json()
    assert all(unit["id"] != unit_id for unit in active_units)

    all_units = client.get(
        "/v1/units",
        params={"include_inactive": True},
    ).json()
    assert any(unit["id"] == unit_id for unit in all_units)


def test_create_rejects_reversed_model_count_range() -> None:
    payload = {
        **UNIT_PAYLOAD,
        "minimum_model_count": 10,
        "maximum_model_count": 5,
    }

    response = client.post("/v1/units", json=payload)

    assert response.status_code == 422


def test_patch_rejects_null_for_required_field() -> None:
    create_response = client.post(
        "/v1/units",
        json={**UNIT_PAYLOAD, "name": "Null Test Unit"},
    )
    unit_id = create_response.json()["id"]

    response = client.patch(
        f"/v1/units/{unit_id}",
        json={"toughness": None},
    )

    assert response.status_code == 422


def test_missing_unit_returns_404() -> None:
    response = client.get("/v1/units/999999")

    assert response.status_code == 404


def test_duplicate_unit_identity_returns_409() -> None:
    first_response = client.post(
        "/v1/units",
        json={**UNIT_PAYLOAD, "name": "Duplicate Test Unit"},
    )

    duplicate_response = client.post(
        "/v1/units",
        json={
            **UNIT_PAYLOAD,
            "name": "  duplicate test unit  ",
            "faction": "adeptus astartes",
        },
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert "already exists" in duplicate_response.json()["detail"]


def test_patch_cannot_duplicate_another_unit_identity() -> None:
    first_response = client.post(
        "/v1/units",
        json={**UNIT_PAYLOAD, "name": "First Identity"},
    )
    second_response = client.post(
        "/v1/units",
        json={**UNIT_PAYLOAD, "name": "Second Identity"},
    )
    first_id = first_response.json()["id"]

    response = client.patch(
        f"/v1/units/{first_id}",
        json={"name": second_response.json()["name"]},
    )

    assert response.status_code == 409
