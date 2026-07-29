import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("laboratories", "0002_flag"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExamenModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "laboratorio",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="examen",
                        to="laboratories.laboratoriomodel",
                    ),
                ),
            ],
            options={
                "db_table": "laboratories_examen",
            },
        ),
        migrations.CreateModel(
            name="PreguntaModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("enunciado", models.TextField()),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("opcion_multiple", "Opción múltiple"),
                            ("abierta", "Abierta"),
                        ],
                        max_length=20,
                    ),
                ),
                ("opciones", models.JSONField(blank=True, null=True)),
                ("respuesta_hash", models.CharField(max_length=255)),
                (
                    "examen",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="preguntas",
                        to="laboratories.examenmodel",
                    ),
                ),
            ],
            options={
                "db_table": "laboratories_pregunta",
            },
        ),
    ]
