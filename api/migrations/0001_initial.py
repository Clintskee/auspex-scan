from django.db import migrations, models
import django.db.models.deletion
from django.db.models.functions import Lower


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Unit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=100)),
                ("faction", models.CharField(db_index=True, max_length=100)),
                ("movement", models.PositiveSmallIntegerField()), ("toughness", models.PositiveSmallIntegerField()),
                ("armour_save", models.PositiveSmallIntegerField(db_column="save")), ("invulnerable_save", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("wounds", models.PositiveSmallIntegerField()), ("leadership", models.PositiveSmallIntegerField()),
                ("objective_control", models.PositiveSmallIntegerField()), ("minimum_model_count", models.PositiveSmallIntegerField()),
                ("maximum_model_count", models.PositiveSmallIntegerField()), ("points", models.PositiveIntegerField(blank=True, null=True)),
                ("edition", models.PositiveSmallIntegerField(default=11)), ("source", models.CharField(blank=True, max_length=200, null=True)),
                ("source_version", models.CharField(blank=True, max_length=50, null=True)), ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ], options={"ordering": ["name", "id"]},
        ),
        migrations.CreateModel(
            name="WeaponProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=100)), ("profile_name", models.CharField(default="default", max_length=100)),
                ("weapon_type", models.CharField(choices=[("ranged", "Ranged"), ("melee", "Melee")], max_length=10)),
                ("range_inches", models.PositiveSmallIntegerField(blank=True, null=True)), ("attacks", models.PositiveSmallIntegerField()),
                ("skill", models.PositiveSmallIntegerField()), ("strength", models.PositiveSmallIntegerField()),
                ("armour_penetration", models.SmallIntegerField(default=0)), ("damage", models.PositiveSmallIntegerField()),
                ("is_active", models.BooleanField(db_index=True, default=True)), ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("unit", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="weapons", to="api.unit")),
            ], options={"ordering": ["name", "profile_name", "id"]},
        ),
        migrations.AddConstraint(model_name="unit", constraint=models.UniqueConstraint(Lower("name"), Lower("faction"), "edition", name="unique_unit_identity")),
        migrations.AddConstraint(model_name="weaponprofile", constraint=models.UniqueConstraint("unit", Lower("name"), Lower("profile_name"), "weapon_type", name="unique_unit_weapon_identity")),
    ]
