"""CRUD endpoints for weapon profiles owned by stored units."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models import Unit, WeaponProfile
from app.weapon_schemas import WeaponCreate, WeaponRead, WeaponUpdate

router = APIRouter(
    prefix="/v1/units/{unit_id}/weapons",
    tags=["weapons"],
)

WEAPON_IDENTITY_CONFLICT = (
    "This unit already has a weapon with the same name, profile, and type."
)


def get_parent_unit_or_404(unit_id: int, database: Session) -> Unit:
    """Return a unit or raise HTTP 404 when it does not exist."""
    unit = database.get(Unit, unit_id)
    if unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found.",
        )
    return unit


def get_weapon_or_404(
    unit_id: int,
    weapon_id: int,
    database: Session,
) -> WeaponProfile:
    """Return a weapon belonging to the unit or raise HTTP 404."""
    statement = select(WeaponProfile).where(
        WeaponProfile.id == weapon_id,
        WeaponProfile.unit_id == unit_id,
    )
    weapon = database.scalar(statement)
    if weapon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weapon profile not found for this unit.",
        )
    return weapon


def find_matching_weapon(
    database: Session,
    unit_id: int,
    name: str,
    profile_name: str,
    weapon_type: str,
    excluded_weapon_id: int | None = None,
) -> WeaponProfile | None:
    """Find a case-insensitive matching weapon identity for one unit."""
    statement = select(WeaponProfile).where(
        WeaponProfile.unit_id == unit_id,
        WeaponProfile.name == name,
        WeaponProfile.profile_name == profile_name,
        WeaponProfile.weapon_type == weapon_type,
    )
    if excluded_weapon_id is not None:
        statement = statement.where(WeaponProfile.id != excluded_weapon_id)
    return database.scalar(statement)


def commit_or_conflict(database: Session) -> None:
    """Commit changes or translate an identity race into HTTP 409."""
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=WEAPON_IDENTITY_CONFLICT,
        ) from error


def validate_weapon_range(
    weapon_type: str,
    range_inches: int | None,
) -> None:
    """Validate the relationship between weapon type and range."""
    if weapon_type == "ranged" and range_inches is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ranged weapons require range_inches.",
        )
    if weapon_type == "melee" and range_inches is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Melee weapons cannot have range_inches.",
        )


@router.post(
    "",
    response_model=WeaponRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a weapon profile",
)
def create_weapon(
    unit_id: int,
    payload: WeaponCreate,
    database: Session = Depends(get_db),
) -> WeaponProfile:
    """Validate and attach a fixed weapon profile to a stored unit."""
    unit = get_parent_unit_or_404(unit_id, database)
    if not unit.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot add a weapon to an inactive unit.",
        )

    duplicate = find_matching_weapon(
        database,
        unit_id,
        payload.name,
        payload.profile_name,
        payload.weapon_type,
    )
    if duplicate is not None:
        state = "inactive" if not duplicate.is_active else "active"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"{WEAPON_IDENTITY_CONFLICT} "
                f"The existing profile is {state}."
            ),
        )

    weapon = WeaponProfile(unit_id=unit_id, **payload.model_dump())
    database.add(weapon)
    commit_or_conflict(database)
    database.refresh(weapon)
    return weapon


@router.get("", response_model=list[WeaponRead], summary="List weapons")
def list_weapons(
    unit_id: int,
    include_inactive: bool = Query(
        default=False,
        description="Include weapon profiles that have been soft deleted.",
    ),
    database: Session = Depends(get_db),
) -> list[WeaponProfile]:
    """List weapon profiles owned by one unit."""
    get_parent_unit_or_404(unit_id, database)
    statement = (
        select(WeaponProfile)
        .where(WeaponProfile.unit_id == unit_id)
        .order_by(WeaponProfile.name, WeaponProfile.profile_name)
    )
    if not include_inactive:
        statement = statement.where(WeaponProfile.is_active.is_(True))
    return list(database.scalars(statement))


@router.get(
    "/{weapon_id}",
    response_model=WeaponRead,
    summary="Get a weapon profile",
)
def get_weapon(
    unit_id: int,
    weapon_id: int,
    database: Session = Depends(get_db),
) -> WeaponProfile:
    """Return one weapon profile owned by the selected unit."""
    get_parent_unit_or_404(unit_id, database)
    return get_weapon_or_404(unit_id, weapon_id, database)


@router.patch(
    "/{weapon_id}",
    response_model=WeaponRead,
    summary="Update a weapon profile",
)
def update_weapon(
    unit_id: int,
    weapon_id: int,
    payload: WeaponUpdate,
    database: Session = Depends(get_db),
) -> WeaponProfile:
    """Apply validated partial changes to a weapon profile."""
    get_parent_unit_or_404(unit_id, database)
    weapon = get_weapon_or_404(unit_id, weapon_id, database)
    changes = payload.model_dump(exclude_unset=True)

    non_nullable_fields = {
        "name",
        "profile_name",
        "weapon_type",
        "attacks",
        "skill",
        "strength",
        "armour_penetration",
        "damage",
        "is_active",
    }
    null_fields = non_nullable_fields.intersection(
        field_name
        for field_name, value in changes.items()
        if value is None
    )
    if null_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Fields cannot be null: {', '.join(sorted(null_fields))}.",
        )

    weapon_type = changes.get("weapon_type", weapon.weapon_type)
    range_inches = changes.get("range_inches", weapon.range_inches)
    validate_weapon_range(weapon_type, range_inches)

    identity_name = changes.get("name", weapon.name)
    identity_profile = changes.get("profile_name", weapon.profile_name)
    duplicate = find_matching_weapon(
        database,
        unit_id,
        identity_name,
        identity_profile,
        weapon_type,
        excluded_weapon_id=weapon.id,
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=WEAPON_IDENTITY_CONFLICT,
        )

    for field_name, value in changes.items():
        setattr(weapon, field_name, value)

    commit_or_conflict(database)
    database.refresh(weapon)
    return weapon


@router.delete(
    "/{weapon_id}",
    response_model=WeaponRead,
    summary="Deactivate a weapon profile",
)
def delete_weapon(
    unit_id: int,
    weapon_id: int,
    database: Session = Depends(get_db),
) -> WeaponProfile:
    """Soft delete a weapon profile so references remain valid."""
    get_parent_unit_or_404(unit_id, database)
    weapon = get_weapon_or_404(unit_id, weapon_id, database)
    weapon.is_active = False
    database.commit()
    database.refresh(weapon)
    return weapon
