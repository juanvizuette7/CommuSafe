from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageDraw

from incidentes.models import EvidenciaIncidente, HistorialEstado, Incidente
from incidentes.services import cambiar_estado_incidente
from notificaciones.models import Notificacion
from usuarios.models import Usuario


USUARIOS_DEMO = [
    {
        "email": "admin@remansos.com",
        "password": "Admin2026*",
        "nombre": "Carlos",
        "apellido": "Gonzalez",
        "rol": Usuario.Rol.ADMINISTRADOR,
        "unidad_residencial": "Administracion",
        "is_staff": True,
    },
    {
        "email": "vigilante1@remansos.com",
        "password": "Commu2026*",
        "nombre": "Pedro",
        "apellido": "Garcia",
        "rol": Usuario.Rol.VIGILANTE,
        "unidad_residencial": "Porteria principal",
    },
    {
        "email": "vigilante2@remansos.com",
        "password": "Commu2026*",
        "nombre": "Luis",
        "apellido": "Martinez",
        "rol": Usuario.Rol.VIGILANTE,
        "unidad_residencial": "Porteria norte",
    },
    {
        "email": "residente1@remansos.com",
        "password": "Commu2026*",
        "nombre": "Maria",
        "apellido": "Lopez",
        "rol": Usuario.Rol.RESIDENTE,
        "unidad_residencial": "Apto 101 Torre A",
    },
    {
        "email": "residente2@remansos.com",
        "password": "Commu2026*",
        "nombre": "Juan",
        "apellido": "Perez",
        "rol": Usuario.Rol.RESIDENTE,
        "unidad_residencial": "Apto 202 Torre B",
    },
    {
        "email": "residente3@remansos.com",
        "password": "Commu2026*",
        "nombre": "Ana",
        "apellido": "Rodriguez",
        "rol": Usuario.Rol.RESIDENTE,
        "unidad_residencial": "Apto 305 Torre A",
    },
    {
        "email": "residente4@remansos.com",
        "password": "Commu2026*",
        "nombre": "Sofia",
        "apellido": "Ramirez",
        "rol": Usuario.Rol.RESIDENTE,
        "unidad_residencial": "Apto 410 Torre C",
    },
    {
        "email": "residente5@remansos.com",
        "password": "Commu2026*",
        "nombre": "Andres",
        "apellido": "Castro",
        "rol": Usuario.Rol.RESIDENTE,
        "unidad_residencial": "Casa 12",
    },
]


