# Guía de demostración académica del asistente híbrido

## Objetivo

Este recorrido permite demostrar el valor técnico de CommuBot sin depender de explicaciones improvisadas. La presentación evidencia que el asistente:

- Responde preguntas conocidas con conocimiento local verificado.
- Comprende variaciones naturales y errores ortográficos.
- Solicita aclaración cuando una pregunta es ambigua.
- Usa Gemini únicamente como respaldo controlado.
- Responde de forma segura cuando una consulta está fuera del dominio.
- Registra métricas de uso y ahorro estimado de tokens.
- Mantiene aislamiento al atender solicitudes concurrentes de diferentes roles.

## Preparación antes de la sustentación

Desde la raíz del repositorio:

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe -m pytest asistente -q
```

La salida esperada actualmente es:

```text
System check identified no issues
80 passed, 16 subtests passed
```

La cantidad puede aumentar si se agregan nuevas pruebas. Lo importante es que no existan fallos.

La regresión completa verificada para esta preparación fue:

```text
209 passed, 22 subtests passed
```

## Prevalidación completa

Ejecutar antes de presentar:

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py demostrar_asistente_hibrido --usar-gemini --solicitudes 60 --workers 6 --json ..\docs\evidencias\asistente_demo_academica.json
```

El comando:

1. Verifica seis comportamientos representativos.
2. Ejecuta una única llamada real y controlada a Gemini.
3. Muestra las métricas registradas durante las últimas 24 horas.
4. Simula solicitudes concurrentes de residentes, vigilantes y administradores.
5. Guarda evidencia JSON sin incluir credenciales.
6. Termina con `ASISTENTE LISTO PARA LA DEMOSTRACION ACADEMICA` si todos los criterios se cumplen.

Para ensayar sin consumir Gemini:

```powershell
.\.venv\Scripts\python.exe manage.py demostrar_asistente_hibrido --solicitudes 60 --workers 6
```

## Recorrido recomendado ante el jurado

### 1. Explicar la decisión arquitectónica

Mensaje sugerido:

> CommuBot no envía todas las preguntas a una IA generativa. Primero consulta conocimiento local aprobado y aplica un modelo de comprensión. Solo cuando la consulta pertenece al dominio, pero no existe suficiente confianza local, habilita Gemini como respaldo.

Mostrar:

- `docs/MEJORA_ACADEMICA_ASISTENTE_HIBRIDO.md`
- `docs/evidencias/asistente_evidencia_tecnica_2026.md`

### 2. Pregunta conocida respondida localmente

Pregunta:

```text
¿Cómo reporto un incidente?
```

Resultado esperado:

- Acción local: `answer`.
- Método: `coincidencia_exacta`.
- Proveedor final: `local`.
- No consume Gemini.

Explicación sugerida:

> Esta pregunta ya tiene conocimiento verificado. La respuesta es consistente, trazable y no consume tokens externos.

### 3. Variación natural de redacción

Pregunta:

```text
Parce, no puedo entrar a la cuenta, ¿qué hago?
```

Resultado esperado:

- Acción local: `answer`.
- Intención: `acceso_sesion`.
- Método: `regla_negocio`.

Explicación sugerida:

> El usuario no necesita escribir exactamente una pregunta frecuente. La normalización y las reglas reconocen lenguaje informal.

También puede mostrarse el error ortográfico:

```text
Komo reporto un insidente
```

### 4. Pregunta ambigua

Pregunta:

```text
Música alta
```

Resultado esperado:

- Acción local: `clarify`.
- El asistente presenta opciones o solicita más contexto.

Explicación sugerida:

> En lugar de asumir una intención y entregar una respuesta posiblemente incorrecta, CommuBot reconoce la ambigüedad y solicita aclaración.

### 5. Gemini como respaldo controlado

Pregunta:

```text
¿Cuál es el procedimiento oficial para activar un código QR temporal biométrico en portería?
```

Resultado esperado:

- Decisión local previa: `fallback_allowed`.
- Confianza local aproximada: `0.225`.
- Resultado final: modo `ia`.
- Proveedor: `gemini`.
- Modelo: `gemini-2.5-flash-lite`.
- La respuesta reconoce que no encuentra información oficial y recomienda validar con administración o portería.

