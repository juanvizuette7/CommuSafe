"""Vistas del panel web administrativo."""

from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from incidentes.models import Incidente
from incidentes.serializers import CambiarEstadoSerializer
from incidentes.services import cambiar_estado_incidente
from usuarios.models import Usuario


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


def _opciones_estado_disponibles(usuario, incidente):
    if incidente.estado == Incidente.Estado.REGISTRADO:
        return [Incidente.Estado.EN_PROCESO]
    if incidente.estado == Incidente.Estado.EN_PROCESO:
        return [Incidente.Estado.RESUELTO]
    if incidente.estado == Incidente.Estado.RESUELTO and usuario.es_administrador:
        return [Incidente.Estado.CERRADO]
    return []


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Autentica al usuario y permite acceso solo a administradores y vigilantes."""

    if request.user.is_authenticated:
        if _es_usuario_panel(request.user):
            return redirect("panel_web:dashboard")
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
            return redirect("panel_web:dashboard")

    return render(
        request,
        "panel/login.html",
        {
            "page_title": "Iniciar sesión",
            "page_subtitle": "Acceso administrativo",
        },
    )


@require_GET
def inicio(request):
    """Redirige al login o al dashboard según el estado de sesión."""

    if request.user.is_authenticated and _es_usuario_panel(request.user):
        return redirect("panel_web:dashboard")
    return redirect("panel_web:login")


@require_POST
def logout_view(request):
    """Cierra la sesión del usuario del panel."""

    logout(request)
    messages.success(request, "La sesión se cerró correctamente.")
    return redirect("panel_web:login")


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
