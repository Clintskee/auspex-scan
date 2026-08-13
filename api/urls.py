from django.urls import path

from api.views import InlineDamageView, StoredDamageView, UnitDetailView, UnitListCreateView, WeaponDetailView, WeaponListCreateView

urlpatterns = [
    path("units", UnitListCreateView.as_view()),
    path("units/<int:unit_id>", UnitDetailView.as_view()),
    path("units/<int:unit_id>/weapons", WeaponListCreateView.as_view()),
    path("units/<int:unit_id>/weapons/<int:weapon_id>", WeaponDetailView.as_view()),
    path("expected-damage", InlineDamageView.as_view()),
    path("calculations/expected-damage", StoredDamageView.as_view()),
]
