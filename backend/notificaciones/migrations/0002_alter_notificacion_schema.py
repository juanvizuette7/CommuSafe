from django.db import migrations, models
import django.db.models.deletion


def migrar_tipos_notificacion(apps, schema_editor):
    Notificacion = apps.get_model("notificaciones", "Notificacion")
    equivalencias = {
        "INCIDENTE": "CAMBIO_ESTADO",
        "SISTEMA": "AVISO_ADMIN",
        "RECORDATORIO": "AVISO_ADMIN",
        "ALERTA": "EMERGENCIA",
    }
    for anterior, nuevo in equivalencias.items():
        Notificacion.objects.filter(tipo=anterior).update(tipo=nuevo)


class Migration(migrations.Migration):

    dependencies = [
        ("incidentes", "0001_initial"),
        ("notificaciones", "0001_initial"),
        ("usuarios", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="notificacion",
            old_name="usuario",
            new_name="destinatario",
        ),
        migrations.RenameField(
            model_name="notificacion",
            old_name="mensaje",
            new_name="cuerpo",
        ),
        migrations.RenameField(
            model_name="notificacion",
            old_name="incidente",
            new_name="incidente_relacionado",
        ),
        migrations.RenameField(
            model_name="notificacion",
            old_name="creada_en",
            new_name="fecha_envio",
        ),
        migrations.RemoveField(
            model_name="notificacion",
            name="leida_en",
        ),
        migrations.AlterField(
            model_name="notificacion",
            name="destinatario",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="notificaciones",
                to="usuarios.usuario",
            ),
        ),
        migrations.AlterField(
            model_name="notificacion",
            name="incidente_relacionado",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="notificaciones",
                to="incidentes.incidente",
            ),
        ),
        migrations.AlterField(
            model_name="notificacion",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("INCIDENTE_NUEVO", "Incidente nuevo"),
                    ("CAMBIO_ESTADO", "Cambio de estado"),
                    ("AVISO_ADMIN", "Aviso administrativo"),
                    ("EMERGENCIA", "Emergencia"),
                ],
                max_length=20,
            ),
        ),
        migrations.RunPython(migrar_tipos_notificacion, migrations.RunPython.noop),
        migrations.AlterModelOptions(
            name="notificacion",
            options={
                "ordering": ("-fecha_envio",),
                "verbose_name": "Notificación",
                "verbose_name_plural": "Notificaciones",
            },
        ),
    ]
