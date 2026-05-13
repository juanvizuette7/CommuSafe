from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0002_passwordresettoken"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="politica_privacidad_aceptada",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="usuario",
            name="politica_privacidad_aceptada_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
