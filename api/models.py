"""Django models for stored unit and weapon profiles."""

from django.db import models
from django.db.models.functions import Lower


class Unit(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    faction = models.CharField(max_length=100, db_index=True)
    movement = models.PositiveSmallIntegerField()
    toughness = models.PositiveSmallIntegerField()
    armour_save = models.PositiveSmallIntegerField(db_column="save")
    invulnerable_save = models.PositiveSmallIntegerField(null=True, blank=True)
    wounds = models.PositiveSmallIntegerField()
    leadership = models.PositiveSmallIntegerField()
    objective_control = models.PositiveSmallIntegerField()
    minimum_model_count = models.PositiveSmallIntegerField()
    maximum_model_count = models.PositiveSmallIntegerField()
    points = models.PositiveIntegerField(null=True, blank=True)
    edition = models.PositiveSmallIntegerField(default=11)
    source = models.CharField(max_length=200, null=True, blank=True)
    source_version = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(Lower("name"), Lower("faction"), "edition", name="unique_unit_identity"),
        ]


class WeaponProfile(models.Model):
    class WeaponType(models.TextChoices):
        RANGED = "ranged", "Ranged"
        MELEE = "melee", "Melee"

    unit = models.ForeignKey(Unit, related_name="weapons", on_delete=models.CASCADE)
    name = models.CharField(max_length=100, db_index=True)
    profile_name = models.CharField(max_length=100, default="default")
    weapon_type = models.CharField(max_length=10, choices=WeaponType.choices)
    range_inches = models.PositiveSmallIntegerField(null=True, blank=True)
    attacks = models.PositiveSmallIntegerField()
    skill = models.PositiveSmallIntegerField()
    strength = models.PositiveSmallIntegerField()
    armour_penetration = models.SmallIntegerField(default=0)
    damage = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "profile_name", "id"]
        constraints = [
            models.UniqueConstraint("unit", Lower("name"), Lower("profile_name"), "weapon_type", name="unique_unit_weapon_identity"),
        ]
