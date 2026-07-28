import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("laboratories", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FlagModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("hash", models.CharField(max_length=255)),
                ("pista_texto", models.TextField(blank=True, null=True)),
                ("paso_a_paso_texto", models.TextField(blank=True, null=True)),
                (
                    "seccion",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="flag",
                        to="laboratories.seccionmodel",
                    ),
                ),
            ],
            options={
                "db_table": "laboratories_flag",
            },
        ),
    ]
