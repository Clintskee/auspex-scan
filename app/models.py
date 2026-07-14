from pydantic import BaseModel, Field


class WeaponProfile(BaseModel):
    name: str = Field(default="Weapon", min_length=1, max_length=100)
    attacks: int = Field(ge=1, le=1000)
    skill: int = Field(ge=2, le=6, description="Unmodified hit roll required, e.g. 3 means 3+.")
    strength: int = Field(ge=1, le=100)
    armour_penetration: int = Field(
        default=0,
        ge=-10,
        le=0,
        description="AP as printed on the profile, e.g. -2.",
    )
    damage: int = Field(ge=1, le=100)


class DefenderProfile(BaseModel):
    name: str = Field(default="Defender", min_length=1, max_length=100)
    toughness: int = Field(ge=1, le=100)
    save: int = Field(ge=2, le=7, description="Armour save, e.g. 3 means 3+; use 7 for no save.")
    wounds: int = Field(ge=1, le=100, description="Wounds per model.")
    model_count: int = Field(ge=1, le=1000, description="Models in the defending unit.")


class DamageRequest(BaseModel):
    weapon: WeaponProfile
    defender: DefenderProfile


class DamageResponse(BaseModel):
    hit_probability: float
    wound_roll_required: int
    wound_probability: float
    modified_save_required: int
    failed_save_probability: float
    expected_hits: float
    expected_wounds: float
    expected_unsaved_attacks: float
    expected_damage: float
    expected_models_destroyed: float
