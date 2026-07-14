"""Schemas for calculations that use stored database profiles."""

from pydantic import BaseModel, Field

from app.models import DamageResponse
from app.rules.edition_11 import MAXIMUM_ATTACKS, MINIMUM_ATTACKS


class StoredDamageRequest(BaseModel):
    """Select stored profiles and quantities for a damage calculation."""

    weapon_profile_id: int = Field(ge=1)
    defender_unit_id: int = Field(ge=1)
    weapon_count: int = Field(
        default=1,
        ge=MINIMUM_ATTACKS,
        le=MAXIMUM_ATTACKS,
        description="Number of identical weapon profiles being resolved.",
    )
    defender_model_count: int = Field(
        ge=1,
        description=(
            "Selected defender size within the unit's permitted range."
        ),
    )


class CalculationUnitReference(BaseModel):
    """Identify a stored unit used in a calculation."""

    id: int
    name: str


class CalculationWeaponReference(BaseModel):
    """Identify a stored weapon profile used in a calculation."""

    id: int
    name: str
    profile_name: str


class StoredDamageResponse(BaseModel):
    """Return stored profile identities and their calculated result."""

    attacking_unit: CalculationUnitReference
    weapon: CalculationWeaponReference
    defender: CalculationUnitReference
    weapon_count: int
    defender_model_count: int
    result: DamageResponse
