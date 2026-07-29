import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TemaModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("nombre", models.CharField(max_length=100, unique=True)),
            ],
            options={
                "db_table": "laboratories_tema",
            },
        ),
        migrations.CreateModel(
            name="LaboratorioModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("nombre", models.CharField(max_length=200)),
                ("descripcion", models.TextField()),
                (
                    "nivel_dificultad",
                    models.CharField(
                        choices=[
                            ("basico", "Básico"),
                            ("intermedio", "Intermedio"),
                            ("avanzado", "Avanzado"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "estado",
                    models.CharField(
                        choices=[("borrador", "Borrador"), ("publicado", "Publicado")],
                        default="borrador",
                        max_length=20,
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("predeterminado", "Predeterminado"),
                            ("personalizado", "Personalizado"),
                        ],
                        max_length=20,
                    ),
                ),
                ("instructor_id", models.UUIDField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "origen",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="copias",
                        to="laboratories.laboratoriomodel",
                    ),
                ),
                (
                    "temas",
                    models.ManyToManyField(
                        blank=True,
                        db_table="laboratories_laboratorio_tema",
                        related_name="laboratorios",
                        to="laboratories.temamodel",
                    ),
                ),
            ],
            options={
                "db_table": "laboratories_laboratorio",
            },
        ),
        migrations.CreateModel(
            name="SeccionModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("titulo", models.CharField(max_length=200)),
                ("contenido_teorico", models.TextField()),
                ("orden", models.PositiveIntegerField()),
                ("tiene_practica", models.BooleanField(default=False)),
                (
                    "laboratorio",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="secciones",
                        to="laboratories.laboratoriomodel",
                    ),
                ),
            ],
            options={
                "db_table": "laboratories_seccion",
                "ordering": ["orden"],
            },
        ),
        migrations.AddIndex(
            model_name="laboratoriomodel",
            index=models.Index(
                fields=["estado", "nivel_dificultad"], name="idx_lab_estado_dificultad"
            ),
        ),
        migrations.AddIndex(
            model_name="laboratoriomodel",
            index=models.Index(
                fields=["tipo", "instructor_id"], name="idx_lab_tipo_instructor"
            ),
        ),
        migrations.AddConstraint(
            model_name="laboratoriomodel",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("instructor_id__isnull", True), ("tipo", "predeterminado")),
                    models.Q(("tipo", "predeterminado"), _negated=True),
                    _connector="OR",
                ),
                name="ck_lab_predet_sin_instructor",
            ),
        ),
        migrations.AddConstraint(
            model_name="laboratoriomodel",
            constraint=models.CheckConstraint(
                condition=models.Q(("tipo", "personalizado"))
                | models.Q(("origen__isnull", True)),
                name="ck_lab_origen_si_personalizado",
            ),
        ),
        migrations.AddConstraint(
            model_name="seccionmodel",
            constraint=models.UniqueConstraint(
                fields=("laboratorio", "orden"), name="uq_seccion_laboratorio_orden"
            ),
        ),
    ]
