"""DRF views for CRUD and expected-damage calculations."""

from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from pydantic import ValidationError as PydanticValidationError
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import Unit, WeaponProfile
from api.serializers import InlineDamageSerializer, StoredDamageSerializer, UnitSerializer, WeaponSerializer
from app.calculator import calculate_expected_damage
from app.models import DamageRequest


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response({"status": "ok"})


class UnitListCreateView(APIView):
    @extend_schema(responses=UnitSerializer(many=True))
    def get(self, request):
        units = Unit.objects.all()
        if request.query_params.get("include_inactive", "false").lower() != "true":
            units = units.filter(is_active=True)
        return Response(UnitSerializer(units, many=True).data)

    @extend_schema(request=UnitSerializer, responses={201: UnitSerializer})
    def post(self, request):
        serializer = UnitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UnitDetailView(APIView):
    def get_object(self, unit_id):
        return get_object_or_404(Unit, pk=unit_id)

    @extend_schema(responses=UnitSerializer)
    def get(self, request, unit_id):
        return Response(UnitSerializer(self.get_object(unit_id)).data)

    @extend_schema(request=UnitSerializer, responses=UnitSerializer)
    def patch(self, request, unit_id):
        serializer = UnitSerializer(self.get_object(unit_id), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(responses=UnitSerializer)
    def delete(self, request, unit_id):
        unit = self.get_object(unit_id)
        unit.is_active = False
        unit.save(update_fields=["is_active", "updated_at"])
        return Response(UnitSerializer(unit).data)


class WeaponListCreateView(APIView):
    def parent(self, unit_id):
        return get_object_or_404(Unit, pk=unit_id)

    @extend_schema(responses=WeaponSerializer(many=True))
    def get(self, request, unit_id):
        unit = self.parent(unit_id)
        weapons = unit.weapons.all()
        if request.query_params.get("include_inactive", "false").lower() != "true":
            weapons = weapons.filter(is_active=True)
        return Response(WeaponSerializer(weapons, many=True, context={"unit": unit}).data)

    @extend_schema(request=WeaponSerializer, responses={201: WeaponSerializer})
    def post(self, request, unit_id):
        unit = self.parent(unit_id)
        serializer = WeaponSerializer(data=request.data, context={"unit": unit})
        serializer.is_valid(raise_exception=True)
        serializer.save(unit=unit)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WeaponDetailView(APIView):
    def objects(self, unit_id, weapon_id):
        unit = get_object_or_404(Unit, pk=unit_id)
        weapon = get_object_or_404(WeaponProfile, pk=weapon_id, unit=unit)
        return unit, weapon

    @extend_schema(responses=WeaponSerializer)
    def get(self, request, unit_id, weapon_id):
        unit, weapon = self.objects(unit_id, weapon_id)
        return Response(WeaponSerializer(weapon, context={"unit": unit}).data)

    @extend_schema(request=WeaponSerializer, responses=WeaponSerializer)
    def patch(self, request, unit_id, weapon_id):
        unit, weapon = self.objects(unit_id, weapon_id)
        serializer = WeaponSerializer(weapon, data=request.data, partial=True, context={"unit": unit})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(responses=WeaponSerializer)
    def delete(self, request, unit_id, weapon_id):
        unit, weapon = self.objects(unit_id, weapon_id)
        weapon.is_active = False
        weapon.save(update_fields=["is_active", "updated_at"])
        return Response(WeaponSerializer(weapon, context={"unit": unit}).data)


class InlineDamageView(APIView):
    @extend_schema(request=InlineDamageSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        try:
            payload = DamageRequest.model_validate(request.data)
        except PydanticValidationError as exc:
            raise ValidationError(exc.errors(include_url=False)) from exc
        return Response(calculate_expected_damage(payload).model_dump())


class StoredDamageView(APIView):
    @extend_schema(request=StoredDamageSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        serializer = StoredDamageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        weapon = get_object_or_404(WeaponProfile.objects.select_related("unit"), pk=data["weapon_profile_id"])
        defender = get_object_or_404(Unit, pk=data["defender_unit_id"])
        if not weapon.is_active or not weapon.unit.is_active or not defender.is_active:
            raise Conflict("Stored profiles must be active to calculate damage.")
        count = data["defender_model_count"]
        if not defender.minimum_model_count <= count <= defender.maximum_model_count:
            raise ValidationError("Defender model count is outside the unit's permitted range.")
        payload = DamageRequest.model_validate({
            "weapon": {"name": weapon.name, "attacks": weapon.attacks * data["weapon_count"], "skill": weapon.skill, "strength": weapon.strength, "armour_penetration": weapon.armour_penetration, "damage": weapon.damage},
            "defender": {"name": defender.name, "toughness": defender.toughness, "save": defender.armour_save, "invulnerable_save": defender.invulnerable_save, "wounds": defender.wounds, "model_count": count},
        })
        result = calculate_expected_damage(payload)
        return Response({
            "attacking_unit": {"id": weapon.unit_id, "name": weapon.unit.name},
            "weapon": {"id": weapon.id, "name": weapon.name, "profile_name": weapon.profile_name},
            "defender": {"id": defender.id, "name": defender.name},
            "weapon_count": data["weapon_count"], "defender_model_count": count,
            "result": result.model_dump(),
        })
