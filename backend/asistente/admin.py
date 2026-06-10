"""Administracion del asistente y su base de conocimiento."""

from django.contrib import admin, messages
from django.utils import timezone
from django.utils.text import slugify

from .local_engine import normalize_text
from .models import (
    AsistenteRespuestaLog,
    ConsultaSinRespuesta,
    ConversacionAsistente,
    EntradaConocimiento,
    MensajeAsistente,
    VersionEntradaConocimiento,
)


class SoloAdministradorMixin:
    """Restringe el conocimiento oficial a administradores del sistema."""

    def _es_administrador(self, request):
        return request.user.is_superuser or getattr(request.user, "es_administrador", False)

    def has_module_permission(self, request):
        return self._es_administrador(request)

    def has_view_permission(self, request, obj=None):
        return self._es_administrador(request)

    def has_add_permission(self, request):
        return self._es_administrador(request)

    def has_change_permission(self, request, obj=None):
        return self._es_administrador(request)

    def has_delete_permission(self, request, obj=None):
        return self._es_administrador(request)


class MensajeAsistenteInline(admin.TabularInline):
    model = MensajeAsistente
    extra = 0
    readonly_fields = ("rol", "contenido", "fecha_creacion")
    can_delete = False


class VersionEntradaConocimientoInline(admin.TabularInline):
    model = VersionEntradaConocimiento
    extra = 0
    can_delete = False
    readonly_fields = ("version", "cambiado_por", "fecha_cambio", "datos")
    ordering = ("-version",)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ConversacionAsistente)
class ConversacionAsistenteAdmin(SoloAdministradorMixin, admin.ModelAdmin):
    list_display = ("titulo", "usuario", "fecha_creacion", "fecha_actualizacion")
    list_filter = ("fecha_creacion", "fecha_actualizacion")
    search_fields = ("titulo", "usuario__email", "usuario__nombre", "usuario__apellido")
    autocomplete_fields = ("usuario",)
    readonly_fields = ("fecha_creacion", "fecha_actualizacion")
    inlines = (MensajeAsistenteInline,)


@admin.register(MensajeAsistente)
class MensajeAsistenteAdmin(SoloAdministradorMixin, admin.ModelAdmin):
    list_display = ("conversacion", "rol", "fecha_creacion")
    list_filter = ("rol", "fecha_creacion")
    search_fields = ("contenido", "conversacion__titulo", "conversacion__usuario__email")
    autocomplete_fields = ("conversacion",)
    readonly_fields = ("fecha_creacion",)


@admin.register(AsistenteRespuestaLog)
class AsistenteRespuestaLogAdmin(SoloAdministradorMixin, admin.ModelAdmin):
    list_display = (
        "fecha_creacion",
        "usuario",
        "modo",
        "proveedor",
        "intencion",
        "confianza",
        "latencia_ms",
        "requiere_validacion",
    )
    list_filter = ("modo", "proveedor", "categoria", "requiere_validacion", "fecha_creacion")
    search_fields = ("mensaje", "intencion", "usuario__email", "usuario__nombre", "usuario__apellido")
    autocomplete_fields = ("usuario", "conversacion")
    readonly_fields = (
        "usuario",
        "conversacion",
        "mensaje",
        "modo",
        "proveedor",
        "modelo",
        "intencion",
        "categoria",
        "metodo",
        "confianza",
        "latencia_ms",
        "tokens_entrada",
        "tokens_salida",
        "requiere_validacion",
        "metadata",
        "fecha_creacion",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EntradaConocimiento)