INCIDENTES_DEMO = [
    {
        "titulo": "Vehiculo sin autorizacion en parqueadero",
        "descripcion": "Se identifica un vehiculo sin registro visible ocupando un espacio asignado a residentes.",
        "categoria": Incidente.Categoria.SEGURIDAD,
        "estado": Incidente.Estado.EN_PROCESO,
        "ubicacion": "Parqueadero sotano 1",
        "reportante": "residente1@remansos.com",
        "responsable": "vigilante1@remansos.com",
        "comentarios": ["Vigilancia verifica placa y contacta a porteria."],
    },
    {
        "titulo": "Ruido nocturno en apartamento 302",
        "descripcion": "Vecinos reportan musica alta despues del horario de descanso establecido.",
        "categoria": Incidente.Categoria.CONVIVENCIA,
        "estado": Incidente.Estado.REGISTRADO,
        "ubicacion": "Apto 302 Torre B",
        "reportante": "residente2@remansos.com",
    },
    {
        "titulo": "Fuga de agua en pasillo Torre A",
        "descripcion": "Hay acumulacion de agua cerca del ducto tecnico del tercer piso.",
        "categoria": Incidente.Categoria.INFRAESTRUCTURA,
        "estado": Incidente.Estado.RESUELTO,
        "ubicacion": "Pasillo piso 3 Torre A",
        "reportante": "residente3@remansos.com",
        "responsable": "vigilante2@remansos.com",
        "comentarios": [
            "Se delimita el area para prevenir caidas.",
            "Mantenimiento corrige la fuga y seca el pasillo.",
        ],
    },
    {
        "titulo": "Persona sospechosa en zona verde",
        "descripcion": "Un residente observa a una persona desconocida merodeando cerca del cerramiento.",
        "categoria": Incidente.Categoria.SEGURIDAD,
        "estado": Incidente.Estado.EN_PROCESO,
        "ubicacion": "Zona verde oriental",
        "reportante": "residente4@remansos.com",
        "responsable": "vigilante1@remansos.com",
        "comentarios": ["Se realiza ronda preventiva y verificacion presencial en el sector."],
    },
    {
        "titulo": "Luminaria danada en calle interna",
        "descripcion": "La luminaria principal de la calle interna no enciende en horario nocturno.",
        "categoria": Incidente.Categoria.INFRAESTRUCTURA,
        "estado": Incidente.Estado.REGISTRADO,
        "ubicacion": "Calle interna frente a Torre C",
        "reportante": "residente5@remansos.com",
    },
    {
        "titulo": "Puerta de acceso principal con falla",
        "descripcion": "La puerta peatonal principal no cierra correctamente y queda vulnerable.",
        "categoria": Incidente.Categoria.SEGURIDAD,
        "estado": Incidente.Estado.RESUELTO,
        "ubicacion": "Acceso peatonal principal",
        "reportante": "residente1@remansos.com",
        "responsable": "vigilante2@remansos.com",
        "comentarios": [
            "Vigilancia mantiene control manual del acceso.",
            "Proveedor ajusta el brazo de cierre y valida funcionamiento.",
        ],
    },
    {
        "titulo": "Mascotas sueltas en zona comun",
        "descripcion": "Dos mascotas permanecen sin correa en la zona comun y generan molestia a otros residentes.",
        "categoria": Incidente.Categoria.CONVIVENCIA,
        "estado": Incidente.Estado.EN_PROCESO,
        "ubicacion": "Zona comun frente al salon social",
        "reportante": "residente2@remansos.com",
        "responsable": "vigilante1@remansos.com",
        "comentarios": ["Se informa a los propietarios sobre el uso obligatorio de correa."],
    },
    {
        "titulo": "Intento de ingreso por reja norte",
        "descripcion": "Se reporta intento de ingreso no autorizado por el cerramiento norte.",
        "categoria": Incidente.Categoria.EMERGENCIA,
        "estado": Incidente.Estado.EN_PROCESO,
        "ubicacion": "Reja norte",
        "reportante": "residente3@remansos.com",
        "responsable": "vigilante2@remansos.com",
        "comentarios": ["Vigilancia acude al punto y refuerza rondas en el sector."],
    },
    {
        "titulo": "Incendio pequeno en caneca",
        "descripcion": "Se detecta humo y fuego pequeno en una caneca cerca del parque infantil.",
        "categoria": Incidente.Categoria.EMERGENCIA,
        "estado": Incidente.Estado.RESUELTO,
        "ubicacion": "Parque infantil",
        "reportante": "residente4@remansos.com",
        "responsable": "vigilante1@remansos.com",
        "comentarios": [
            "Se controla el area y se usa extintor disponible.",
            "La situacion queda controlada sin personas afectadas.",
        ],
    },
    {
        "titulo": "Residente herida en escalera exterior",
        "descripcion": "Una residente reporta caida en escalera exterior y requiere apoyo inmediato.",
        "categoria": Incidente.Categoria.EMERGENCIA,
        "estado": Incidente.Estado.EN_PROCESO,
        "ubicacion": "Escalera exterior Torre A",
        "reportante": "residente5@remansos.com",
        "responsable": "vigilante2@remansos.com",
        "comentarios": ["Se acompana a la residente y se solicita contacto con familiar responsable."],
    },
    {
        "titulo": "Basura fuera de horario",
        "descripcion": "Se dejan bolsas de basura en zona comun fuera del horario permitido.",
        "categoria": Incidente.Categoria.CONVIVENCIA,
        "estado": Incidente.Estado.REGISTRADO,
        "ubicacion": "Cuarto de basuras Torre B",
        "reportante": "residente1@remansos.com",
    },
    {
        "titulo": "Rayados en paredes",
        "descripcion": "Aparecen rayados recientes en paredes del pasillo comun.",
        "categoria": Incidente.Categoria.CONVIVENCIA,
        "estado": Incidente.Estado.RESUELTO,
        "ubicacion": "Pasillo primer piso Torre C",
        "reportante": "residente2@remansos.com",
        "responsable": "vigilante1@remansos.com",
        "comentarios": [
            "Se registra evidencia fotografica del dano.",
            "Administracion coordina limpieza y comunica normas de convivencia.",
        ],
    },
    {
        "titulo": "Problema con intercomunicador apto 205",
        "descripcion": "El intercomunicador no recibe llamadas desde porteria.",
        "categoria": Incidente.Categoria.INFRAESTRUCTURA,
        "estado": Incidente.Estado.EN_PROCESO,
        "ubicacion": "Apto 205 Torre B",
        "reportante": "residente3@remansos.com",
        "responsable": "vigilante2@remansos.com",
        "comentarios": ["Se reporta al tecnico para revision de cableado y equipo."],
    },
    {
        "titulo": "Goteras en techo salon comunal",
        "descripcion": "Durante la lluvia se observan goteras en el techo del salon comunal.",
        "categoria": Incidente.Categoria.INFRAESTRUCTURA,
        "estado": Incidente.Estado.REGISTRADO,
        "ubicacion": "Salon comunal",
        "reportante": "residente4@remansos.com",
    },
    {
        "titulo": "Bicicleta abandonada en parqueadero",
        "descripcion": "Una bicicleta permanece abandonada y obstruye el paso peatonal del parqueadero.",
        "categoria": Incidente.Categoria.CONVIVENCIA,
        "estado": Incidente.Estado.CERRADO,
        "ubicacion": "Parqueadero visitantes",
        "reportante": "residente5@remansos.com",
        "responsable": "vigilante1@remansos.com",
        "comentarios": [
            "Se publica aviso para identificar propietario.",
            "El propietario retira la bicicleta del paso peatonal.",
            "Administracion cierra el caso con evidencia de retiro.",
        ],
    },
]


