"""Calculation endpoints backed by stored database profiles."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.calculation_schemas import (
    CalculationUnitReference,
    CalculationWeaponReference,
    StoredDamageRequest,
    StoredDamageResponse,
)
from app.calculator import calculate_expected_damage
from app.database import get_db
from app.db_models import Unit, WeaponProfile as StoredWeaponProfile
from app.models import (
    DamageRequest,
    DefenderProfile,
    WeaponProfile as CalculationWeaponProfile,
)
from app.rules.edition_11 import MAXIMUM_ATTACKS

router = APIRouter(prefix="/v1/calculations", tags=["calculations"])


def get_active_unit(
    unit_id: int,
    role: str,
    database: Session,
) -> Unit:
    """Return an active unit or raise a role-specific HTTP error."""
    unit = database.get(Unit, unit_id)
    if unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{role} unit not found.",
        )
    if not unit.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{role} unit is inactive.",
        )
    return unit


def get_active_weapon(
    weapon_profile_id: int,
    database: Session,
) -> StoredWeaponProfile:
    """Return an active weapon profile or raise an HTTP error."""
    weapon = database.get(StoredWeaponProfile, weapon_profile_id)
    if weapon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weapon profile not found.",
        )
    if not weapon.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Weapon profile is inactive.",
        )
    return weapon


@router.post(
    "/expected-damage",
    response_model=StoredDamageResponse,
    summary="Calculate damage using stored profiles",
)
def calculate_stored_damage(
    payload: StoredDamageRequest,
    database: Session = Depends(get_db),
) -> StoredDamageResponse:
    """Calculate expected damage using a stored weapon and defender."""
    weapon = get_active_weapon(payload.weapon_profile_id, database)
    attacker = get_active_unit(weapon.unit_id, "Attacking", database)
    defender = get_active_unit(
        payload.defender_unit_id,
        "Defending",
        database,
    )

    if not (
        defender.minimum_model_count
        <= payload.defender_model_count
        <= defender.maximum_model_count
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Defender model count must be between "
                f"{defender.minimum_model_count} and "
                f"{defender.maximum_model_count}."
            ),
        )

    total_attacks = weapon.attacks * payload.weapon_count
    if total_attacks > MAXIMUM_ATTACKS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Total attacks cannot exceed {MAXIMUM_ATTACKS}.",
        )

    calculation_request = DamageRequest(
        weapon=CalculationWeaponProfile(
            name=weapon.name,
            attacks=total_attacks,
            skill=weapon.skill,
            strength=weapon.strength,
            armour_penetration=weapon.armour_penetration,
            damage=weapon.damage,
        ),
        defender=DefenderProfile(
            name=defender.name,
            toughness=defender.toughness,
            save=defender.save,
            invulnerable_save=defender.invulnerable_save,
            wounds=defender.wounds,
            model_count=payload.defender_model_count,
        ),
    )

    return StoredDamageResponse(
        attacking_unit=CalculationUnitReference(
            id=attacker.id,
            name=attacker.name,
        ),
        weapon=CalculationWeaponReference(
            id=weapon.id,
            name=weapon.name,
            profile_name=weapon.profile_name,
        ),
        defender=CalculationUnitReference(
            id=defender.id,
            name=defender.name,
        ),
        weapon_count=payload.weapon_count,
        defender_model_count=payload.defender_model_count,
        result=calculate_expected_damage(calculation_request),
    )