class EntradaConocimientoAdmin(SoloAdministradorMixin, admin.ModelAdmin):
    list_display = (
        "codigo",
        "pregunta",
        "categoria",
        "estado",
        "version",
        "actualizado_por",
        "aprobado_por",
        "fecha_actualizacion",
    )
    list_filter = ("estado", "categoria", "roles_permitidos", "fecha_actualizacion")
    search_fields = ("codigo", "pregunta", "respuesta", "intencion_principal", "palabras_clave")
    readonly_fields = (
        "version",
        "creado_por",
        "actualizado_por",
        "aprobado_por",
        "fecha_aprobacion",
        "fecha_creacion",
        "fecha_actualizacion",
    )
    inlines = (VersionEntradaConocimientoInline,)
    actions = ("enviar_a_revision", "aprobar_entradas", "desactivar_entradas", "devolver_a_borrador")
    fieldsets = (
        (
            "Contenido",
            {
                "fields": (
                    "codigo",
                    "pregunta",
                    "respuesta",
                    "categoria",
                    "intencion_principal",
                    "subintencion",
                )
            },
        ),
        (
            "Comprension local",
            {"fields": ("palabras_clave", "variaciones", "roles_permitidos")},
        ),
        (
            "Gobierno y vigencia",
            {
                "fields": (
                    "estado",
                    "vigente_desde",
                    "vigente_hasta",
                    "fuente",
                    "nota_cambio",
                    "version",
                    "creado_por",
                    "actualizado_por",
                    "aprobado_por",
                    "fecha_aprobacion",
                    "fecha_creacion",
                    "fecha_actualizacion",
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not obj.creado_por_id:
            obj.creado_por = request.user
        obj.actualizado_por = request.user
        campos_que_exigen_revision = set(EntradaConocimiento.CAMPOS_VERSIONADOS) - {
            "estado",
            "nota_cambio",
        }
        if (
            change
            and obj.estado == EntradaConocimiento.Estado.APROBADA
            and campos_que_exigen_revision.intersection(form.changed_data)
        ):
            obj.estado = EntradaConocimiento.Estado.EN_REVISION
            obj.aprobado_por = None
            obj.fecha_aprobacion = None
            self.message_user(
                request,
                "La entrada cambio y fue enviada a revision antes de volver a publicarse.",
                messages.WARNING,
            )
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        campos = list(super().get_readonly_fields(request, obj))
        if obj:
            campos.append("codigo")
        return tuple(campos)

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description="Enviar entradas seleccionadas a revision")
    def enviar_a_revision(self, request, queryset):
        total = self._cambiar_estado(queryset, request, EntradaConocimiento.Estado.EN_REVISION)
        self.message_user(request, f"{total} entradas enviadas a revision.", messages.SUCCESS)

    @admin.action(description="Aprobar y publicar entradas seleccionadas")
    def aprobar_entradas(self, request, queryset):
        total = 0
        for entrada in queryset:
            entrada.estado = EntradaConocimiento.Estado.APROBADA
            entrada.aprobado_por = request.user
            entrada.fecha_aprobacion = timezone.now()
            entrada.actualizado_por = request.user
            entrada.nota_cambio = entrada.nota_cambio or "Entrada aprobada para uso oficial."
            entrada.full_clean()
            entrada.save()
            total += 1
        self.message_user(request, f"{total} entradas aprobadas y publicadas.", messages.SUCCESS)

    @admin.action(description="Desactivar entradas seleccionadas")
    def desactivar_entradas(self, request, queryset):
        total = self._cambiar_estado(queryset, request, EntradaConocimiento.Estado.INACTIVA)
        self.message_user(request, f"{total} entradas desactivadas.", messages.SUCCESS)

    @admin.action(description="Devolver entradas seleccionadas a borrador")
    def devolver_a_borrador(self, request, queryset):
        total = self._cambiar_estado(queryset, request, EntradaConocimiento.Estado.BORRADOR)
        self.message_user(request, f"{total} entradas devueltas a borrador.", messages.SUCCESS)

    @staticmethod
    def _cambiar_estado(queryset, request, estado):
        total = 0
        for entrada in queryset:
            entrada.estado = estado
            entrada.actualizado_por = request.user
            entrada.save()
            total += 1
        return total


@admin.register(VersionEntradaConocimiento)
class VersionEntradaConocimientoAdmin(SoloAdministradorMixin, admin.ModelAdmin):
    list_display = ("entrada", "version", "cambiado_por", "fecha_cambio")
    list_filter = ("fecha_cambio",)
    search_fields = ("entrada__codigo", "entrada__pregunta", "cambiado_por__email")
    readonly_fields = ("entrada", "version", "datos", "cambiado_por", "fecha_cambio")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ConsultaSinRespuesta)
class ConsultaSinRespuestaAdmin(SoloAdministradorMixin, admin.ModelAdmin):
    list_display = (
        "consulta_muestra",
        "rol",
        "cantidad",
        "confianza_maxima",
        "intencion_sugerida",
        "estado",
        "fecha_ultima_consulta",
    )
    list_filter = ("estado", "rol", "fecha_ultima_consulta")
    search_fields = ("consulta_muestra", "consulta_normalizada", "intencion_sugerida")
    readonly_fields = (
        "huella",
        "rol",
        "consulta_muestra",
        "consulta_normalizada",
        "cantidad",
        "confianza_maxima",
        "intencion_sugerida",
        "entrada_generada",
        "revisado_por",
        "fecha_primera_consulta",
        "fecha_ultima_consulta",
    )
    actions = ("marcar_en_revision", "convertir_en_borrador", "descartar_consultas")

    @admin.action(description="Marcar consultas seleccionadas en revision")
    def marcar_en_revision(self, request, queryset):
        total = queryset.update(estado=ConsultaSinRespuesta.Estado.EN_REVISION, revisado_por=request.user)
        self.message_user(request, f"{total} consultas marcadas en revision.", messages.SUCCESS)

    @admin.action(description="Convertir consultas seleccionadas en borradores")
    def convertir_en_borrador(self, request, queryset):
        total = 0
        for consulta in queryset.exclude(estado=ConsultaSinRespuesta.Estado.CONVERTIDA):
            codigo_base = slugify(consulta.consulta_normalizada)[:90] or "consulta"
            codigo = f"pendiente-{codigo_base}"
            consecutivo = 2
            while EntradaConocimiento.objects.filter(codigo=codigo).exists():
                codigo = f"pendiente-{codigo_base[:80]}-{consecutivo}"
                consecutivo += 1

            tokens = list(dict.fromkeys(normalize_text(consulta.consulta_muestra).split()))
            palabras_clave = (tokens + ["commusafe", "administracion", "consulta"])[:8]
            variaciones = list(dict.fromkeys([consulta.consulta_muestra, consulta.consulta_normalizada]))
            if len(variaciones) < 2:
                variaciones.append(f"Necesito informacion sobre {consulta.consulta_normalizada}")

            entrada = EntradaConocimiento.objects.create(
                codigo=codigo,
                pregunta=consulta.consulta_muestra[:300],
                respuesta="Pendiente de redactar y verificar por administracion.",
                categoria="pendiente_clasificacion",
                intencion_principal=consulta.intencion_sugerida or "sin_intencion_confiable",
                subintencion=codigo,
                palabras_clave=palabras_clave,
                variaciones=variaciones,
                roles_permitidos=[consulta.rol],
                estado=EntradaConocimiento.Estado.BORRADOR,
                fuente="Consulta frecuente detectada por CommuSafe",
                nota_cambio=f"Creada desde una consulta repetida {consulta.cantidad} veces.",
                creado_por=request.user,
                actualizado_por=request.user,
            )
            consulta.estado = ConsultaSinRespuesta.Estado.CONVERTIDA
            consulta.entrada_generada = entrada
            consulta.revisado_por = request.user
            consulta.save(update_fields=["estado", "entrada_generada", "revisado_por"])
            total += 1
        self.message_user(request, f"{total} borradores creados para revision.", messages.SUCCESS)

    @admin.action(description="Descartar consultas seleccionadas")
    def descartar_consultas(self, request, queryset):
        total = queryset.update(estado=ConsultaSinRespuesta.Estado.DESCARTADA, revisado_por=request.user)
        self.message_user(request, f"{total} consultas descartadas.", messages.SUCCESS)

    def has_add_permission(self, request):
        return False