DEMO_TITULOS = {incidente["titulo"] for incidente in INCIDENTES_DEMO}


class Command(BaseCommand):
    help = "Carga usuarios e incidentes realistas para demostracion de CommuSafe."

    @transaction.atomic
    def handle(self, *args, **options):
        usuarios = self._crear_usuarios()
        notificaciones_eliminadas = self._limpiar_notificaciones()
        incidentes_eliminados = self._limpiar_incidentes_no_demo()
        incidentes_creados = self._crear_incidentes(usuarios)
        evidencias_creadas = self._crear_evidencias_demo()
        notificaciones_creadas = self._crear_notificaciones_demo(usuarios)

        self.stdout.write(self.style.SUCCESS("Datos demo cargados correctamente."))
        self.stdout.write("")
        self.stdout.write("Usuarios de prueba:")
        for usuario in USUARIOS_DEMO:
            self.stdout.write(f"- {usuario['email']} / {usuario['password']} ({usuario['rol']})")
        self.stdout.write("")
        self.stdout.write(f"Usuarios activos: {Usuario.objects.filter(activo=True).count()}")
        self.stdout.write(f"Incidentes no demo eliminados: {incidentes_eliminados}")
        self.stdout.write(f"Incidentes demo disponibles: {incidentes_creados}")
        self.stdout.write(f"Evidencias demo disponibles: {evidencias_creadas}")
        self.stdout.write(f"Historiales registrados: {HistorialEstado.objects.count()}")
        self.stdout.write(f"Notificaciones demo reiniciadas: {notificaciones_eliminadas}")
        self.stdout.write(f"Notificaciones demo disponibles: {notificaciones_creadas}")

    def _crear_usuarios(self):
        usuarios = {}
        for datos in USUARIOS_DEMO:
            password = datos["password"]
            defaults = {
                "nombre": datos["nombre"],
                "apellido": datos["apellido"],
                "rol": datos["rol"],
                "unidad_residencial": datos["unidad_residencial"],
                "is_staff": datos.get("is_staff", False),
                "activo": True,
            }
            usuario, creado = Usuario.objects.get_or_create(email=datos["email"], defaults=defaults)
            for campo, valor in defaults.items():
                setattr(usuario, campo, valor)
            usuario.set_password(password)
            usuario.full_clean()
            usuario.save()
            usuarios[usuario.email] = usuario
            estado = "creado" if creado else "actualizado"
            self.stdout.write(f"Usuario {estado}: {usuario.email}")
        return usuarios

    def _limpiar_notificaciones(self):
        total = Notificacion.objects.count()
        if total:
            Notificacion.objects.all().delete()
            self.stdout.write(f"Notificaciones anteriores eliminadas: {total}")
        return total

    def _limpiar_incidentes_no_demo(self):
        queryset = Incidente.objects.exclude(titulo__in=DEMO_TITULOS)
        total = queryset.count()
        if total:
            queryset.delete()
            self.stdout.write(f"Incidentes no demo eliminados: {total}")
        return total

    def _crear_notificaciones_demo(self, usuarios):
        incidentes = {incidente.titulo: incidente for incidente in Incidente.objects.all()}
        datos = [
            {
                "destinatario": "residente1@remansos.com",
                "titulo": "Tu reporte fue recibido",
                "cuerpo": "Vigilancia ya tiene registrado el caso del vehiculo sin autorizacion.",
                "tipo": Notificacion.Tipo.CAMBIO_ESTADO,
                "incidente": "Vehiculo sin autorizacion en parqueadero",
                "leida": False,
            },
            {
                "destinatario": "residente2@remansos.com",
                "titulo": "Aviso de convivencia",
                "cuerpo": "Recuerda respetar los horarios de descanso nocturno del conjunto.",
                "tipo": Notificacion.Tipo.AVISO_ADMIN,
                "incidente": None,
                "leida": False,
            },
            {
                "destinatario": "residente3@remansos.com",
                "titulo": "Emergencia en seguimiento",
                "cuerpo": "El intento de ingreso por la reja norte se encuentra en atencion.",
                "tipo": Notificacion.Tipo.EMERGENCIA,
                "incidente": "Intento de ingreso por reja norte",
                "leida": False,
            },
            {
                "destinatario": "residente4@remansos.com",
                "titulo": "Incidente resuelto",
                "cuerpo": "El incendio pequeno en caneca fue controlado sin personas afectadas.",
                "tipo": Notificacion.Tipo.CAMBIO_ESTADO,
                "incidente": "Incendio pequeno en caneca",
                "leida": True,
            },
            {
                "destinatario": "residente5@remansos.com",
                "titulo": "Caso en proceso",
                "cuerpo": "Vigilancia acompana el reporte de la residente herida en escalera exterior.",
                "tipo": Notificacion.Tipo.CAMBIO_ESTADO,
                "incidente": "Residente herida en escalera exterior",
                "leida": False,
            },
            {
                "destinatario": "vigilante1@remansos.com",
                "titulo": "Nuevo incidente de seguridad",
                "cuerpo": "Revisa el reporte de persona sospechosa en zona verde.",
                "tipo": Notificacion.Tipo.INCIDENTE_NUEVO,
                "incidente": "Persona sospechosa en zona verde",
                "leida": False,
            },
            {
                "destinatario": "vigilante2@remansos.com",
                "titulo": "Emergencia asignada",
                "cuerpo": "Atiende el intento de ingreso por la reja norte.",
                "tipo": Notificacion.Tipo.EMERGENCIA,
                "incidente": "Intento de ingreso por reja norte",
                "leida": False,
            },
            {
                "destinatario": "admin@remansos.com",
                "titulo": "Resumen operativo disponible",
                "cuerpo": "El panel cuenta con incidentes activos, resueltos y cerrados para demostracion.",
                "tipo": Notificacion.Tipo.AVISO_ADMIN,
                "incidente": None,
                "leida": False,
            },
        ]

        for item in datos:
            Notificacion.objects.create(
                destinatario=usuarios[item["destinatario"]],
                titulo=item["titulo"],
                cuerpo=item["cuerpo"],
                tipo=item["tipo"],
                leida=item["leida"],
                incidente_relacionado=incidentes.get(item["incidente"]) if item["incidente"] else None,
                enviada_push=False,
            )
        return len(datos)

    def _crear_incidentes(self, usuarios):
        admin = usuarios["admin@remansos.com"]
        total = 0
        for datos in INCIDENTES_DEMO:
            reportante = usuarios[datos["reportante"]]
            incidente, creado = Incidente.objects.get_or_create(
                titulo=datos["titulo"],
                defaults={
                    "descripcion": datos["descripcion"],
                    "categoria": datos["categoria"],
                    "ubicacion_referencia": datos["ubicacion"],
                    "reportado_por": reportante,
                },
            )
            incidente.descripcion = datos["descripcion"]
            incidente.categoria = datos["categoria"]
            incidente.ubicacion_referencia = datos["ubicacion"]
            incidente.reportado_por = reportante
            incidente.atendido_por = None
            incidente.estado = Incidente.Estado.REGISTRADO
            incidente.fecha_cierre = None
            incidente.observaciones_cierre = ""
            incidente.save()
            incidente.historial.all().delete()
            incidente.evidencias.all().delete()

            responsable = usuarios.get(datos.get("responsable", ""), admin)
            comentarios = datos.get("comentarios", [])
            self._aplicar_estado_demo(incidente, datos["estado"], responsable, admin, comentarios)

            total += 1
            estado = "creado" if creado else "actualizado"
            self.stdout.write(f"Incidente {estado}: {incidente.titulo}")
        return total

    def _crear_evidencias_demo(self):
        datos = [
            {
                "titulo": "Vehiculo sin autorizacion en parqueadero",
                "descripcion": "Foto adjunta del vehiculo ubicado en parqueadero.",
                "texto": "Parqueadero",
                "color": (26, 26, 46),
            },
            {
                "titulo": "Fuga de agua en pasillo Torre A",
                "descripcion": "Foto adjunta de acumulacion de agua en el pasillo.",
                "texto": "Pasillo Torre A",
                "color": (15, 52, 96),
            },
            {
                "titulo": "Incendio pequeno en caneca",
                "descripcion": "Foto adjunta posterior al control del conato.",
                "texto": "Zona infantil",
                "color": (233, 69, 96),
            },
            {
                "titulo": "Luminaria danada en calle interna",
                "descripcion": "Foto adjunta de la luminaria reportada.",
                "texto": "Calle interna",
                "color": (22, 33, 62),
            },
            {
                "titulo": "Rayados en paredes",
                "descripcion": "Foto adjunta del dano en pared comunal.",
                "texto": "Pared comunal",
                "color": (245, 158, 11),
            },
        ]

        total = 0
        for item in datos:
            incidente = Incidente.objects.filter(titulo=item["titulo"]).first()
            if not incidente:
                continue
            evidencia = EvidenciaIncidente(
                incidente=incidente,
                descripcion=item["descripcion"],
            )
            evidencia.imagen.save(
                f"evidencia_demo_{total + 1}.jpg",
                ContentFile(self._generar_imagen_demo(item["texto"], item["color"])),
                save=True,
            )
            total += 1
        return total

    def _generar_imagen_demo(self, texto, color):
        width, height = 960, 640
        image = Image.new("RGB", (width, height), color)
        draw = ImageDraw.Draw(image)

        for y in range(height):
            alpha = y / height
            line_color = tuple(max(0, min(255, int(channel * (1 - alpha) + 248 * alpha))) for channel in color)
            draw.line((0, y, width, y), fill=line_color)

        draw.rounded_rectangle((72, 72, width - 72, height - 72), radius=44, outline=(255, 255, 255), width=6)
        draw.ellipse((104, 104, 176, 176), fill=(255, 255, 255))
        draw.text((128, 124), "CS", fill=color)
        draw.text((104, 245), "Evidencia fotografica", fill=(255, 255, 255))
        draw.text((104, 305), texto, fill=(255, 255, 255))
        draw.text((104, 390), "CommuSafe - Remansos del Norte", fill=(255, 255, 255))
        draw.text((104, 455), "Imagen demo adjunta por residente", fill=(255, 255, 255))

        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=88)
        return buffer.getvalue()

    def _aplicar_estado_demo(self, incidente, estado_objetivo, responsable, admin, comentarios):
        if estado_objetivo == Incidente.Estado.REGISTRADO:
            return

        comentario_proceso = comentarios[0] if comentarios else "Vigilancia inicia la atencion del caso."
        cambiar_estado_incidente(
            incidente=incidente,
            estado_nuevo=Incidente.Estado.EN_PROCESO,
            comentario=comentario_proceso,
            usuario=responsable,
        )

        if estado_objetivo == Incidente.Estado.EN_PROCESO:
            return

        comentario_resuelto = (
            comentarios[1] if len(comentarios) > 1 else "El caso queda gestionado operativamente."
        )
        cambiar_estado_incidente(
            incidente=incidente,
            estado_nuevo=Incidente.Estado.RESUELTO,
            comentario=comentario_resuelto,
            usuario=responsable,
        )

        if estado_objetivo == Incidente.Estado.RESUELTO:
            return

        comentario_cierre = (
            comentarios[2] if len(comentarios) > 2 else "Administracion valida la solucion y cierra el caso."
        )
        cambiar_estado_incidente(
            incidente=incidente,
            estado_nuevo=Incidente.Estado.CERRADO,
            comentario=comentario_cierre,
            usuario=admin,
        )
