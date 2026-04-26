# Plan de Desarrollo de CommuSafe

## 1. Enfoque general

CommuSafe se desarrolla bajo el modelo incremental. Cada sprint representa un incremento funcional que se construye sobre los incrementos anteriores, se integra con el sistema existente y deja una version mas completa del producto.

El proyecto no sigue una entrega unica al final. La estrategia consiste en avanzar por capas: primero documentacion y arquitectura, luego backend, despues panel web, posteriormente app movil y finalmente pruebas, datos de demostracion y despliegue. Esta organizacion permite validar el sistema progresivamente y reducir riesgos tecnicos.

La ruta de desarrollo se ejecutará en 11 sprints numerados del 0 al 10. Aunque el enunciado los llama "10 sprints", el alcance definido incluye explícitamente desde Sprint 0 hasta Sprint 10, por lo que la planificación real contempla once iteraciones.

La secuencia está organizada para minimizar retrabajo:

- Primero se fija arquitectura y documentación.
- Luego se consolida el backend y sus reglas de negocio.
- Después se construye la interfaz web administrativa.
- Finalmente se desarrolla la app Flutter y se cierra con pruebas, demo y despliegue.

Documento metodologico relacionado:

- `docs/MODELO_INCREMENTAL.md`

## 1.1 Aplicacion del modelo incremental

El modelo incremental se evidencia en que ningun sprint queda aislado:

- Sprint 1 usa la arquitectura definida en Sprint 0.
- Sprint 2 usa usuarios y autenticacion del Sprint 1.
- Sprint 3 usa eventos de incidentes del Sprint 2.
- Sprint 4 administra visualmente los datos del backend ya construido.
- Sprint 5 prepara la base movil para consumir la API.
- Sprint 6 conecta la app movil con autenticacion real.
- Sprint 7 agrega incidentes moviles sobre la autenticacion y API existentes.
- Sprint 8 incorpora comunicacion y asistencia sobre los modulos previos.
- Sprint 9 valida el producto completo.
- Sprint 10 formaliza entrega y despliegue.

Asi, cada incremento aporta funcionalidad nueva sin reemplazar lo anterior.

## 2. Sprints del proyecto

### Sprint 0: Arquitectura y documentación base

Objetivo:

- Definir la arquitectura completa del sistema, el modelo de datos, la ruta de trabajo y la identidad visual.

Entregables:

- `docs/ARQUITECTURA.md`
- `docs/MODELO_DATOS.md`
- `docs/PLAN_DESARROLLO.md`
- `docs/DISENO.md`

Dependencias:

- No depende de sprints previos.
- Es prerequisito de todos los sprints posteriores.

### Sprint 1: Entorno, configuración Django, modelo de usuario y autenticación JWT

Objetivo:

- Inicializar backend Django y dejar autenticación funcional para todos los roles.

Entregables:

- Proyecto Django configurado.
- Apps base creadas.
- Modelo de usuario personalizado.
- Endpoints de login, refresh, perfil y cambio de contraseña.
- Configuración de archivos, variables de entorno y estructura inicial.

Dependencias:

- Requiere Sprint 0 para seguir el diseño y modelo definido.

### Sprint 2: Módulo completo de incidentes (backend)

Objetivo:

- Implementar la lógica central de incidentes con evidencias, historial y reglas de estado.

Entregables:

- Modelos `Incidente`, `EvidenciaIncidente`, `HistorialEstado`.
- Serializers, servicios, permisos y vistas REST.
- Cálculo automático de prioridad.
- Flujo de estados validado.
- Pruebas del dominio de incidentes.

Dependencias:

- Requiere Sprint 1 por el modelo de usuario y autenticación.

### Sprint 3: Módulo de notificaciones push y asistente virtual IA

Objetivo:

- Agregar comunicación proactiva al usuario y respuestas automatizadas para consultas frecuentes.

Entregables:

- Modelo y endpoints de `Notificacion`.
- Registro de tokens FCM.
- Servicio de envío push.
- Integración con Anthropic Claude Haiku.
- Endpoint del asistente virtual.

Dependencias:

- Requiere Sprint 2 porque las notificaciones y el asistente se apoyan en eventos e información del dominio ya construido.

### Sprint 4: Panel web administrativo con Django + Tailwind

Objetivo:

- Construir el panel web con experiencia profesional para administración y seguimiento.

Entregables:

