"""API schemas for inline expected-damage calculations."""

from typing import Literal

from pydantic import BaseModel, Field

from app.rules.common import MAXIMUM_NAME_LENGTH, MINIMUM_NAME_LENGTH
from app.rules.edition_11 import (
    BEST_ARMOUR_SAVE,
    BEST_INVULNERABLE_SAVE,
    BEST_HIT_ROLL,
    MAXIMUM_ARMOUR_PENETRATION,
    MAXIMUM_ATTACKS,
    MAXIMUM_DAMAGE,
    MAXIMUM_STRENGTH,
    MAXIMUM_TOUGHNESS,
    MAXIMUM_UNIT_SIZE,
    MAXIMUM_WOUNDS,
    MINIMUM_ARMOUR_PENETRATION,
    MINIMUM_ATTACKS,
    MINIMUM_DAMAGE,
    MINIMUM_STRENGTH,
    MINIMUM_TOUGHNESS,
    MINIMUM_UNIT_SIZE,
    MINIMUM_WOUNDS,
    NO_ARMOUR_SAVE,
    WORST_HIT_ROLL,
    WORST_INVULNERABLE_SAVE,
)


class WeaponProfile(BaseModel):
    """Describe one fixed weapon profile used in a calculation."""

    name: str = Field(
        default="Weapon",
        min_length=MINIMUM_NAME_LENGTH,
        max_length=MAXIMUM_NAME_LENGTH,
    )
    attacks: int = Field(ge=MINIMUM_ATTACKS, le=MAXIMUM_ATTACKS)
    skill: int = Field(
        ge=BEST_HIT_ROLL,
        le=WORST_HIT_ROLL,
        description="Unmodified hit roll required, e.g. 3 means 3+.",
    )
    strength: int = Field(ge=MINIMUM_STRENGTH, le=MAXIMUM_STRENGTH)
    armour_penetration: int = Field(
        default=0,
        ge=MINIMUM_ARMOUR_PENETRATION,
        le=MAXIMUM_ARMOUR_PENETRATION,
        description="AP as printed on the profile, e.g. -2.",
    )
    damage: int = Field(ge=MINIMUM_DAMAGE, le=MAXIMUM_DAMAGE)


class DefenderProfile(BaseModel):
    """Describe one homogeneous defending unit used in a calculation."""

    name: str = Field(
        default="Defender",
        min_length=MINIMUM_NAME_LENGTH,
        max_length=MAXIMUM_NAME_LENGTH,
    )
    toughness: int = Field(
        ge=MINIMUM_TOUGHNESS,
        le=MAXIMUM_TOUGHNESS,
    )
    save: int = Field(
        ge=BEST_ARMOUR_SAVE,
        le=NO_ARMOUR_SAVE,
        description="Armour save, e.g. 3 means 3+; use 7 for no save.",
    )
    invulnerable_save: int | None = Field(
        default=None,
        ge=BEST_INVULNERABLE_SAVE,
        le=WORST_INVULNERABLE_SAVE,
        description="Invulnerable save target, or null when none exists.",
    )
    wounds: int = Field(
        ge=MINIMUM_WOUNDS,
        le=MAXIMUM_WOUNDS,
        description="Wounds per model.",
    )
    model_count: int = Field(
        ge=MINIMUM_UNIT_SIZE,
        le=MAXIMUM_UNIT_SIZE,
        description="Models in the defending unit.",
    )


class DamageRequest(BaseModel):
    """Pair one weapon profile with one defending unit profile."""

    weapon: WeaponProfile
    defender: DefenderProfile


class DamageResponse(BaseModel):
    """Expose probability stages and expected attack results."""

    hit_probability: float
    wound_roll_required: int
    wound_probability: float
    modified_save_required: int
    save_used: Literal["armour", "invulnerable", "none"]
    effective_save_required: int | None
    failed_save_probability: float
    expected_hits: float
    expected_wounds: float
    expected_unsaved_attacks: float
    expected_damage: float
    expected_models_destroyed: float
