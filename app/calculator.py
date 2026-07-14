"""Expected-damage calculations for a single attack profile."""

from math import ceil, comb

from app.models import DamageRequest, DamageResponse
from app.rules.common import BEST_D6_TARGET, D6_SIDES, IMPOSSIBLE_D6_TARGET


def success_probability(required_roll: int) -> float:
    """Return the probability of rolling at least required_roll on one D6."""
    if required_roll <= BEST_D6_TARGET:
        return (D6_SIDES - 1) / D6_SIDES
    if required_roll >= IMPOSSIBLE_D6_TARGET:
        return 0.0
    return (D6_SIDES + 1 - required_roll) / D6_SIDES


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
    """Calculate expected damage and destroyed models for one profile.

    The destroyed-model expectation uses the binomial distribution of
    unsaved attacks. Damage from one attack does not spill between models.

    Args:
        request: Validated weapon and homogeneous defender profiles.

    Returns:
        Probability stages and expected combat results.
    """
    weapon = request.weapon
    defender = request.defender

    hit_probability = success_probability(weapon.skill)
    required_wound_roll = wound_roll_required(
        weapon.strength,
        defender.toughness,
    )
    wound_probability = success_probability(required_wound_roll)

    # AP is represented as a non-positive value. AP -2 worsens a 3+ save to 5+.
    modified_save = defender.save - weapon.armour_penetration
    armour_save_probability = success_probability(modified_save)
    invulnerable_save_probability = 0.0
    if defender.invulnerable_save is not None:
        invulnerable_save_probability = success_probability(
            defender.invulnerable_save
        )

    if invulnerable_save_probability > armour_save_probability:
        save_probability = invulnerable_save_probability
        save_used = "invulnerable"
        effective_save_required = defender.invulnerable_save
    elif armour_save_probability > 0:
        save_probability = armour_save_probability
        save_used = "armour"
        effective_save_required = modified_save
    else:
        save_probability = 0.0
        save_used = "none"
        effective_save_required = None

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
        * (1 - unsaved_attack_probability)
        ** (weapon.attacks - unsaved_attacks)
        for unsaved_attacks in range(weapon.attacks + 1)
    )

    return DamageResponse(
        hit_probability=hit_probability,
        wound_roll_required=required_wound_roll,
        wound_probability=wound_probability,
        modified_save_required=modified_save,
        save_used=save_used,
        effective_save_required=effective_save_required,
        failed_save_probability=failed_save_probability,
        expected_hits=expected_hits,
        expected_wounds=expected_wounds,
        expected_unsaved_attacks=expected_unsaved_attacks,
        expected_damage=expected_damage,
        expected_models_destroyed=expected_models_destroyed,
    )
