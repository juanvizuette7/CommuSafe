"""Completa una base nueva sin borrar ni sobrescribir datos existentes."""

from datetime import timedelta

from decouple import config
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from asistente.models import ConversacionAsistente, EntradaConocimiento, MensajeAsistente
from incidentes.models import HistorialEstado, Incidente
from notificaciones.models import AvisoProgramado, Notificacion
from notificaciones.services import AudienciaAviso
from usuarios.models import Usuario


USUARIOS_RECONSTRUIDOS = (
    {
        "email": "admin@remansos.com",
        "nombre": "Administrador",
        "apellido": "Remansos",
        "rol": Usuario.Rol.ADMINISTRADOR,
        "unidad_residencial": "Administración",
        "telefono": "+57 300 100 1000",
        "is_staff": True,
        "is_superuser": True,
        "password_key": "RECOVERY_ADMIN_PASSWORD",
        "password_default": "Admin2026*",
    },
    {
        "email": "vigilante1@remansos.com",
        "nombre": "Pedro",
        "apellido": "García",
        "rol": Usuario.Rol.VIGILANTE,
        "unidad_residencial": "Portería principal - turno diurno",
        "telefono": "+57 300 100 1001",
    },
    {
        "email": "vigilante2@remansos.com",
        "nombre": "Luis",
        "apellido": "Martínez",
        "rol": Usuario.Rol.VIGILANTE,
        "unidad_residencial": "Portería vehicular - turno nocturno",
        "telefono": "+57 300 100 1002",
    },
    {
        "email": "residente1@remansos.com",
        "nombre": "María",
        "apellido": "López",
        "rol": Usuario.Rol.RESIDENTE,
        "unidad_residencial": "Apto 101 Torre C",
        "telefono": "+57 300 100 1003",
    },
    {
        "email": "residente2@remansos.com",
        "nombre": "Juan",
        "apellido": "Pérez",
        "rol": Usuario.Rol.RESIDENTE,
        "unidad_residencial": "Apto 204 Torre B",
        "telefono": "+57 300 100 1004",
    },
    {
        "email": "residente3@remansos.com",
        "nombre": "Ana",
        "apellido": "Rodríguez",
        "rol": Usuario.Rol.RESIDENTE,
        "unidad_residencial": "Apto 302 Torre B",
        "telefono": "+57 300 100 1005",
    },
    {
        "email": "residente4@remansos.com",
        "nombre": "Laura",
        "apellido": "Martínez",
        "rol": Usuario.Rol.RESIDENTE,
        "unidad_residencial": "Apto 202 Torre A",
        "telefono": "+57 300 100 1006",
    },
    {
        "email": "residente5@remansos.com",
        "nombre": "Andrés",
        "apellido": "Castro",
        "rol": Usuario.Rol.RESIDENTE,
        "unidad_residencial": "Apto 101 Torre A",
        "telefono": "+57 300 100 1007",
    },
)


INCIDENTES_RECONSTRUIDOS = (
    {
        "titulo": "Música a alto volumen de madrugada",
        "descripcion": (
            "Residentes reportan música a alto volumen desde el apartamento 302 de la Torre B "
            "hasta las 2:00 a. m. Se intentó tocar la puerta en varias ocasiones y no atendieron."
        ),
        "categoria": Incidente.Categoria.CONVIVENCIA,
        "estado": Incidente.Estado.RESUELTO,
        "ubicacion": "Apartamento 302 Torre B",
        "reportante": "residente3@remansos.com",
        "responsable": "vigilante1@remansos.com",
        "dias": 6,
        "historial": (
            (
                Incidente.Estado.REGISTRADO,
                Incidente.Estado.EN_PROCESO,
                "Vigilancia realiza visita al piso y deja registro del ruido reportado por vecinos.",
            ),
            (
                Incidente.Estado.EN_PROCESO,
                Incidente.Estado.RESUELTO,
                "Se contactó al residente responsable, se dejó advertencia formal y no se repitió el ruido.",
            ),
        ),
    },
    {
        "titulo": "Falla de iluminación en calle interna",
        "descripcion": (
            "Se observan tres postes de luz seguidos apagados en la calle interna entre el "
            "parqueadero y la Torre C, generando baja visibilidad."
        ),
        "categoria": Incidente.Categoria.INFRAESTRUCTURA,
        "estado": Incidente.Estado.REGISTRADO,
        "ubicacion": "Calle interna entre parqueadero y Torre C",
        "reportante": "residente1@remansos.com",
        "responsable": "",
        "dias": 4,
        "historial": (),
    },
    {
        "titulo": "Cerraduras vandalizadas",
        "descripcion": (
            "Se evidencian varias cerraduras dañadas intencionalmente en los cuartos de depósito "
            "del parqueadero cubierto de la Torre B."
        ),
        "categoria": Incidente.Categoria.SEGURIDAD,
        "estado": Incidente.Estado.REGISTRADO,
        "ubicacion": "Parqueadero cubierto Torre B",
        "reportante": "residente2@remansos.com",
        "responsable": "",
        "dias": 2,
        "historial": (),
    },
    {
        "titulo": "Olor fuerte a gas",
        "descripcion": (
            "Se percibe olor a gas en el pasillo del piso 2 de la Torre A. El olor aumenta cerca "
            "del ducto de servicios y varios residentes solicitan revisión inmediata."
        ),
        "categoria": Incidente.Categoria.EMERGENCIA,
        "estado": Incidente.Estado.EN_PROCESO,
        "ubicacion": "Pasillo piso 2 Torre A",
        "reportante": "residente4@remansos.com",
        "responsable": "vigilante1@remansos.com",
        "dias": 1,
        "historial": (
            (
                Incidente.Estado.REGISTRADO,
                Incidente.Estado.EN_PROCESO,
                "Vigilancia acordona el pasillo, ventila la zona y solicita revisión técnica inmediata.",
            ),
        ),
    },
)


