# Modelo de Desarrollo Incremental de CommuSafe

## 1. Enfoque metodologico

CommuSafe se desarrolla bajo el modelo incremental. Esto significa que el sistema no se construye como un unico bloque al final del proyecto, sino mediante incrementos funcionales acumulativos. Cada sprint entrega una parte util, verificable e integrada con lo construido anteriormente.

El proyecto usa este modelo porque permite controlar mejor el riesgo tecnico, validar progresivamente los modulos principales y demostrar avance real en cada etapa del trabajo de grado.

## 2. Como se aplica en el proyecto

Cada incremento agrega valor funcional concreto:

- Primero se define la arquitectura, el modelo de datos y la vision completa del sistema.
- Luego se construye la base del backend, autenticacion y usuarios.
- Despues se implementa el modulo central de incidentes.
- Mas adelante se agregan notificaciones, asistente virtual y panel web.
- Finalmente se desarrolla la app movil por capas: estructura, autenticacion, incidentes, notificaciones, asistente y cierre de calidad.

Cada modulo queda integrado con los anteriores antes de avanzar. Por ejemplo, el modulo de incidentes depende del usuario autenticado; las notificaciones dependen de incidentes; la app movil depende de la API; y las pruebas finales dependen de todo el sistema ya conectado.

## 3. Incrementos principales

| Incremento | Sprints | Resultado acumulado |
| --- | --- | --- |
| Base conceptual | Sprint 0 | Arquitectura, datos, diseno y ruta tecnica definidos. |
| Backend base | Sprint 1 | Django configurado, usuario personalizado y autenticacion JWT. |
| Nucleo de negocio | Sprint 2 | Gestion completa de incidentes, evidencias e historial. |
| Servicios inteligentes | Sprint 3 | Notificaciones y asistente virtual con IA. |
| Gestion web | Sprint 4 | Panel administrativo funcional para administradores y vigilantes. |
| Base movil | Sprint 5 | App Flutter estructurada, navegacion y servicios base. |
| Experiencia movil autenticada | Sprint 6 | Login, perfil y sesion segura en Android. |
| Operacion movil | Sprint 7 | Lista, creacion y detalle de incidentes desde la app. |
| Comunicacion movil | Sprint 8 | Notificaciones, chat IA y contactos de emergencia. |
| Consolidacion | Sprint 9 | Pruebas, datos demo y preparacion de sustentacion. |
| Entrega final | Sprint 10 | Despliegue, README final y checklist de entrega. |

## 4. Razones para usar el modelo incremental

- Permite entregar avances funcionales desde etapas tempranas.
- Reduce el riesgo de descubrir errores importantes solo al final.
- Facilita la validacion por modulo: backend, panel web y app movil.
- Permite integrar progresivamente reglas de negocio reales.
- Hace mas clara la sustentacion, porque se puede explicar como el sistema fue creciendo por incrementos.
- Se ajusta al contexto academico del trabajo de grado, donde es importante mostrar trazabilidad del proceso.

## 5. Evidencia del enfoque incremental

La evidencia del modelo incremental se observa en:

- La division del proyecto en sprints secuenciales.
- La dependencia explicita entre entregables.
- La construccion por capas: documentacion, backend, panel web, app movil, pruebas y despliegue.
- La integracion continua entre modulos al terminar cada sprint.
- La verificacion funcional de cada incremento antes de continuar.

## 6. Relacion con la arquitectura

La arquitectura de CommuSafe tambien responde al modelo incremental. Se eligio un monolito modular en Django y una app Flutter organizada por features porque esta estructura permite agregar nuevas capacidades sin romper lo anterior.

Cada app de Django y cada feature de Flutter representa una unidad funcional que puede evolucionar por incrementos. Esta decision mantiene el proyecto ordenado, entendible y facil de presentar ante el jurado.

## 7. Conclusion

CommuSafe no se plantea como un desarrollo lineal de una sola entrega final. El sistema se construye mediante incrementos funcionales, donde cada sprint produce una version mas completa, estable e integrada de la plataforma.

Por esta razon, el modelo incremental es el enfoque metodologico principal de todo el proyecto.
