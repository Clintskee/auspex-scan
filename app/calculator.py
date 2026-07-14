from math import ceil, comb

from app.models import DamageRequest, DamageResponse


def success_probability(required_roll: int) -> float:
    """Return the probability of rolling at least required_roll on one D6."""
    if required_roll <= 2:
        return 5 / 6
    if required_roll >= 7:
        return 0.0
    return (7 - required_roll) / 6


def wound_roll_required(strength: int, toughness: int) -> int:
    """Apply the Warhammer 40,000 11th-edition wound roll table."""
    if strength >= toughness * 2:
        return 2
    if strength > toughness:
        return 3
    if strength == toughness:
        return 4
    if strength * 2 <= toughness:
        return 6
    return 5


def calculate_expected_damage(request: DamageRequest) -> DamageResponse:
    weapon = request.weapon
    defender = request.defender

    hit_probability = success_probability(weapon.skill)
    required_wound_roll = wound_roll_required(weapon.strength, defender.toughness)
    wound_probability = success_probability(required_wound_roll)

    # AP is represented as a non-positive value. AP -2 worsens a 3+ save to 5+.
    modified_save = defender.save - weapon.armour_penetration
    save_probability = success_probability(modified_save)
    failed_save_probability = 1 - save_probability

    expected_hits = weapon.attacks * hit_probability
    expected_wounds = expected_hits * wound_probability
    expected_unsaved_attacks = expected_wounds * failed_save_probability
    expected_damage = expected_unsaved_attacks * weapon.damage

    unsaved_attack_probability = (
        hit_probability * wound_probability * failed_save_probability
    )
    attacks_to_destroy_model = ceil(defender.wounds / weapon.damage)
    expected_models_destroyed = sum(
        min(defender.model_count, unsaved_attacks // attacks_to_destroy_model)
        * comb(weapon.attacks, unsaved_attacks)
        * unsaved_attack_probability**unsaved_attacks
        * (1 - unsaved_attack_probability) ** (weapon.attacks - unsaved_attacks)
        for unsaved_attacks in range(weapon.attacks + 1)
    )

    return DamageResponse(
        hit_probability=hit_probability,
        wound_roll_required=required_wound_roll,
        wound_probability=wound_probability,
        modified_save_required=modified_save,
        failed_save_probability=failed_save_probability,
        expected_hits=expected_hits,
        expected_wounds=expected_wounds,
        expected_unsaved_attacks=expected_unsaved_attacks,
        expected_damage=expected_damage,
        expected_models_destroyed=expected_models_destroyed,
    )
