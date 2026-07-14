"""Validation and response schemas for stored unit profiles."""

from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.rules.common import MAXIMUM_NAME_LENGTH, MINIMUM_NAME_LENGTH
from app.rules.edition_11 import (
    BEST_ARMOUR_SAVE,
    BEST_INVULNERABLE_SAVE,
    EDITION,
    MAXIMUM_LEADERSHIP,
    MAXIMUM_MOVEMENT,
    MAXIMUM_OBJECTIVE_CONTROL,
    MAXIMUM_TOUGHNESS,
    MAXIMUM_UNIT_SIZE,
    MAXIMUM_WOUNDS,
    MINIMUM_LEADERSHIP,
    MINIMUM_MOVEMENT,
    MINIMUM_OBJECTIVE_CONTROL,
    MINIMUM_POINTS,
    MINIMUM_TOUGHNESS,
    MINIMUM_UNIT_SIZE,
    MINIMUM_WOUNDS,
    NO_ARMOUR_SAVE,
    WORST_INVULNERABLE_SAVE,
)


class UnitFields(BaseModel):
    """Define fields required to describe a homogeneous unit."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        min_length=MINIMUM_NAME_LENGTH,
        max_length=MAXIMUM_NAME_LENGTH,
        description="Published name of the unit.",
        examples=["Intercessor Squad"],
    )
    faction: str = Field(
        min_length=MINIMUM_NAME_LENGTH,
        max_length=MAXIMUM_NAME_LENGTH,
        description="Faction that owns the unit.",
        examples=["Adeptus Astartes"],
    )
    movement: int = Field(
        ge=MINIMUM_MOVEMENT,
        le=MAXIMUM_MOVEMENT,
        description="Movement characteristic in inches.",
    )
    toughness: int = Field(
        ge=MINIMUM_TOUGHNESS,
        le=MAXIMUM_TOUGHNESS,
        description="Toughness characteristic shared by the models.",
    )
    save: int = Field(
        ge=BEST_ARMOUR_SAVE,
        le=NO_ARMOUR_SAVE,
        description="Armour save target; use 7 when no armour save exists.",
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
        description="Wounds characteristic for each model.",
    )
    leadership: int = Field(
        ge=MINIMUM_LEADERSHIP,
        le=MAXIMUM_LEADERSHIP,
        description="Leadership characteristic.",
    )
    objective_control: int = Field(
        ge=MINIMUM_OBJECTIVE_CONTROL,
        le=MAXIMUM_OBJECTIVE_CONTROL,
        description="Objective Control characteristic for each model.",
    )
    minimum_model_count: int = Field(
        ge=MINIMUM_UNIT_SIZE,
        le=MAXIMUM_UNIT_SIZE,
        description="Smallest supported unit size.",
    )
    maximum_model_count: int = Field(
        ge=MINIMUM_UNIT_SIZE,
        le=MAXIMUM_UNIT_SIZE,
        description="Largest supported unit size.",
    )
    points: int | None = Field(
        default=None,
        ge=MINIMUM_POINTS,
        description="Optional points cost for the base unit.",
    )
    edition: int = Field(
        default=EDITION,
        ge=1,
        description="Rules edition associated with the profile.",
    )
    source: str | None = Field(
        default=None,
        max_length=200,
        description="Optional source or import reference.",
    )
    source_version: str | None = Field(
        default=None,
        max_length=50,
        description="Optional version of the source data.",
    )

    @model_validator(mode="after")
    def validate_model_count_order(self) -> Self:
        """Require the maximum unit size to include the minimum size."""
        if self.maximum_model_count < self.minimum_model_count:
            raise ValueError(
                "Maximum model count cannot be less than minimum model count."
            )
        return self


class UnitCreate(UnitFields):
    """Validate a request to create a stored unit."""

    pass


class UnitUpdate(BaseModel):
    """Validate fields that may be changed on a stored unit."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(
        default=None,
        min_length=MINIMUM_NAME_LENGTH,
        max_length=MAXIMUM_NAME_LENGTH,
    )
    faction: str | None = Field(
        default=None,
        min_length=MINIMUM_NAME_LENGTH,
        max_length=MAXIMUM_NAME_LENGTH,
    )
    movement: int | None = Field(
        default=None,
        ge=MINIMUM_MOVEMENT,
        le=MAXIMUM_MOVEMENT,
    )
    toughness: int | None = Field(
        default=None,
        ge=MINIMUM_TOUGHNESS,
        le=MAXIMUM_TOUGHNESS,
    )
    save: int | None = Field(
        default=None,
        ge=BEST_ARMOUR_SAVE,
        le=NO_ARMOUR_SAVE,
    )
    invulnerable_save: int | None = Field(
        default=None,
        ge=BEST_INVULNERABLE_SAVE,
        le=WORST_INVULNERABLE_SAVE,
    )
    wounds: int | None = Field(
        default=None,
        ge=MINIMUM_WOUNDS,
        le=MAXIMUM_WOUNDS,
    )
    leadership: int | None = Field(
        default=None,
        ge=MINIMUM_LEADERSHIP,
        le=MAXIMUM_LEADERSHIP,
    )
    objective_control: int | None = Field(
        default=None,
        ge=MINIMUM_OBJECTIVE_CONTROL,
        le=MAXIMUM_OBJECTIVE_CONTROL,
    )
    minimum_model_count: int | None = Field(
        default=None,
        ge=MINIMUM_UNIT_SIZE,
        le=MAXIMUM_UNIT_SIZE,
    )
    maximum_model_count: int | None = Field(
        default=None,
        ge=MINIMUM_UNIT_SIZE,
        le=MAXIMUM_UNIT_SIZE,
    )
    points: int | None = Field(default=None, ge=MINIMUM_POINTS)
    edition: int | None = Field(default=None, ge=1)
    source: str | None = Field(default=None, max_length=200)
    source_version: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None


class UnitRead(UnitFields):
    """Serialize a stored unit and its database-managed fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
