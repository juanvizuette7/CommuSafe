"""Prepara una base limpia con incidentes reales para la presentacion."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from incidentes.models import EvidenciaIncidente, HistorialEstado, Incidente, IncidenteEliminado
from incidentes.services import cambiar_estado_incidente
from notificaciones.models import AvisoProgramado, Notificacion
from notificaciones.services import notificar_cambio_estado, notificar_incidente_nuevo
from usuarios.models import Usuario


PASSWORD_RESIDENTE = "Commu2026*"
PASSWORD_ADMIN = "Admin2026*"


class Command(BaseCommand):
    help = "Limpia los datos operativos y carga cuatro incidentes reales de lanzamiento."

    def handle(self, *args, **options):
        with transaction.atomic():
            eliminados = self._limpiar_datos_operativos()
            usuarios_creados, usuarios_actualizados = self._preparar_usuarios()
            incidentes = self._crear_incidentes_lanzamiento()

        self._imprimir_resumen(eliminados, usuarios_creados, usuarios_actualizados, incidentes)

    def _limpiar_datos_operativos(self):
        modelos = [
            ("avisos_programados", AvisoProgramado),
            ("notificaciones", Notificacion),
            ("historiales", HistorialEstado),
            ("evidencias", EvidenciaIncidente),
            ("incidentes_eliminados", IncidenteEliminado),
            ("incidentes", Incidente),
        ]
        resultado = {}
        for nombre, modelo in modelos:
            total, _ = modelo.objects.all().delete()
            resultado[nombre] = total
        return resultado

    def _crear_usuario_si_no_existe(self, email, password, **datos):
        usuario, creado = Usuario.objects.get_or_create(email=email.lower(), defaults=datos)
        if creado:
            usuario.set_password(password)
            usuario.save()
        return usuario, creado

    def _preparar_usuarios(self):
        usuarios_requeridos = [
            (
                "admin@remansos.com",
                PASSWORD_ADMIN,
                {
                    "nombre": "Administrador",
                    "apellido": "Remansos",
                    "rol": Usuario.Rol.ADMINISTRADOR,
                    "unidad_residencial": "Administracion",
                    "telefono": "+57 300 100 1000",
                    "activo": True,
                    "is_staff": True,
                    "is_superuser": True,
                },
            ),
            (
                "vigilante1@remansos.com",
                PASSWORD_RESIDENTE,
                {
                    "nombre": "Pedro",
                    "apellido": "Garcia",
                    "rol": Usuario.Rol.VIGILANTE,
                    "unidad_residencial": "Porteria principal - turno diurno",
                    "telefono": "+57 300 100 1001",
                    "activo": True,
                    "is_staff": False,
                },
            ),
            (
                "vigilante2@remansos.com",
                PASSWORD_RESIDENTE,
                {
                    "nombre": "Luis",
                    "apellido": "Martinez",
                    "rol": Usuario.Rol.VIGILANTE,
                    "unidad_residencial": "Porteria vehicular - turno nocturno",
                    "telefono": "+57 300 100 1002",
                    "activo": True,
                    "is_staff": False,
                },
            ),
            (
                "residente1@remansos.com",
                PASSWORD_RESIDENTE,
                {
                    "nombre": "Maria",
                    "apellido": "Lopez",
                    "rol": Usuario.Rol.RESIDENTE,
                    "unidad_residencial": "Apto 101 Torre C",
                    "telefono": "+57 300 100 1003",
                    "activo": True,
                    "is_staff": False,
                },
            ),
            (
                "residente2@remansos.com",
                PASSWORD_RESIDENTE,
                {
                    "nombre": "Juan",
                    "apellido": "Perez",
                    "rol": Usuario.Rol.RESIDENTE,
                    "unidad_residencial": "Apto 204 Torre B",
                    "telefono": "+57 300 100 1004",
                    "activo": True,
                    "is_staff": False,
                },
            ),
            (
                "residente3@remansos.com",
                PASSWORD_RESIDENTE,
                {
                    "nombre": "Ana",
                    "apellido": "Rodriguez",
                    "rol": Usuario.Rol.RESIDENTE,
                    "unidad_residencial": "Apto 302 Torre B",
                    "telefono": "+57 300 100 1005",
                    "activo": True,
                    "is_staff": False,
                },
            ),
            (
                "residente4@remansos.com",
                PASSWORD_RESIDENTE,
                {
                    "nombre": "Laura",
                    "apellido": "Martinez",
                    "rol": Usuario.Rol.RESIDENTE,
                    "unidad_residencial": "Apto 202 Torre A",
                    "telefono": "+57 300 100 1006",
                    "activo": True,
                    "is_staff": False,
                },
            ),
        ]

        creados = 0
        for email, password, datos in usuarios_requeridos:
            _, creado = self._crear_usuario_si_no_existe(email, password, **datos)
            creados += int(creado)

        unidades_residentes = {
            "residente1@remansos.com": "Apto 101 Torre C",
            "residente2@remansos.com": "Apto 204 Torre B",
            "residente3@remansos.com": "Apto 302 Torre B",
            "residente4@remansos.com": "Apto 202 Torre A",
        }
        unidades_genericas = [
            "Apto 101 Torre A",
            "Apto 305 Torre A",
            "Apto 402 Torre B",
            "Apto 503 Torre C",
            "Apto 604 Torre C",
        ]
        telefonos = [
            "+57 300 100 1010",
            "+57 300 100 1011",
            "+57 300 100 1012",
            "+57 300 100 1013",
            "+57 300 100 1014",
        ]

        actualizados = 0
        residentes_extra = 0
        for usuario in Usuario.objects.all().order_by("email"):
            campos = []
            if usuario.rol == Usuario.Rol.ADMINISTRADOR:
                if usuario.unidad_residencial != "Administracion":
                    usuario.unidad_residencial = "Administracion"
                    campos.append("unidad_residencial")
                if not usuario.is_staff:
                    usuario.is_staff = True
                    campos.append("is_staff")
            elif usuario.rol == Usuario.Rol.VIGILANTE:
                unidad = (
                    "Porteria principal - turno diurno"
                    if "1" in usuario.email
                    else "Porteria vehicular - turno nocturno"
                )
                if usuario.unidad_residencial != unidad:
                    usuario.unidad_residencial = unidad
                    campos.append("unidad_residencial")
            elif usuario.rol == Usuario.Rol.RESIDENTE:
                unidad = unidades_residentes.get(usuario.email)
                if unidad is None:
                    unidad = unidades_genericas[residentes_extra % len(unidades_genericas)]
                    residentes_extra += 1
                if usuario.unidad_residencial != unidad:
                    usuario.unidad_residencial = unidad
                    campos.append("unidad_residencial")

            if not usuario.telefono:
                usuario.telefono = telefonos[actualizados % len(telefonos)]
                campos.append("telefono")

            if campos:
                usuario.save(update_fields=sorted(set(campos)))
                actualizados += 1

        return creados, actualizados

    def _crear_incidentes_lanzamiento(self):
        ahora = timezone.now()
        residente1 = Usuario.objects.get(email="residente1@remansos.com")
        residente2 = Usuario.objects.get(email="residente2@remansos.com")
        residente3 = Usuario.objects.get(email="residente3@remansos.com")
        residente4 = Usuario.objects.get(email="residente4@remansos.com")
        vigilante = Usuario.objects.filter(rol=Usuario.Rol.VIGILANTE, activo=True).order_by("email").first()
        administrador = Usuario.objects.filter(rol=Usuario.Rol.ADMINISTRADOR, activo=True).order_by("email").first()

        creados = []

        convivencia = self._crear_incidente(
            titulo="Música a alto volumen de madrugada",
            descripcion=(
                "Residentes reportan música a alto volumen desde el apartamento 302 de la Torre B "
                "hasta las 2:00 a. m. Se intentó tocar la puerta en varias ocasiones y no atendieron."
            ),
            categoria=Incidente.Categoria.CONVIVENCIA,
            ubicacion="Apartamento 302 Torre B",
            reportado_por=residente3,
            fecha=ahora - timedelta(days=6, hours=2),
        )
        self._cambiar_estado(
            convivencia,
            Incidente.Estado.EN_PROCESO,
            "Vigilancia realiza visita al piso y deja registro del ruido reportado por vecinos.",
            vigilante,
            ahora - timedelta(days=6, hours=1, minutes=20),
        )
        self._cambiar_estado(
            convivencia,
            Incidente.Estado.RESUELTO,
            "Se contacto al residente responsable, se dejo advertencia formal y no se repitio el ruido.",
            administrador or vigilante,
            ahora - timedelta(days=5, hours=10),
        )
        Incidente.objects.filter(id=convivencia.id).update(
            fecha_cierre=ahora - timedelta(days=5, hours=10),
            observaciones_cierre="Caso resuelto con llamado de atencion y compromiso de convivencia.",
            fecha_actualizacion=ahora - timedelta(days=5, hours=10),
        )
        creados.append(convivencia.id)

        infraestructura = self._crear_incidente(
            titulo="Falla de iluminación en calle interna",
            descripcion=(
                "Se observan tres postes de luz seguidos apagados en la calle interna entre el "
                "parqueadero y la Torre C, generando baja visibilidad para peatones y vehículos."
            ),
            categoria=Incidente.Categoria.INFRAESTRUCTURA,
            ubicacion="Calle interna entre parqueadero y Torre C",
            reportado_por=residente1,
            fecha=ahora - timedelta(days=4, hours=4),
        )
        creados.append(infraestructura.id)

        seguridad = self._crear_incidente(
            titulo="Cerraduras vandalizadas",
            descripcion=(
                "Se evidencian varias cerraduras dañadas intencionalmente en los cuartos de depósito "
                "del parqueadero cubierto de la Torre B. Se solicita revisión preventiva."
            ),
            categoria=Incidente.Categoria.SEGURIDAD,
            ubicacion="Parqueadero cubierto Torre B",
            reportado_por=residente2,
            fecha=ahora - timedelta(days=2, hours=6),
        )
        creados.append(seguridad.id)

        emergencia = self._crear_incidente(
            titulo="Olor fuerte a gas",
            descripcion=(
                "Se percibe olor a gas en el pasillo del piso 2 de la Torre A. El olor aumenta cerca "
                "del ducto de servicios y varios residentes solicitan revisión inmediata."
            ),
            categoria=Incidente.Categoria.EMERGENCIA,
            ubicacion="Pasillo piso 2 Torre A",
            reportado_por=residente4,
            fecha=ahora - timedelta(hours=20),
        )
        self._cambiar_estado(
            emergencia,
            Incidente.Estado.EN_PROCESO,
            "Vigilancia acordona el pasillo, ventila la zona y solicita revision tecnica inmediata.",
            vigilante,
            ahora - timedelta(hours=19, minutes=20),
        )
        creados.append(emergencia.id)

        return creados

    def _crear_incidente(self, *, titulo, descripcion, categoria, ubicacion, reportado_por, fecha):
        incidente = Incidente.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            categoria=categoria,
            estado=Incidente.Estado.REGISTRADO,
            ubicacion_referencia=ubicacion,
            reportado_por=reportado_por,
        )
        Incidente.objects.filter(id=incidente.id).update(fecha_reporte=fecha, fecha_actualizacion=fecha)
        incidente.refresh_from_db()

        inicio_notificaciones = timezone.now()
        notificar_incidente_nuevo(incidente)
        self._fechar_notificaciones(incidente, fecha + timedelta(minutes=5), inicio_notificaciones)
        return incidente

    def _cambiar_estado(self, incidente, estado_nuevo, comentario, usuario, fecha):
        incidente.refresh_from_db()
        incidente, historial = cambiar_estado_incidente(
            incidente=incidente,
            estado_nuevo=estado_nuevo,
            comentario=comentario,
            usuario=usuario,
        )
        HistorialEstado.objects.filter(id=historial.id).update(fecha_cambio=fecha)
        Incidente.objects.filter(id=incidente.id).update(fecha_actualizacion=fecha)
        incidente.refresh_from_db()

        inicio_notificaciones = timezone.now()
        notificar_cambio_estado(incidente, estado_nuevo)
        self._fechar_notificaciones(incidente, fecha + timedelta(minutes=2), inicio_notificaciones)
        return incidente

    def _fechar_notificaciones(self, incidente, fecha, inicio):
        Notificacion.objects.filter(
            incidente_relacionado=incidente,
            fecha_envio__gte=inicio,
        ).update(fecha_envio=fecha)

    def _imprimir_resumen(self, eliminados, usuarios_creados, usuarios_actualizados, incidentes):
        self.stdout.write(self.style.SUCCESS("Base operativa limpiada y datos de lanzamiento cargados."))
        self.stdout.write(f"Base de datos: {connection.vendor} / {connection.settings_dict.get('NAME')}")
        self.stdout.write("Registros eliminados:")
        for nombre, total in eliminados.items():
            self.stdout.write(f"  - {nombre}: {total}")

        self.stdout.write("Registros preparados:")
        self.stdout.write(f"  - usuarios creados: {usuarios_creados}")
        self.stdout.write(f"  - usuarios actualizados: {usuarios_actualizados}")
        self.stdout.write(f"  - incidentes creados: {len(incidentes)}")
        self.stdout.write(f"  - historiales creados: {HistorialEstado.objects.count()}")
        self.stdout.write(f"  - evidencias creadas: {EvidenciaIncidente.objects.count()}")
        self.stdout.write(f"  - incidentes eliminados: {IncidenteEliminado.objects.count()}")
        self.stdout.write(f"  - notificaciones creadas: {Notificacion.objects.count()}")
        self.stdout.write("Incidentes activos:")
        for incidente in Incidente.objects.select_related("reportado_por").order_by("fecha_reporte"):
            fecha = timezone.localtime(incidente.fecha_reporte).strftime("%Y-%m-%d %H:%M")
            self.stdout.write(
                "  - "
                f"{incidente.categoria} | {incidente.prioridad} | {incidente.estado} | "
                f"{incidente.titulo} | {incidente.reportado_por.email} | {fecha}"
            )
