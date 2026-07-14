"""CRUD endpoints for stored unit profiles."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models import Unit
from app.unit_schemas import UnitCreate, UnitRead, UnitUpdate

router = APIRouter(prefix="/v1/units", tags=["units"])

UNIT_IDENTITY_CONFLICT = (
    "A unit with this name, faction, and edition already exists."
)


def get_unit_or_404(unit_id: int, database: Session) -> Unit:
    """Return a stored unit or raise HTTP 404 when it does not exist."""
    unit = database.get(Unit, unit_id)
    if unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found.",
        )
    return unit


def find_matching_unit(
    database: Session,
    name: str,
    faction: str,
    edition: int,
    excluded_unit_id: int | None = None,
) -> Unit | None:
    """Find a unit with the same case-insensitive canonical identity."""
    statement = select(Unit).where(
        Unit.name == name,
        Unit.faction == faction,
        Unit.edition == edition,
    )
    if excluded_unit_id is not None:
        statement = statement.where(Unit.id != excluded_unit_id)
    return database.scalar(statement)


def commit_or_conflict(database: Session) -> None:
    """Commit changes or translate an identity race into HTTP 409."""
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=UNIT_IDENTITY_CONFLICT,
        ) from error


@router.post(
    "",
    response_model=UnitRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a unit",
)
def create_unit(
    payload: UnitCreate,
    database: Session = Depends(get_db),
) -> Unit:
    """Validate and persist a homogeneous unit profile."""
    duplicate = find_matching_unit(
        database,
        payload.name,
        payload.faction,
        payload.edition,
    )
    if duplicate is not None:
        state = "inactive" if not duplicate.is_active else "active"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{UNIT_IDENTITY_CONFLICT} The existing unit is {state}.",
        )

    unit = Unit(**payload.model_dump())
    database.add(unit)
    commit_or_conflict(database)
    database.refresh(unit)
    return unit


@router.get("", response_model=list[UnitRead], summary="List units")
def list_units(
    include_inactive: bool = Query(
        default=False,
        description="Include units that have been soft deleted.",
    ),
    database: Session = Depends(get_db),
) -> list[Unit]:
    """List units alphabetically, excluding inactive units by default."""
    statement = select(Unit).order_by(Unit.name, Unit.id)
    if not include_inactive:
        statement = statement.where(Unit.is_active.is_(True))
    return list(database.scalars(statement))


@router.get(
    "/{unit_id}",
    response_model=UnitRead,
    summary="Get a unit",
)
def get_unit(
    unit_id: int,
    database: Session = Depends(get_db),
) -> Unit:
    """Return one stored unit by its identifier."""
    return get_unit_or_404(unit_id, database)


@router.patch(
    "/{unit_id}",
    response_model=UnitRead,
    summary="Update a unit",
)
def update_unit(
    unit_id: int,
    payload: UnitUpdate,
    database: Session = Depends(get_db),
) -> Unit:
    """Apply validated partial changes to a stored unit."""
    unit = get_unit_or_404(unit_id, database)
    changes = payload.model_dump(exclude_unset=True)

    non_nullable_fields = {
        "name",
        "faction",
        "movement",
        "toughness",
        "save",
        "wounds",
        "leadership",
        "objective_control",
        "minimum_model_count",
        "maximum_model_count",
        "edition",
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

    minimum_count = changes.get(
        "minimum_model_count",
        unit.minimum_model_count,
    )
    maximum_count = changes.get(
        "maximum_model_count",
        unit.maximum_model_count,
    )
    if maximum_count < minimum_count:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Maximum model count cannot be less than minimum model count."
            ),
        )

    identity_name = changes.get("name", unit.name)
    identity_faction = changes.get("faction", unit.faction)
    identity_edition = changes.get("edition", unit.edition)
    duplicate = find_matching_unit(
        database,
        identity_name,
        identity_faction,
        identity_edition,
        excluded_unit_id=unit.id,
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=UNIT_IDENTITY_CONFLICT,
        )

    for field_name, value in changes.items():
        setattr(unit, field_name, value)

    commit_or_conflict(database)
    database.refresh(unit)
    return unit


@router.delete(
    "/{unit_id}",
    response_model=UnitRead,
    summary="Deactivate a unit",
)
def delete_unit(
    unit_id: int,
    database: Session = Depends(get_db),
) -> Unit:
    """Soft delete a unit so existing references remain valid."""
    unit = get_unit_or_404(unit_id, database)
    unit.is_active = False
    database.commit()
    database.refresh(unit)
    return unit
