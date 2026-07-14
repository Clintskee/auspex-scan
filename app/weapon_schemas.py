"""Validation and response schemas for stored weapon profiles."""

from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.rules.common import MAXIMUM_NAME_LENGTH, MINIMUM_NAME_LENGTH
from app.rules.edition_11 import (
    BEST_HIT_ROLL,
    MAXIMUM_ARMOUR_PENETRATION,
    MAXIMUM_ATTACKS,
    MAXIMUM_DAMAGE,
    MAXIMUM_STRENGTH,
    MAXIMUM_WEAPON_RANGE,
    MINIMUM_ARMOUR_PENETRATION,
    MINIMUM_ATTACKS,
    MINIMUM_DAMAGE,
    MINIMUM_STRENGTH,
    MINIMUM_WEAPON_RANGE,
    WORST_HIT_ROLL,
)

WeaponType = Literal["ranged", "melee"]


class WeaponFields(BaseModel):
    """Define fields required for one fixed weapon profile."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        min_length=MINIMUM_NAME_LENGTH,
        max_length=MAXIMUM_NAME_LENGTH,
        description="Published name of the weapon.",
        examples=["Bolt rifle"],
    )
    profile_name: str = Field(
        default="default",
        min_length=MINIMUM_NAME_LENGTH,
        max_length=MAXIMUM_NAME_LENGTH,
        description="Name distinguishing alternate profiles or firing modes.",
        examples=["default"],
    )
    weapon_type: WeaponType = Field(
        description="Whether the profile is ranged or melee."
    )
    range_inches: int | None = Field(
        default=None,
        ge=MINIMUM_WEAPON_RANGE,
        le=MAXIMUM_WEAPON_RANGE,
        description="Range in inches; required for ranged and null for melee.",
    )
    attacks: int = Field(
        ge=MINIMUM_ATTACKS,
        le=MAXIMUM_ATTACKS,
        description="Fixed number of attacks made by the profile.",
    )
    skill: int = Field(
        ge=BEST_HIT_ROLL,
        le=WORST_HIT_ROLL,
        description="Unmodified hit roll required, e.g. 3 means 3+.",
    )
    strength: int = Field(
        ge=MINIMUM_STRENGTH,
        le=MAXIMUM_STRENGTH,
        description="Strength characteristic.",
    )
    armour_penetration: int = Field(
        default=0,
        ge=MINIMUM_ARMOUR_PENETRATION,
        le=MAXIMUM_ARMOUR_PENETRATION,
        description="Armour Penetration as printed, e.g. -1.",
    )
    damage: int = Field(
        ge=MINIMUM_DAMAGE,
        le=MAXIMUM_DAMAGE,
        description="Fixed damage inflicted by an unsaved attack.",
    )

    @model_validator(mode="after")
    def validate_range_for_weapon_type(self) -> Self:
        """Require range only for ranged weapon profiles."""
        if self.weapon_type == "ranged" and self.range_inches is None:
            raise ValueError("Ranged weapons require range_inches.")
        if self.weapon_type == "melee" and self.range_inches is not None:
            raise ValueError("Melee weapons cannot have range_inches.")
        return self


class WeaponCreate(WeaponFields):
    """Validate a request to create a stored weapon profile."""

    pass


class WeaponUpdate(BaseModel):
    """Validate fields that may be changed on a weapon profile."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(
        default=None,
        min_length=MINIMUM_NAME_LENGTH,
        max_length=MAXIMUM_NAME_LENGTH,
    )
    profile_name: str | None = Field(
        default=None,
        min_length=MINIMUM_NAME_LENGTH,
        max_length=MAXIMUM_NAME_LENGTH,
    )
    weapon_type: WeaponType | None = None
    range_inches: int | None = Field(
        default=None,
        ge=MINIMUM_WEAPON_RANGE,
        le=MAXIMUM_WEAPON_RANGE,
    )
    attacks: int | None = Field(
        default=None,
        ge=MINIMUM_ATTACKS,
        le=MAXIMUM_ATTACKS,
    )
    skill: int | None = Field(
        default=None,
        ge=BEST_HIT_ROLL,
        le=WORST_HIT_ROLL,
    )
    strength: int | None = Field(
        default=None,
        ge=MINIMUM_STRENGTH,
        le=MAXIMUM_STRENGTH,
    )
    armour_penetration: int | None = Field(
        default=None,
        ge=MINIMUM_ARMOUR_PENETRATION,
        le=MAXIMUM_ARMOUR_PENETRATION,
    )
    damage: int | None = Field(
        default=None,
        ge=MINIMUM_DAMAGE,
        le=MAXIMUM_DAMAGE,
    )
    is_active: bool | None = None


class WeaponRead(WeaponFields):
    """Serialize a stored weapon profile and database-managed fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    unit_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

