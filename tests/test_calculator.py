import pytest

from app.calculator import calculate_expected_damage, wound_roll_required
from app.models import DamageRequest


@pytest.mark.parametrize(
    ("strength", "toughness", "required"),
    [(8, 4, 2), (5, 4, 3), (4, 4, 4), (4, 5, 5), (4, 8, 6)],
)
def test_wound_roll_table(strength: int, toughness: int, required: int) -> None:
    assert wound_roll_required(strength, toughness) == required


def test_expected_damage() -> None:
    request = DamageRequest.model_validate(
        {
            "weapon": {
                "attacks": 6,
                "skill": 3,
                "strength": 5,
                "armour_penetration": -1,
                "damage": 2,
            },
            "defender": {"toughness": 4, "save": 3, "wounds": 2, "model_count": 5},
        }
    )

    result = calculate_expected_damage(request)

    assert result.expected_hits == pytest.approx(4)
    assert result.expected_wounds == pytest.approx(8 / 3)
    assert result.expected_unsaved_attacks == pytest.approx(4 / 3)
    assert result.expected_damage == pytest.approx(8 / 3)
    # Six successful attacks would cause six kills, but the five-model unit caps it at five.
    assert result.expected_models_destroyed == pytest.approx((4 / 3) - (2 / 9) ** 6)


def test_no_armour_save_when_modified_save_is_seven_plus() -> None:
    request = DamageRequest.model_validate(
        {
            "weapon": {
                "attacks": 1,
                "skill": 2,
                "strength": 4,
                "armour_penetration": -4,
                "damage": 1,
            },
            "defender": {"toughness": 4, "save": 3, "wounds": 1, "model_count": 1},
        }
    )

    result = calculate_expected_damage(request)

    assert result.modified_save_required == 7
    assert result.failed_save_probability == 1


def test_expected_destroyed_models_accounts_for_non_spillover_damage() -> None:
    request = DamageRequest.model_validate(
        {
            "weapon": {
                "attacks": 2,
                "skill": 2,
                "strength": 8,
                "armour_penetration": -4,
                "damage": 2,
            },
            "defender": {
                "toughness": 4,
                "save": 3,
                "wounds": 3,
                "model_count": 10,
            },
        }
    )

    result = calculate_expected_damage(request)

    # Each model needs two unsaved D2 attacks, so a two-attack weapon can kill at most one.
    assert result.expected_models_destroyed == pytest.approx((25 / 36) ** 2)


def test_expected_destroyed_models_is_capped_by_unit_size() -> None:
    request = DamageRequest.model_validate(
        {
            "weapon": {
                "attacks": 10,
                "skill": 2,
                "strength": 8,
                "armour_penetration": -4,
                "damage": 2,
            },
            "defender": {
                "toughness": 4,
                "save": 3,
                "wounds": 1,
                "model_count": 1,
            },
        }
    )

    result = calculate_expected_damage(request)

    assert result.expected_models_destroyed <= 1
