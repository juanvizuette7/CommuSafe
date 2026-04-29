"""Vistas del panel web administrativo."""

from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import ProtectedError
from django.db.models import Count, Max, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from rest_framework_simplejwt.tokens import RefreshToken

from incidentes.models import Incidente
from incidentes.serializers import CambiarEstadoSerializer
from incidentes.services import cambiar_estado_incidente
from notificaciones.models import Notificacion
from notificaciones.serializers import AvisoComunitarioSerializer
from notificaciones.services import (
    AudienciaAviso,
    notificar_aviso_comunitario,
    usuarios_disponibles_para_aviso,
)
from usuarios.models import Usuario
from usuarios.serializers import CambioRolSerializer
from usuarios.services import PasswordResetError, confirmar_reset_password, crear_y_enviar_token_reset

from .forms import (
    PasswordResetConfirmacionForm,
    PasswordResetSolicitudForm,
    UsuarioCreacionForm,
    UsuarioEdicionForm,
)


def _es_usuario_panel(usuario):
    return usuario.is_authenticated and not usuario.es_residente


def panel_login_required(view_func):
    """Restringe el acceso al panel a administradores y vigilantes autenticados."""

    @wraps(view_func)
    @login_required(login_url="panel_web:login")
    def wrapper(request, *args, **kwargs):
        if request.user.es_residente:
            logout(request)
            messages.error(
                request,
                "Los residentes no tienen acceso al panel web. Deben usar la aplicación móvil.",
            )
            return redirect("panel_web:login")
        return view_func(request, *args, **kwargs)

    return wrapper


def _contexto_base_panel(request, **extra):
    contexto = {
        "usuario_panel": request.user,
        "notificaciones_no_leidas": request.user.notificaciones.filter(leida=False).count()
        if request.user.is_authenticated
        else 0,
    }
    contexto.update(extra)
    return contexto


def _redirigir_si_no_es_administrador(request):
    if request.user.es_administrador:
        return None
    messages.error(request, "Solo un administrador puede gestionar usuarios desde el panel web.")
    return redirect("panel_web:usuarios_lista")


def _opciones_estado_disponibles(usuario, incidente):
    if incidente.estado == Incidente.Estado.REGISTRADO:
        return [Incidente.Estado.EN_PROCESO]
    if incidente.estado == Incidente.Estado.EN_PROCESO:
        return [Incidente.Estado.RESUELTO]
    if incidente.estado == Incidente.Estado.RESUELTO and usuario.es_administrador:
        return [Incidente.Estado.CERRADO]
    return []


