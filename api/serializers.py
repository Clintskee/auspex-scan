"""DRF serializers for persistence and API documentation."""

from rest_framework import serializers

from app.rules.edition_11 import (
    BEST_ARMOUR_SAVE, BEST_HIT_ROLL, BEST_INVULNERABLE_SAVE, MAXIMUM_ARMOUR_PENETRATION,
    MAXIMUM_ATTACKS, MAXIMUM_DAMAGE, MAXIMUM_LEADERSHIP, MAXIMUM_MOVEMENT,
    MAXIMUM_OBJECTIVE_CONTROL, MAXIMUM_STRENGTH, MAXIMUM_TOUGHNESS, MAXIMUM_UNIT_SIZE,
    MAXIMUM_WEAPON_RANGE, MAXIMUM_WOUNDS, MINIMUM_ARMOUR_PENETRATION, MINIMUM_ATTACKS,
    MINIMUM_DAMAGE, MINIMUM_LEADERSHIP, MINIMUM_MOVEMENT, MINIMUM_OBJECTIVE_CONTROL,
    MINIMUM_POINTS, MINIMUM_STRENGTH, MINIMUM_TOUGHNESS, MINIMUM_UNIT_SIZE,
    MINIMUM_WEAPON_RANGE, MINIMUM_WOUNDS, NO_ARMOUR_SAVE, WORST_HIT_ROLL,
    WORST_INVULNERABLE_SAVE,
)
from api.models import Unit, WeaponProfile


class UnitSerializer(serializers.ModelSerializer):
    movement = serializers.IntegerField(min_value=MINIMUM_MOVEMENT, max_value=MAXIMUM_MOVEMENT)
    toughness = serializers.IntegerField(min_value=MINIMUM_TOUGHNESS, max_value=MAXIMUM_TOUGHNESS)
    save = serializers.IntegerField(source="armour_save", min_value=BEST_ARMOUR_SAVE, max_value=NO_ARMOUR_SAVE)
    invulnerable_save = serializers.IntegerField(min_value=BEST_INVULNERABLE_SAVE, max_value=WORST_INVULNERABLE_SAVE, allow_null=True, required=False)
    wounds = serializers.IntegerField(min_value=MINIMUM_WOUNDS, max_value=MAXIMUM_WOUNDS)
    leadership = serializers.IntegerField(min_value=MINIMUM_LEADERSHIP, max_value=MAXIMUM_LEADERSHIP)
    objective_control = serializers.IntegerField(min_value=MINIMUM_OBJECTIVE_CONTROL, max_value=MAXIMUM_OBJECTIVE_CONTROL)
    minimum_model_count = serializers.IntegerField(min_value=MINIMUM_UNIT_SIZE, max_value=MAXIMUM_UNIT_SIZE)
    maximum_model_count = serializers.IntegerField(min_value=MINIMUM_UNIT_SIZE, max_value=MAXIMUM_UNIT_SIZE)
    points = serializers.IntegerField(min_value=MINIMUM_POINTS, allow_null=True, required=False)

    class Meta:
        model = Unit
        fields = (
            "id", "name", "faction", "movement", "toughness", "save",
            "invulnerable_save", "wounds", "leadership", "objective_control",
            "minimum_model_count", "maximum_model_count", "points", "edition",
            "source", "source_version", "is_active", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
        extra_kwargs = {
            "name": {"trim_whitespace": True}, "faction": {"trim_whitespace": True},
            "source": {"allow_null": True, "required": False},
            "source_version": {"allow_null": True, "required": False},
            "edition": {"required": False}, "is_active": {"required": False},
        }

    def validate(self, attrs):
        instance = self.instance
        minimum = attrs.get("minimum_model_count", getattr(instance, "minimum_model_count", None))
        maximum = attrs.get("maximum_model_count", getattr(instance, "maximum_model_count", None))
        if minimum is not None and maximum is not None and maximum < minimum:
            raise serializers.ValidationError("Maximum model count cannot be less than minimum model count.")
        name = attrs.get("name", getattr(instance, "name", None))
        faction = attrs.get("faction", getattr(instance, "faction", None))
        edition = attrs.get("edition", getattr(instance, "edition", 11))
        if name and faction:
            matches = Unit.objects.filter(name__iexact=name, faction__iexact=faction, edition=edition)
            if instance:
                matches = matches.exclude(pk=instance.pk)
            if matches.exists():
                raise serializers.ValidationError("A unit with this name, faction, and edition already exists.", code="conflict")
        return attrs


class WeaponSerializer(serializers.ModelSerializer):
    unit_id = serializers.IntegerField(source="unit.id", read_only=True)
    range_inches = serializers.IntegerField(min_value=MINIMUM_WEAPON_RANGE, max_value=MAXIMUM_WEAPON_RANGE, allow_null=True, required=False)
    attacks = serializers.IntegerField(min_value=MINIMUM_ATTACKS, max_value=MAXIMUM_ATTACKS)
    skill = serializers.IntegerField(min_value=BEST_HIT_ROLL, max_value=WORST_HIT_ROLL)
    strength = serializers.IntegerField(min_value=MINIMUM_STRENGTH, max_value=MAXIMUM_STRENGTH)
    armour_penetration = serializers.IntegerField(min_value=MINIMUM_ARMOUR_PENETRATION, max_value=MAXIMUM_ARMOUR_PENETRATION, required=False)
    damage = serializers.IntegerField(min_value=MINIMUM_DAMAGE, max_value=MAXIMUM_DAMAGE)

    class Meta:
        model = WeaponProfile
        exclude = ("unit",)
        read_only_fields = ("id", "created_at", "updated_at")
        extra_kwargs = {"profile_name": {"required": False}, "is_active": {"required": False}}

    def validate(self, attrs):
        instance = self.instance
        weapon_type = attrs.get("weapon_type", getattr(instance, "weapon_type", None))
        range_inches = attrs.get("range_inches", getattr(instance, "range_inches", None))
        if weapon_type == "ranged" and range_inches is None:
            raise serializers.ValidationError("Ranged weapons require range_inches.")
        if weapon_type == "melee" and range_inches is not None:
            raise serializers.ValidationError("Melee weapons cannot have range_inches.")
        unit = self.context["unit"]
        name = attrs.get("name", getattr(instance, "name", None))
        profile = attrs.get("profile_name", getattr(instance, "profile_name", "default"))
        matches = WeaponProfile.objects.filter(unit=unit, name__iexact=name, profile_name__iexact=profile, weapon_type=weapon_type)
        if instance:
            matches = matches.exclude(pk=instance.pk)
        if matches.exists():
            raise serializers.ValidationError("This unit already has a weapon with the same name, profile, and type.", code="conflict")
        return attrs


class InlineDamageSerializer(serializers.Serializer):
    weapon = serializers.JSONField()
    defender = serializers.JSONField()


class StoredDamageSerializer(serializers.Serializer):
    weapon_profile_id = serializers.IntegerField(min_value=1)
    defender_unit_id = serializers.IntegerField(min_value=1)
    weapon_count = serializers.IntegerField(min_value=MINIMUM_ATTACKS, max_value=MAXIMUM_ATTACKS, default=1)
    defender_model_count = serializers.IntegerField(min_value=1)
