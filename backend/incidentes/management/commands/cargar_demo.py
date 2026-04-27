from django.core.management.base import BaseCommand
from django.db import transaction

from incidentes.models import HistorialEstado, Incidente
from incidentes.services import cambiar_estado_incidente
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
        incidentes_eliminados = self._limpiar_incidentes_no_demo()
        incidentes_creados = self._crear_incidentes(usuarios)

        self.stdout.write(self.style.SUCCESS("Datos demo cargados correctamente."))
        self.stdout.write("")
        self.stdout.write("Usuarios de prueba:")
        for usuario in USUARIOS_DEMO:
            self.stdout.write(f"- {usuario['email']} / {usuario['password']} ({usuario['rol']})")
        self.stdout.write("")
        self.stdout.write(f"Usuarios activos: {Usuario.objects.filter(activo=True).count()}")
        self.stdout.write(f"Incidentes no demo eliminados: {incidentes_eliminados}")
        self.stdout.write(f"Incidentes demo disponibles: {incidentes_creados}")
        self.stdout.write(f"Historiales registrados: {HistorialEstado.objects.count()}")

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

    def _limpiar_incidentes_no_demo(self):
        queryset = Incidente.objects.exclude(titulo__in=DEMO_TITULOS)
        total = queryset.count()
        if total:
            queryset.delete()
            self.stdout.write(f"Incidentes no demo eliminados: {total}")
        return total

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

            responsable = usuarios.get(datos.get("responsable", ""), admin)
            comentarios = datos.get("comentarios", [])
            self._aplicar_estado_demo(incidente, datos["estado"], responsable, admin, comentarios)

            total += 1
            estado = "creado" if creado else "actualizado"
            self.stdout.write(f"Incidente {estado}: {incidente.titulo}")
        return total

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