def _respuesta_con_cookie_jwt_panel(request, usuario, destino):
    """Crea la redireccion del panel y adjunta un JWT para refrescos del sidebar."""

    access_token = RefreshToken.for_user(usuario).access_token
    response = redirect(destino)
    response.set_cookie(
        "commusafe_panel_access",
        str(access_token),
        max_age=8 * 60 * 60,
        secure=request.is_secure() and not settings.DEBUG,
        samesite="Lax",
    )
    return response


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Autentica al usuario y permite acceso solo a administradores y vigilantes."""

    if request.user.is_authenticated:
        if _es_usuario_panel(request.user):
            return _respuesta_con_cookie_jwt_panel(request, request.user, "panel_web:dashboard")
        logout(request)
        messages.error(
            request,
            "Los residentes no tienen acceso al panel web. Deben ingresar desde la app móvil.",
        )

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        usuario = authenticate(request, email=email, password=password)
        if usuario is None:
            messages.error(request, "Correo electrónico o contraseña incorrectos.")
        elif usuario.es_residente:
            messages.error(
                request,
                "Tu cuenta corresponde a un residente. Este acceso está reservado para administración y vigilancia.",
            )
        else:
            login(request, usuario)
            messages.success(request, f"Bienvenido al panel, {usuario.nombre}.")
            return _respuesta_con_cookie_jwt_panel(request, usuario, "panel_web:dashboard")

    return render(
        request,
        "panel/login.html",
        {
            "page_title": "Iniciar sesión",
            "page_subtitle": "Acceso administrativo",
        },
    )


@require_http_methods(["GET", "POST"])
def reset_solicitar(request):
    """Muestra y procesa el formulario publico de recuperacion."""

    form = PasswordResetSolicitudForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        usuario = Usuario.objects.filter(email__iexact=email, activo=True).first()
        if usuario is not None:
            crear_y_enviar_token_reset(usuario, request)
        messages.success(
            request,
            "Si el correo existe, recibirás un enlace de recuperación en los próximos minutos.",
        )
        return redirect("panel_web:reset_solicitar")

    return render(
        request,
        "panel/reset_solicitar.html",
        {
            "page_title": "Recuperar contraseña",
            "page_subtitle": "Solicita un enlace seguro para restablecer tu acceso",
            "form": form,
        },
    )


@require_http_methods(["GET", "POST"])
def reset_confirmar(request, token):
    """Permite definir una contrasena nueva usando un token vigente."""

    form = PasswordResetConfirmacionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            confirmar_reset_password(token, form.cleaned_data["password"])
        except PasswordResetError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "La contraseña fue actualizada correctamente. Ya puedes iniciar sesión.")
            return redirect("panel_web:login")

    return render(
        request,
        "panel/reset_confirmar.html",
        {
            "page_title": "Nueva contraseña",
            "page_subtitle": "Define una contraseña segura para tu cuenta",
            "form": form,
            "token": token,
        },
    )


@require_GET
def inicio(request):
    """Redirige al login o al dashboard según el estado de sesión."""

    if request.user.is_authenticated and _es_usuario_panel(request.user):
        return redirect("panel_web:dashboard")
    response = redirect("panel_web:login")
    response.delete_cookie("commusafe_panel_access")
    return response


@require_POST
def logout_view(request):
    """Cierra la sesión del usuario del panel."""

    logout(request)
    messages.success(request, "La sesión se cerró correctamente.")
    response = redirect("panel_web:login")
    response.delete_cookie("commusafe_panel_access")
    return response


@panel_login_required
@require_GET
def dashboard(request):
    """Página principal del panel con métricas y últimos incidentes."""

    hoy = timezone.localdate()
    incidentes_activos = Incidente.objects.exclude(estado=Incidente.Estado.CERRADO)
    recientes = (
        Incidente.objects.select_related("reportado_por", "atendido_por")
        .order_by("-fecha_reporte")[:10]
    )

    contexto = _contexto_base_panel(
        request,
        page_title="Dashboard",
        page_subtitle="Resumen operativo de Remansos del Norte",
        active_nav="dashboard",
        metricas={
            "incidentes_activos": incidentes_activos.count(),
            "incidentes_alta": incidentes_activos.filter(prioridad=Incidente.Prioridad.ALTA).count(),
            "resueltos_hoy": Incidente.objects.filter(
                estado=Incidente.Estado.RESUELTO,
                fecha_actualizacion__date=hoy,
            ).count(),
            "usuarios_activos": Usuario.objects.filter(activo=True).count(),
        },
        incidentes_recientes=recientes,
    )
    return render(request, "panel/dashboard.html", contexto)


@panel_login_required
@require_GET
def panel_notificaciones(request):
    """Lista las notificaciones propias del usuario autenticado en el panel."""

    queryset = Notificacion.objects.filter(destinatario=request.user).select_related(
        "incidente_relacionado"
    ).order_by("-fecha_envio")
    paginador = Paginator(queryset, 25)
    page_obj = paginador.get_page(request.GET.get("page"))

    contexto = _contexto_base_panel(
        request,
        page_title="Notificaciones",
        page_subtitle="Alertas y avisos recibidos por tu cuenta",
        active_nav="notificaciones",
        page_obj=page_obj,
    )
    return render(request, "panel/notificaciones.html", contexto)


@panel_login_required
@require_POST
def panel_notificacion_leer(request, id):
    """Marca como leida una notificacion propia del usuario del panel."""

    notificacion = get_object_or_404(Notificacion, id=id, destinatario=request.user)
    if not notificacion.leida:
        notificacion.leida = True
        notificacion.save(update_fields=["leida"])
        messages.success(request, "La notificación fue marcada como leída.")
    else:
        messages.info(request, "La notificación ya estaba marcada como leída.")

    siguiente = request.META.get("HTTP_REFERER")
    if siguiente:
        return HttpResponseRedirect(siguiente)
    return redirect("panel_web:panel_notificaciones")


@panel_login_required
@require_GET
def incidentes_lista(request):
    """Lista completa de incidentes con filtros y búsqueda."""

    queryset = Incidente.objects.select_related("reportado_por", "atendido_por").order_by("-fecha_reporte")

    categoria = request.GET.get("categoria", "").strip()
    estado = request.GET.get("estado", "").strip()
    prioridad = request.GET.get("prioridad", "").strip()
    busqueda = request.GET.get("q", "").strip()

    if categoria:
        queryset = queryset.filter(categoria=categoria)
    if estado:
        queryset = queryset.filter(estado=estado)
    if prioridad:
        queryset = queryset.filter(prioridad=prioridad)
    if busqueda:
        queryset = queryset.filter(Q(titulo__icontains=busqueda) | Q(descripcion__icontains=busqueda))

    paginador = Paginator(queryset, 12)
    page_obj = paginador.get_page(request.GET.get("page"))

    contexto = _contexto_base_panel(
        request,
        page_title="Incidentes",
        page_subtitle="Seguimiento y trazabilidad de reportes",
        active_nav="incidentes",
        page_obj=page_obj,
        filtros_activos={
            "categoria": categoria,
            "estado": estado,
            "prioridad": prioridad,
            "q": busqueda,
        },
        categorias=Incidente.Categoria.choices,
        estados=Incidente.Estado.choices,
        prioridades=Incidente.Prioridad.choices,
    )
    return render(request, "panel/incidentes_lista.html", contexto)


@panel_login_required
@require_http_methods(["GET", "POST"])
def incidente_detalle(request, incidente_id):
    """Muestra el detalle del incidente y permite cambiar su estado."""

    incidente = get_object_or_404(
        Incidente.objects.select_related("reportado_por", "atendido_por"),
        id=incidente_id,
    )

    if request.method == "POST":
        comentario = request.POST.get("comentario", "").strip()
        estado_nuevo = request.POST.get("estado_nuevo", "").strip()

        if not comentario:
            messages.error(request, "Debes escribir un comentario para registrar el cambio de estado.")
            return redirect("panel_web:incidente_detalle", incidente_id=incidente.id)

        serializer = CambiarEstadoSerializer(
            data={"estado_nuevo": estado_nuevo, "comentario": comentario},
            context={"request": request, "incidente": incidente},
        )

        if serializer.is_valid():
            incidente, _ = cambiar_estado_incidente(
                incidente=incidente,
                estado_nuevo=serializer.validated_data["estado_nuevo"],
                comentario=serializer.validated_data["comentario"],
                usuario=request.user,
            )
            from notificaciones.services import notificar_cambio_estado

            notificar_cambio_estado(incidente, serializer.validated_data["estado_nuevo"])
            messages.success(request, "El incidente fue actualizado correctamente.")
            return redirect("panel_web:incidente_detalle", incidente_id=incidente.id)

        for errores in serializer.errors.values():
            if isinstance(errores, (list, tuple)):
                for error in errores:
                    messages.error(request, str(error))
            else:
                messages.error(request, str(errores))
        return redirect("panel_web:incidente_detalle", incidente_id=incidente.id)

    contexto = _contexto_base_panel(
        request,
        page_title=incidente.titulo,
        page_subtitle="Detalle completo del incidente",
        active_nav="incidentes",
        incidente=incidente,
        historial=incidente.historial.select_related("cambiado_por").order_by("fecha_cambio"),
        evidencias=incidente.evidencias.all().order_by("-fecha_subida"),
        estados_disponibles=_opciones_estado_disponibles(request.user, incidente),
    )
    return render(request, "panel/incidente_detalle.html", contexto)


@panel_login_required
@require_GET
def usuarios_lista(request):
    """Lista los usuarios del sistema con filtro por rol."""

    rol = request.GET.get("rol", "").strip()
    usuarios = Usuario.objects.all().order_by("nombre", "apellido")
    if rol:
        usuarios = usuarios.filter(rol=rol)

    contexto = _contexto_base_panel(
        request,
        page_title="Usuarios",
        page_subtitle="Control de cuentas y roles del sistema",
        active_nav="usuarios",
        usuarios=usuarios,
        rol_activo=rol,
        roles=Usuario.Rol.choices,
    )
    return render(request, "panel/usuarios_lista.html", contexto)


@panel_login_required
@require_http_methods(["GET", "POST"])
def usuario_crear(request):
    """Crea una cuenta de usuario desde el panel administrativo."""

    redireccion = _redirigir_si_no_es_administrador(request)
    if redireccion:
        return redireccion

    form = UsuarioCreacionForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            usuario = form.save()
            messages.success(request, f"El usuario {usuario.nombre_completo} fue creado correctamente.")
            return redirect("panel_web:usuarios_lista")
        messages.error(request, "Revisa los datos del formulario antes de crear el usuario.")

    contexto = _contexto_base_panel(
        request,
        page_title="Nuevo Usuario",
        page_subtitle="Creación de cuentas para residentes, vigilancia y administración",
        active_nav="usuarios",
        form=form,
        modo_formulario="crear",
        titulo_formulario="Crear nuevo usuario",
        texto_boton="Crear usuario",
    )
    return render(request, "panel/usuario_form.html", contexto)


@panel_login_required
@require_http_methods(["GET", "POST"])
def usuario_editar(request, usuario_id):
    """Edita los datos principales de una cuenta de usuario."""

    redireccion = _redirigir_si_no_es_administrador(request)
    if redireccion:
        return redireccion

    usuario = get_object_or_404(Usuario, id=usuario_id)
    form = UsuarioEdicionForm(request.POST or None, instance=usuario)
    if request.method == "POST":
        if form.is_valid():
            usuario = form.save()
            messages.success(request, f"El usuario {usuario.nombre_completo} fue actualizado correctamente.")
            return redirect("panel_web:usuarios_lista")
        messages.error(request, "Revisa los datos del formulario antes de guardar los cambios.")

    contexto = _contexto_base_panel(
        request,
        page_title="Editar Usuario",
        page_subtitle=f"Actualización de datos de {usuario.nombre_completo}",
        active_nav="usuarios",
        form=form,
        usuario_objetivo=usuario,
        modo_formulario="editar",
        titulo_formulario="Editar usuario",
        texto_boton="Guardar cambios",
    )
    return render(request, "panel/usuario_form.html", contexto)


@panel_login_required
@require_POST
def usuario_cambiar_rol(request, usuario_id):
    """Cambia el rol de una cuenta usando la misma validación del serializer REST."""

    redireccion = _redirigir_si_no_es_administrador(request)
    if redireccion:
        return redireccion

    usuario = get_object_or_404(Usuario, id=usuario_id)
    serializer = CambioRolSerializer(data={"rol": request.POST.get("nuevo_rol", "")})
    if serializer.is_valid():
        usuario.rol = serializer.validated_data["rol"]
        usuario.is_staff = usuario.rol == Usuario.Rol.ADMINISTRADOR or usuario.is_superuser
        try:
            usuario.full_clean()
            usuario.save(update_fields=["rol", "is_staff"])
        except Exception as exc:
            messages.error(request, f"No fue posible cambiar el rol: {exc}")
        else:
            messages.success(
                request,
                f"El rol de {usuario.nombre_completo} fue actualizado a {usuario.get_rol_display()}.",
            )
    else:
        messages.error(request, "El rol seleccionado no es válido.")

    siguiente = request.META.get("HTTP_REFERER")
    if siguiente:
        return HttpResponseRedirect(siguiente)
    return redirect("panel_web:usuarios_lista")


@panel_login_required
@require_http_methods(["GET", "POST"])
def usuario_eliminar(request, usuario_id):
    """Elimina físicamente una cuenta de usuario desde el panel administrativo."""

    redireccion = _redirigir_si_no_es_administrador(request)
    if redireccion:
        return redireccion

    usuario = get_object_or_404(Usuario, id=usuario_id)
    if request.method == "POST":
        nombre_usuario = usuario.nombre_completo
        try:
            usuario.delete()
        except ProtectedError:
            messages.error(
                request,
                "No se puede eliminar definitivamente este usuario porque tiene incidentes o historial asociado.",
            )
            return redirect("panel_web:usuarios_lista")
        messages.success(request, f"El usuario {nombre_usuario} fue eliminado definitivamente.")
        return redirect("panel_web:usuarios_lista")

    contexto = _contexto_base_panel(
        request,
        page_title="Eliminar Usuario",
        page_subtitle="Confirmación de eliminación definitiva",
        active_nav="usuarios",
        usuario_objetivo=usuario,
    )
    return render(request, "panel/usuario_eliminar.html", contexto)


@panel_login_required
@require_http_methods(["GET", "POST"])
def avisos_comunitarios(request):
    """Permite enviar avisos o alertas manuales a usuarios segmentados."""

    if request.method == "POST":
        datos = request.POST.copy()
        destinatarios_ids = request.POST.getlist("destinatarios_ids")
        if destinatarios_ids:
            datos.setlist("destinatarios_ids", destinatarios_ids)
        if request.user.es_vigilante and datos.get("audiencia") != AudienciaAviso.ESPECIFICOS:
            datos["audiencia"] = AudienciaAviso.RESIDENTES

        serializer = AvisoComunitarioSerializer(data=datos, context={"request": request})
        if serializer.is_valid():
            resultado = notificar_aviso_comunitario(**serializer.validated_data)
            messages.success(
                request,
                f"El aviso fue enviado a {resultado['total_destinatarios']} usuario(s).",
            )
            return redirect("panel_web:avisos")

        for errores in serializer.errors.values():
            if isinstance(errores, (list, tuple)):
                for error in errores:
                    messages.error(request, str(error))
            else:
                messages.error(request, str(errores))
        return redirect("panel_web:avisos")

    audiencias = AudienciaAviso.CHOICES
    if request.user.es_vigilante:
        audiencias = (
            (AudienciaAviso.RESIDENTES, "Residentes activos"),
            (AudienciaAviso.ESPECIFICOS, "Usuarios seleccionados"),
        )

    destinatarios_disponibles = usuarios_disponibles_para_aviso(request.user)
    residentes_destinatarios = destinatarios_disponibles.filter(rol=Usuario.Rol.RESIDENTE)
    vigilantes_destinatarios = destinatarios_disponibles.filter(rol=Usuario.Rol.VIGILANTE)
    administradores_destinatarios = destinatarios_disponibles.filter(rol=Usuario.Rol.ADMINISTRADOR)

    avisos_recientes = (
        Notificacion.objects.filter(
            incidente_relacionado__isnull=True,
            tipo__in=[Notificacion.Tipo.AVISO_ADMIN, Notificacion.Tipo.EMERGENCIA],
        )
        .values("titulo", "cuerpo", "tipo")
        .annotate(
            total_destinatarios=Count("id"),
            total_leidas=Count("id", filter=Q(leida=True)),
            fecha=Max("fecha_envio"),
        )
        .order_by("-fecha")[:10]
    )

    contexto = _contexto_base_panel(
        request,
        page_title="Avisos",
        page_subtitle="Comunicación directa con residentes y equipo operativo",
        active_nav="avisos",
        audiencias=audiencias,
        tipos=[
            (Notificacion.Tipo.AVISO_ADMIN, "Aviso informativo"),
            (Notificacion.Tipo.EMERGENCIA, "Alerta de emergencia"),
        ],
        avisos_recientes=avisos_recientes,
        audiencia_forzada_residentes=request.user.es_vigilante,
        residentes_destinatarios=residentes_destinatarios,
        vigilantes_destinatarios=vigilantes_destinatarios,
        administradores_destinatarios=administradores_destinatarios,
    )
    return render(request, "panel/avisos.html", contexto)


@panel_login_required
@require_POST
def usuario_toggle_activo(request, usuario_id):
    """Activa o desactiva una cuenta de usuario."""

    if not request.user.es_administrador:
        messages.error(request, "Solo un administrador puede activar o desactivar usuarios.")
        return redirect("panel_web:usuarios_lista")

    usuario = get_object_or_404(Usuario, id=usuario_id)
    if usuario.id == request.user.id and usuario.activo:
        messages.error(request, "No puedes desactivar tu propia cuenta desde el panel.")
        return redirect("panel_web:usuarios_lista")

    usuario.activo = not usuario.activo
    usuario.save(update_fields=["activo"])

    estado = "activada" if usuario.activo else "desactivada"
    messages.success(request, f"La cuenta de {usuario.nombre_completo} fue {estado} correctamente.")

    siguiente = request.META.get("HTTP_REFERER")
    if siguiente:
        return HttpResponseRedirect(siguiente)
    return redirect("panel_web:usuarios_lista")