Explicación sugerida:

> El motor local reconoce que la consulta pertenece al contexto del conjunto, pero no dispone de una respuesta aprobada. Solo entonces consulta Gemini. La respuesta generada debe pasar validaciones de dominio y prudencia antes de mostrarse.

Si Gemini no está disponible, el sistema entrega una respuesta segura. Esto no rompe el chat, pero la prevalidación debe ejecutarse antes de presentar para confirmar conectividad y cuota.

### 6. Consulta desconocida y respuesta segura

Pregunta:

```text
¿Quién ganó el partido de fútbol ayer?
```

Resultado esperado:

- Acción: `safe`.
- Método: `fuera_de_dominio`.
- Proveedor: `local`.
- Gemini no se utiliza.

Explicación sugerida:

> El asistente está limitado a CommuSafe y Remansos del Norte. No intenta responder temas externos ni desperdicia una llamada generativa.

### 7. Métricas y ahorro de tokens

El comando muestra:

- Consultas totales.
- Consultas resueltas sin Gemini.
- Aclaraciones.
- Uso de IA externa y Gemini.
- Tokens estimados usados.
- Tokens estimados ahorrados.
- Porcentaje de consultas sin Gemini.

Mensaje sugerido:

> Estas métricas provienen de los logs técnicos del asistente. El ahorro es una estimación interna para comparar estrategias, no una factura real del proveedor.

Para mostrar métricas desde la API, iniciar sesión como administrador y consultar:

```text
GET /api/asistente/health/
```

### 8. Funcionamiento con varios usuarios

El comando ejecuta solicitudes concurrentes con roles `RESIDENTE`, `VIGILANTE` y `ADMINISTRADOR`. Mostrar:

- Todas las solicitudes exitosas.
- Cero errores.
- Cero contaminaciones de caché.
- `aislamiento_aprobado: true`.

La separación real de conversaciones por propietario se verifica con:

```powershell
.\.venv\Scripts\python.exe -m pytest asistente -q -k "dos_usuarios_no_mezclan or lista_solo_conversaciones or no_permite_acceder"
```

Explicación sugerida:

> La prueba concurrente verifica que el motor no comparta resultados mutables entre solicitudes. Las pruebas de integración verifican además que cada usuario solo pueda consultar sus propias conversaciones y mensajes.

## Resultados técnicos que pueden mostrarse

La evidencia consolidada vigente registra:

| Indicador | Resultado |
|---|---:|
| Precisión micro en prueba reservada | 90.00 % |
| F1 macro en prueba reservada | 91.82 % |
| Precisión micro en holdout final no ajustado | 55.00 % |
| Cobertura local directa | 61.67 % |
| Dependencia de Gemini evitada | 95.00 % |
| Respuestas directas incorrectas observadas | 0 |
| Solicitudes concurrentes evaluadas | 600 |
| Errores concurrentes | 0 |
| Contaminaciones de caché | 0 |

El challenge de desarrollo fue usado para corregir el motor y no debe presentarse como evidencia independiente. El holdout final no fue usado para ajustes posteriores. Estos resultados no son una garantía universal ni sustituyen pruebas futuras con usuarios reales.

## Orden de archivos para mostrar

1. `docs/MEJORA_ACADEMICA_ASISTENTE_HIBRIDO.md`
2. `docs/evidencias/asistente_evidencia_tecnica_2026.md`
3. `docs/evidencias/asistente_demo_academica.json`
4. `backend/asistente/local_engine.py`
5. `backend/asistente/services.py`
6. `backend/asistente/management/commands/demostrar_asistente_hibrido.py`

## Cierre sugerido

> La mejora híbrida no busca afirmar que la IA generativa sea innecesaria. Busca utilizarla únicamente donde aporta valor. Las preguntas conocidas se resuelven de forma local, las ambiguas se aclaran, las externas se rechazan de manera segura y Gemini queda disponible como respaldo controlado para consultas pertinentes no cubiertas.
