"""SQLAlchemy models for persisted application data."""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.rules.edition_11 import (
    BEST_ARMOUR_SAVE,
    BEST_HIT_ROLL,
    BEST_INVULNERABLE_SAVE,
    MAXIMUM_ARMOUR_PENETRATION,
    MAXIMUM_ATTACKS,
    MAXIMUM_DAMAGE,
    MAXIMUM_LEADERSHIP,
    MAXIMUM_MOVEMENT,
    MAXIMUM_OBJECTIVE_CONTROL,
    MAXIMUM_TOUGHNESS,
    MAXIMUM_UNIT_SIZE,
    MAXIMUM_WEAPON_RANGE,
    MAXIMUM_WOUNDS,
    MAXIMUM_STRENGTH,
    MINIMUM_ARMOUR_PENETRATION,
    MINIMUM_ATTACKS,
    MINIMUM_DAMAGE,
    MINIMUM_LEADERSHIP,
    MINIMUM_MOVEMENT,
    MINIMUM_OBJECTIVE_CONTROL,
    MINIMUM_POINTS,
    MINIMUM_TOUGHNESS,
    MINIMUM_UNIT_SIZE,
    MINIMUM_WEAPON_RANGE,
    MINIMUM_WOUNDS,
    MINIMUM_STRENGTH,
    NO_ARMOUR_SAVE,
    WORST_INVULNERABLE_SAVE,
    WORST_HIT_ROLL,
)


def utc_now() -> datetime:
    """Return the current UTC timestamp for database defaults."""
    return datetime.now(timezone.utc)


class Unit(Base):
    """Persist a homogeneous Warhammer 40,000 unit profile."""

    __tablename__ = "units"
    __table_args__ = (
        CheckConstraint(
            f"movement BETWEEN {MINIMUM_MOVEMENT} AND {MAXIMUM_MOVEMENT}",
            name="unit_movement_range",
        ),
        CheckConstraint(
            f"toughness BETWEEN {MINIMUM_TOUGHNESS} AND {MAXIMUM_TOUGHNESS}",
            name="unit_toughness_range",
        ),
        CheckConstraint(
            f"save BETWEEN {BEST_ARMOUR_SAVE} AND {NO_ARMOUR_SAVE}",
            name="unit_save_range",
        ),
        CheckConstraint(
            "invulnerable_save IS NULL OR "
            f"invulnerable_save BETWEEN {BEST_INVULNERABLE_SAVE} "
            f"AND {WORST_INVULNERABLE_SAVE}",
            name="unit_invulnerable_save_range",
        ),
        CheckConstraint(
            f"wounds BETWEEN {MINIMUM_WOUNDS} AND {MAXIMUM_WOUNDS}",
            name="unit_wounds_range",
        ),
        CheckConstraint(
            f"leadership BETWEEN {MINIMUM_LEADERSHIP} "
            f"AND {MAXIMUM_LEADERSHIP}",
            name="unit_leadership_range",
        ),
        CheckConstraint(
            f"objective_control BETWEEN {MINIMUM_OBJECTIVE_CONTROL} "
            f"AND {MAXIMUM_OBJECTIVE_CONTROL}",
            name="unit_objective_control_range",
        ),
        CheckConstraint(
            f"minimum_model_count BETWEEN {MINIMUM_UNIT_SIZE} "
            f"AND {MAXIMUM_UNIT_SIZE}",
            name="unit_minimum_model_count_range",
        ),
        CheckConstraint(
            f"maximum_model_count BETWEEN {MINIMUM_UNIT_SIZE} "
            f"AND {MAXIMUM_UNIT_SIZE}",
            name="unit_maximum_model_count_range",
        ),
        CheckConstraint(
            "maximum_model_count >= minimum_model_count",
            name="unit_model_count_order",
        ),
        CheckConstraint(
            f"points IS NULL OR points >= {MINIMUM_POINTS}",
            name="unit_points_minimum",
        ),
        UniqueConstraint(
            "faction",
            "name",
            "edition",
            name="unique_unit_identity",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100, collation="NOCASE"),
        index=True,
    )
    faction: Mapped[str] = mapped_column(
        String(100, collation="NOCASE"),
        index=True,
    )
    movement: Mapped[int] = mapped_column(Integer)
    toughness: Mapped[int] = mapped_column(Integer)
    save: Mapped[int] = mapped_column(Integer)
    invulnerable_save: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    wounds: Mapped[int] = mapped_column(Integer)
    leadership: Mapped[int] = mapped_column(Integer)
    objective_control: Mapped[int] = mapped_column(Integer)
    minimum_model_count: Mapped[int] = mapped_column(Integer)
    maximum_model_count: Mapped[int] = mapped_column(Integer)
    points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    edition: Mapped[int] = mapped_column(Integer, default=11)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
    )


class WeaponProfile(Base):
    """Persist one fixed weapon profile owned by a unit."""

    __tablename__ = "weapon_profiles"
    __table_args__ = (
        CheckConstraint(
            "weapon_type IN ('ranged', 'melee')",
            name="weapon_profile_type",
        ),
        CheckConstraint(
            "(weapon_type = 'ranged' AND range_inches IS NOT NULL) OR "
            "(weapon_type = 'melee' AND range_inches IS NULL)",
            name="weapon_profile_range_by_type",
        ),
        CheckConstraint(
            "range_inches IS NULL OR "
            f"range_inches BETWEEN {MINIMUM_WEAPON_RANGE} "
            f"AND {MAXIMUM_WEAPON_RANGE}",
            name="weapon_profile_range",
        ),
        CheckConstraint(
            f"attacks BETWEEN {MINIMUM_ATTACKS} AND {MAXIMUM_ATTACKS}",
            name="weapon_profile_attacks_range",
        ),
        CheckConstraint(
            f"skill BETWEEN {BEST_HIT_ROLL} AND {WORST_HIT_ROLL}",
            name="weapon_profile_skill_range",
        ),
        CheckConstraint(
            f"strength BETWEEN {MINIMUM_STRENGTH} AND {MAXIMUM_STRENGTH}",
            name="weapon_profile_strength_range",
        ),
        CheckConstraint(
            f"armour_penetration BETWEEN {MINIMUM_ARMOUR_PENETRATION} "
            f"AND {MAXIMUM_ARMOUR_PENETRATION}",
            name="weapon_profile_armour_penetration_range",
        ),
        CheckConstraint(
            f"damage BETWEEN {MINIMUM_DAMAGE} AND {MAXIMUM_DAMAGE}",
            name="weapon_profile_damage_range",
        ),
        UniqueConstraint(
            "unit_id",
            "name",
            "profile_name",
            "weapon_type",
            name="unique_unit_weapon_profile_identity",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(
        ForeignKey("units.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100, collation="NOCASE"),
        index=True,
    )
    profile_name: Mapped[str] = mapped_column(
        String(100, collation="NOCASE"),
        default="default",
    )
    weapon_type: Mapped[str] = mapped_column(String(10))
    range_inches: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attacks: Mapped[int] = mapped_column(Integer)
    skill: Mapped[int] = mapped_column(Integer)
    strength: Mapped[int] = mapped_column(Integer)
    armour_penetration: Mapped[int] = mapped_column(Integer, default=0)
    damage: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
    )