class Command(BaseCommand):
    help = "Reconstruye datos mínimos verificables sin borrar ni sobrescribir registros existentes."

    @transaction.atomic
    def handle(self, *args, **options):
        usuarios, usuarios_creados = self._crear_usuarios_faltantes()
        incidentes_creados, historiales_creados = self._crear_incidentes_faltantes(usuarios)
        avisos_creados, notificaciones_creadas = self._crear_aviso_faltante(usuarios)
        conversaciones_creadas, mensajes_creados = self._crear_conversacion_faltante(usuarios)

        call_command(
            "sincronizar_base_conocimiento",
            usuario=usuarios["admin@remansos.com"].email,
            verbosity=0,
        )

        self.stdout.write(self.style.SUCCESS("Reconstrucción idempotente completada."))
        self.stdout.write(f"Motor activo: {connection.vendor}")
        self.stdout.write(f"Usuarios creados: {usuarios_creados}; total: {Usuario.objects.count()}")
        self.stdout.write(f"Incidentes creados: {incidentes_creados}; total: {Incidente.objects.count()}")
        self.stdout.write(
            f"Historiales creados: {historiales_creados}; total: {HistorialEstado.objects.count()}"
        )
        self.stdout.write(f"Avisos creados: {avisos_creados}; total: {AvisoProgramado.objects.count()}")
        self.stdout.write(
            f"Notificaciones creadas: {notificaciones_creadas}; total: {Notificacion.objects.count()}"
        )
        self.stdout.write(
            f"Conversaciones creadas: {conversaciones_creadas}; "
            f"mensajes creados: {mensajes_creados}"
        )
        self.stdout.write(f"Conocimiento administrable: {EntradaConocimiento.objects.count()}")

    def _crear_usuarios_faltantes(self):
        usuarios = {}
        creados = 0
        password_usuarios = config("RECOVERY_USER_PASSWORD", default="Commu2026*")

        for datos in USUARIOS_RECONSTRUIDOS:
            defaults = {
                "nombre": datos["nombre"],
                "apellido": datos["apellido"],
                "rol": datos["rol"],
                "unidad_residencial": datos["unidad_residencial"],
                "telefono": datos["telefono"],
                "activo": True,
                "is_staff": datos.get("is_staff", False),
                "is_superuser": datos.get("is_superuser", False),
            }
            usuario, creado = Usuario.objects.get_or_create(email=datos["email"], defaults=defaults)
            if creado:
                password = config(
                    datos.get("password_key", "RECOVERY_USER_PASSWORD"),
                    default=datos.get("password_default", password_usuarios),
                )
                usuario.set_password(password)
                usuario.save(update_fields=["password"])
                creados += 1
            usuarios[datos["email"]] = usuario

        return usuarios, creados

    def _crear_incidentes_faltantes(self, usuarios):
        ahora = timezone.now()
        incidentes_creados = 0
        historiales_creados = 0

        for posicion, datos in enumerate(INCIDENTES_RECONSTRUIDOS):
            reportante = usuarios[datos["reportante"]]
            responsable = usuarios.get(datos["responsable"])
            defaults = {
                "descripcion": datos["descripcion"],
                "categoria": datos["categoria"],
                "estado": datos["estado"],
                "ubicacion_referencia": datos["ubicacion"],
                "atendido_por": responsable,
                "observaciones_cierre": (
                    "Caso resuelto con seguimiento de convivencia."
                    if datos["estado"] == Incidente.Estado.RESUELTO
                    else ""
                ),
            }
            incidente, creado = Incidente.objects.get_or_create(
                titulo=datos["titulo"],
                reportado_por=reportante,
                defaults=defaults,
            )
            if creado:
                fecha = ahora - timedelta(days=datos["dias"], hours=posicion + 1)
                cierre = fecha + timedelta(hours=4) if datos["estado"] == Incidente.Estado.RESUELTO else None
                Incidente.objects.filter(pk=incidente.pk).update(
                    fecha_reporte=fecha,
                    fecha_actualizacion=cierre or fecha,
                    fecha_cierre=cierre,
                )
                incidente.refresh_from_db()
                incidentes_creados += 1

            for indice, (anterior, nuevo, comentario) in enumerate(datos["historial"], start=1):
                historial, historial_creado = HistorialEstado.objects.get_or_create(
                    incidente=incidente,
                    estado_anterior=anterior,
                    estado_nuevo=nuevo,
                    defaults={
                        "comentario": comentario,
                        "cambiado_por": responsable or usuarios["admin@remansos.com"],
                    },
                )
                if historial_creado:
                    HistorialEstado.objects.filter(pk=historial.pk).update(
                        fecha_cambio=incidente.fecha_reporte + timedelta(hours=indice)
                    )
                    historiales_creados += 1

            self._crear_notificaciones_incidente(incidente, usuarios)

        return incidentes_creados, historiales_creados

    @staticmethod
    def _crear_notificaciones_incidente(incidente, usuarios):
        titulo = f"Nuevo incidente reportado: {incidente.titulo}"
        cuerpo = (
            f"Se registró un incidente de categoría {incidente.get_categoria_display().lower()} "
            f"con prioridad {incidente.get_prioridad_display().lower()}."
        )
        tipo = (
            Notificacion.Tipo.EMERGENCIA
            if incidente.prioridad == Incidente.Prioridad.ALTA
            else Notificacion.Tipo.INCIDENTE_NUEVO
        )
        destinatarios = [
            usuario
            for usuario in usuarios.values()
            if usuario.activo
            and usuario.pk != incidente.reportado_por_id
            and (
                usuario.rol in {Usuario.Rol.ADMINISTRADOR, Usuario.Rol.VIGILANTE}
                or (incidente.prioridad == Incidente.Prioridad.ALTA and usuario.es_residente)
            )
        ]
        for destinatario in destinatarios:
            Notificacion.objects.get_or_create(
                destinatario=destinatario,
                titulo=titulo,
                incidente_relacionado=incidente,
                defaults={"cuerpo": cuerpo, "tipo": tipo},
            )

        for historial in incidente.historial.all():
            estado = dict(Incidente.Estado.choices)[historial.estado_nuevo].lower()
            for destinatario in {incidente.reportado_por, incidente.atendido_por} - {None}:
                Notificacion.objects.get_or_create(
                    destinatario=destinatario,
                    titulo=f"Actualización del incidente: {incidente.titulo}",
                    cuerpo=f"El incidente ahora se encuentra en estado {estado}.",
                    incidente_relacionado=incidente,
                    defaults={"tipo": Notificacion.Tipo.CAMBIO_ESTADO},
                )

    @staticmethod
    def _crear_aviso_faltante(usuarios):
        admin = usuarios["admin@remansos.com"]
        titulo = "Recordatorio de disposición de residuos"
        cuerpo = (
            "Se recuerda a la comunidad disponer los residuos en los horarios informados por "
            "administración y mantener limpia la zona común."
        )
        _, creado = AvisoProgramado.objects.get_or_create(
            titulo=titulo,
            creado_por=admin,
            defaults={
                "cuerpo": cuerpo,
                "tipo": Notificacion.Tipo.AVISO_ADMIN,
                "audiencia": AudienciaAviso.TODOS,
                "dias_semana": "2,4",
                "activo": True,
            },
        )
        creadas = 0
        for usuario in usuarios.values():
            _, notificacion_creada = Notificacion.objects.get_or_create(
                destinatario=usuario,
                titulo=titulo,
                incidente_relacionado=None,
                defaults={"cuerpo": cuerpo, "tipo": Notificacion.Tipo.AVISO_ADMIN},
            )
            creadas += int(notificacion_creada)
        return int(creado), creadas

    @staticmethod
    def _crear_conversacion_faltante(usuarios):
        residente = usuarios["residente1@remansos.com"]
        conversacion, creada = ConversacionAsistente.objects.get_or_create(
            usuario=residente,
            titulo="Guía inicial de CommuSafe (demostración)",
        )
        mensajes = (
            (MensajeAsistente.Rol.USUARIO, "¿Cómo reporto un incidente desde CommuSafe?"),
            (
                MensajeAsistente.Rol.ASISTENTE,
                "En Incidentes, selecciona Nuevo, completa categoría, descripción y ubicación, "
                "adjunta evidencia si la tienes y confirma el reporte.",
            ),
        )
        mensajes_creados = 0
        for rol, contenido in mensajes:
            _, mensaje_creado = MensajeAsistente.objects.get_or_create(
                conversacion=conversacion,
                rol=rol,
                contenido=contenido,
            )
            mensajes_creados += int(mensaje_creado)
        return int(creada), mensajes_creados
