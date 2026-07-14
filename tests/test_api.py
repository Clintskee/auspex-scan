import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_home_page() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Auspex Scan" in response.text


def test_expected_damage_endpoint() -> None:
    response = client.post(
        "/v1/expected-damage",
        json={
            "weapon": {
                "name": "Example gun",
                "attacks": 6,
                "skill": 3,
                "strength": 5,
                "armour_penetration": -1,
                "damage": 2,
            },
            "defender": {
                "name": "Example target",
                "toughness": 4,
                "save": 3,
                "wounds": 2,
                "model_count": 5,
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["expected_damage"] == pytest.approx(8 / 3)


def test_invalid_profile_returns_422() -> None:
    response = client.post(
        "/v1/expected-damage",
        json={
            "weapon": {"attacks": 0, "skill": 3, "strength": 5, "damage": 2},
            "defender": {
                "toughness": 4,
                "save": 3,
                "wounds": 2,
                "model_count": 5,
            },
        },
    )

    assert response.status_code == 422


def test_unit_cannot_exceed_maximum_size() -> None:
    response = client.post(
        "/v1/expected-damage",
        json={
            "weapon": {
                "attacks": 1,
                "skill": 3,
                "strength": 4,
                "damage": 1,
            },
            "defender": {
                "toughness": 4,
                "save": 3,
                "wounds": 1,
                "model_count": 21,
            },
        },
    )

    assert response.status_code == 422