- Layout base del panel.
- Dashboard con métricas.
- Gestión de usuarios.
- Listado, detalle y cierre administrativo de incidentes.
- Componentes visuales alineados con la identidad de diseño.

Dependencias:

- Requiere Sprint 1 para autenticación administrativa.
- Requiere Sprint 2 para gestión de incidentes.
- Requiere Sprint 3 para mostrar notificaciones y métricas enriquecidas.

### Sprint 5: Estructura base de la aplicación Flutter

Objetivo:

- Preparar la app móvil con arquitectura sólida, tema visual y base de navegación.

Entregables:

- Proyecto Flutter inicializado.
- Estructura por features.
- Configuración de cliente HTTP y almacenamiento seguro.
- Tema visual y componentes base.
- Navegación según autenticación y rol.

Dependencias:

- Requiere Sprint 0 para respetar arquitectura y diseño visual.
- Se apoya en la API ya definida en sprints anteriores.

### Sprint 6: Módulo de autenticación y perfil en Flutter

Objetivo:

- Conectar la app con la autenticación real del backend y exponer perfil del usuario.

Entregables:

- Pantallas de inicio de sesión.
- Gestión local de JWT.
- Restauración de sesión.
- Pantalla de perfil y cierre de sesión.
- Manejo visual de errores y estados de carga.

Dependencias:

- Requiere Sprint 1.
- Requiere Sprint 5.

### Sprint 7: Módulo de incidentes en Flutter

Objetivo:

- Permitir a residentes reportar incidentes y a vigilantes atenderlos desde la app.

Entregables:

- Formulario de creación con evidencias.
- Listado de incidentes.
- Detalle con historial.
- Vistas operativas para vigilantes.
- Integración completa con endpoints de incidentes.

Dependencias:

- Requiere Sprint 2 para endpoints funcionales.
- Requiere Sprint 5 y Sprint 6 para la base móvil y autenticación.

### Sprint 8: Módulo de notificaciones, chat IA y contactos de emergencia en Flutter

Objetivo:

- Completar la experiencia móvil con comunicación, asistencia y acceso rápido a ayuda.

Entregables:

- Bandeja de notificaciones.
- Recepción de push con FCM.
- Pantalla de chat con asistente virtual.
- Pantalla de contactos de emergencia.
- Navegación contextual desde notificaciones hacia incidentes.

Dependencias:

- Requiere Sprint 3 por servicios de notificación e IA.
- Requiere Sprint 7 para enlazar incidentes desde notificaciones.

### Sprint 9: Pruebas, datos de demostración y preparación para presentación

Objetivo:

- Consolidar calidad técnica y preparar un flujo demostrable ante jurado.

Entregables:

- Pruebas backend y mobile de escenarios críticos.
- Datos semilla de demostración.
- Ajustes de UX y textos.
- Casos de uso listos para exposición.

Dependencias:

- Requiere que backend, panel y móvil estén funcionales hasta Sprint 8.

### Sprint 10: Despliegue, README final y checklist de entrega

Objetivo:

- Preparar el proyecto para ejecución reproducible, entrega académica y despliegue controlado.

Entregables:

- Configuración para producción.
- Ajustes de PostgreSQL.
- README principal del proyecto.
- Checklist de instalación, demo y sustentación.
- Revisión final de documentación y consistencia.

Dependencias:

- Requiere Sprint 9 por estabilidad y material de presentación.

## 3. Dependencia acumulada entre sprints

```text
Sprint 0
  -> Sprint 1
    -> Sprint 2
      -> Sprint 3
      -> Sprint 4
      -> Sprint 5
        -> Sprint 6
          -> Sprint 7
            -> Sprint 8
              -> Sprint 9
                -> Sprint 10
```

Interpretación:

- Sprint 4 depende de la madurez del backend.
- Sprint 5 puede iniciar después de fijar arquitectura y con la API estabilizada.
- Sprint 6, 7 y 8 dependen progresivamente del backend y de la base móvil.
- Sprint 9 consolida todo lo construido.
- Sprint 10 formaliza la entrega final.

## 4. Resultado esperado al final de la ruta

Al completar los sprints 0 a 10, CommuSafe debe contar con:

- Backend Django REST completamente funcional.
- Panel web administrativo moderno y presentable.
- App Flutter Android operativa para residentes y vigilantes.
- Notificaciones push funcionando.
- Asistente virtual integrado.
- Datos demo y documentación suficiente para evaluación universitaria.
