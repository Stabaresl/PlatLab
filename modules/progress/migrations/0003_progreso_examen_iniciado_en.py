from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("progress", "0002_resultadoexamen"),
    ]

    operations = [
        migrations.AddField(
            model_name="progresomodel",
            name="examen_iniciado_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
