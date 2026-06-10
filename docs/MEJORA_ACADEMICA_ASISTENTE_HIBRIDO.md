# Mejora académica del asistente virtual híbrido de CommuSafe

## 1. Propósito de la mejora

El asistente virtual de CommuSafe fue concebido para orientar a residentes, vigilantes y administradores sobre el uso de la plataforma y sobre procedimientos relacionados con el conjunto residencial Remansos del Norte. Entre sus consultas esperadas se encuentran el reporte y seguimiento de incidentes, la consulta de avisos, las normas de convivencia, el manejo de visitantes, el uso de zonas comunes y los trámites administrativos.

Una primera aproximación basada principalmente en inteligencia artificial generativa permitía responder preguntas redactadas de distintas maneras, pero introducía riesgos que no eran convenientes para un sistema comunitario: dependencia de un proveedor externo, consumo de tokens incluso para preguntas frecuentes, respuestas variables ante la misma consulta y posibilidad de presentar información no verificada. Por esta razón, el asistente evolucionó hacia una arquitectura híbrida en la que el conocimiento local verificable es la primera opción y Gemini funciona únicamente como respaldo controlado.

La mejora no busca reemplazar completamente la IA generativa. Su propósito es asignarle una función proporcional al problema: las consultas conocidas y repetitivas se resuelven localmente; las preguntas ambiguas solicitan aclaración; las solicitudes fuera del dominio o que requieren confirmación reciben una respuesta segura; y solo las consultas pertinentes que no alcanzan suficiente confianza local pueden escalar a Gemini.

## 2. Problema de depender exclusivamente de IA generativa

Una integración directa con un modelo generativo presenta ventajas de flexibilidad lingüística, pero también varios riesgos técnicos y operativos:

- **Disponibilidad externa:** si el proveedor, la red o la cuota fallan, el asistente puede dejar de responder.
- **Consumo innecesario:** una pregunta frecuente puede consumir tokens cada vez que se formula, aunque su respuesta ya sea conocida.
- **Variabilidad:** dos consultas equivalentes pueden producir respuestas diferentes.
- **Información no verificada:** el modelo puede completar vacíos con datos plausibles, pero no registrados oficialmente.
- **Privacidad:** enviar conversaciones completas aumenta la cantidad de información expuesta a un tercero.
- **Trazabilidad limitada:** resulta difícil explicar por qué se produjo una respuesta determinada si toda la decisión depende del proveedor.
- **Dependencia tecnológica:** cambiar de proveedor o afrontar modificaciones de precio afecta directamente la operación.

En CommuSafe estos riesgos son relevantes porque el asistente orienta sobre procedimientos comunitarios y administrativos. Una respuesta convincente, pero incorrecta, puede causar más perjuicio que una aclaración prudente. La solución adoptada prioriza consistencia, verificabilidad y disponibilidad antes que responder todas las preguntas de forma automática.

## 3. Solución híbrida implementada

El asistente aplica una estrategia denominada **local-first**, o conocimiento local primero. Django continúa siendo el backend principal y coordina autenticación, roles, conversaciones, conocimiento, métricas y acceso opcional a Gemini.

```text
Usuario autenticado
  -> API REST de Django
  -> controles de seguridad, dominio y rol
  -> motor local de comprensión
       -> respuesta local verificada
       -> solicitud de aclaración
       -> respuesta segura
       -> candidato a respaldo generativo
  -> Gemini, solo si está permitido y es necesario
  -> persistencia del mensaje y trazabilidad técnica
```

Esta arquitectura conserva una única experiencia conversacional para el usuario. La persona no necesita conocer qué mecanismo produjo la respuesta. Internamente, el sistema registra el modo utilizado, la intención detectada, la confianza, la latencia y el uso estimado de tokens para permitir evaluación posterior.

## 4. Base de conocimiento local

La base de conocimiento contiene respuestas preparadas para consultas frecuentes del dominio de CommuSafe y Remansos del Norte. Actualmente organiza:

| Elemento | Cantidad |
|---|---:|
| Preguntas frecuentes o subintenciones | 108 |
| Intenciones principales | 20 |
| Categorías operativas | 12 |
| Entradas verificadas en el catálogo evaluado | 100 |
| Entradas pendientes de validación administrativa | 8 |

Las categorías cubren, entre otros temas, incidentes, administración, convivencia, seguridad, visitantes, parqueaderos, mascotas, mantenimiento, notificaciones y uso de la aplicación.

Cada entrada conserva información necesaria para su uso y mantenimiento:

- Pregunta principal y variaciones naturales.
- Respuesta preparada.
- Categoría, intención y palabras clave.
- Roles autorizados.
- Fuente y estado de verificación.
- Fechas de vigencia.
- Responsable, historial de cambios y versión.

El conocimiento administrado en base de datos solo se presenta como oficial cuando está aprobado y vigente. Los borradores, contenidos en revisión, entradas rechazadas o respuestas vencidas no se publican. Cuando el sistema identifica preguntas frecuentes aún no cubiertas, las registra para revisión; no las convierte automáticamente en conocimiento oficial.

Este enfoque separa el conocimiento institucional de la lógica del programa. Por tanto, una respuesta puede ser creada, revisada, actualizada, desactivada o versionada sin modificar el código del asistente.

## 5. Comprensión local y modelo seleccionado

El término **modelo local** no se refiere a un modelo generativo de gran tamaño instalado en el servidor. En CommuSafe corresponde a un motor de comprensión y recuperación diseñado para un dominio específico. Combina:

1. Normalización de texto, tildes, puntuación y errores ortográficos frecuentes.
2. Coincidencia exacta con preguntas y variaciones conocidas.
3. Reglas de negocio de alta precisión.
4. Coincidencia por palabras clave.
5. Similitud semántica mediante TF-IDF.
6. Clasificación de intención.
7. Recuperación de la respuesta verificada correspondiente.
8. Caché aislada por texto normalizado y rol.

Para evitar seleccionar una estrategia por su rendimiento sobre los mismos datos usados para ajustarla, el conjunto de 720 ejemplos se separó en entrenamiento, validación y prueba:

| Partición | Ejemplos | Uso |
|---|---:|---|
| Entrenamiento | 480 | Ajuste de estrategias locales |
| Validación | 120 | Comparación y calibración de umbrales |
| Prueba reservada | 120 | Medición final con frases no usadas para entrenar |

Cada una de las 20 intenciones tiene 36 ejemplos. El conjunto incluye preguntas formales, informales, cortas, largas, con errores ortográficos y expresiones no técnicas. La validación automática no detectó frases repetidas entre particiones.

Se compararon palabras clave, TF-IDF por palabras, TF-IDF por caracteres, distintos ensambles y el motor híbrido de producción. El enfoque híbrido fue seleccionado porque obtuvo el mejor equilibrio entre generalización, trazabilidad y control de respuestas:

| Estrategia | F1 validación | F1 prueba | F1 desafío |
|---|---:|---:|---:|
| Palabras clave | 0.6000 | 0.6500 | 0.5714 |
| TF-IDF por palabras | 0.6583 | 0.6667 | 0.5714 |
| TF-IDF por caracteres | 0.6583 | 0.7000 | 0.5714 |
| Mejor ensamble TF-IDF evaluado | 0.6500 | 0.7083 | 0.5714 |
| Híbrido local de producción | 0.8583 | 0.9000 | 0.5714 |

El resultado de desafío se conserva por separado porque incluye consultas deliberadamente ambiguas, externas o que requieren validación. En estos casos, el objetivo correcto no siempre es clasificar y responder, sino reconocer la incertidumbre.

## 6. Función de Python y Flask

Python cumple dos funciones en la solución:

- Es el lenguaje del backend Django y de la lógica principal del asistente.
- Permite entrenar, comparar, evaluar y ejecutar los componentes locales de comprensión de texto.

El procesamiento autoritativo permanece dentro de Django porque allí se encuentran la autenticación, los roles, las conversaciones persistentes, el conocimiento aprobado y las reglas de negocio. Esta decisión evita duplicar lógica y mantiene una sola fuente de verdad.

Además, el proyecto incluye un servicio auxiliar desarrollado con Flask. Su función es ofrecer por HTTP capacidades especializadas de inferencia local, evaluación, procesamiento por lote y selección de modelos. Flask no reemplaza a Django ni es obligatorio para que el asistente funcione. Si se configura `COMMUSAFE_NLP_SERVICE_URL`, Django puede consultarlo; si no está disponible, continúa utilizando el motor local integrado.

En el estado actual de producción, el motor local interno de Django está activo y el servicio Flask es una capacidad opcional no configurada. Esta distinción es importante: Flask demuestra que el componente de comprensión puede separarse o escalarse en el futuro, pero no se presenta como un microservicio productivo actualmente desplegado.

## 7. Estrategia de confianza

El asistente no trata todas las predicciones como igualmente confiables. La estrategia de decisión usa confianza y ambigüedad para elegir una de cuatro acciones:

| Decisión | Comportamiento |
|---|---|
| Respuesta local | Entrega una respuesta aprobada cuando la confianza es alta y no existe ambigüedad relevante. |
| Aclaración | Presenta opciones o solicita más contexto cuando hay varias interpretaciones posibles. |
| Respuesta segura | Reconoce límites ante consultas externas, sensibles o sin información verificable. |
| Respaldo generativo | Permite consultar Gemini cuando la pregunta pertenece al dominio, pero el conocimiento local no es suficiente. |

Los umbrales actuales se calibraron sobre validación y casos de desafío:

- Respuesta local directa: confianza igual o superior a `0.52`, sin ambigüedad.
- Aclaración: confianza igual o superior a `0.28` o candidatos cercanos.
- Margen de ambigüedad entre intenciones: `0.04`.
- Posible respaldo generativo: confianza inferior a `0.28`, únicamente dentro del dominio.

Esta política es deliberadamente conservadora. En un contexto residencial es preferible pedir una aclaración o recomendar confirmar con administración antes que presentar como oficial una respuesta dudosa.

## 8. Uso controlado de Gemini

Gemini se mantiene desacoplado del motor local y se usa únicamente como respaldo. Una consulta puede llegar al proveedor si cumple todas estas condiciones:

1. Pertenece al dominio de CommuSafe o Remansos del Norte.
2. No existe una respuesta local con confianza suficiente.
3. No es un intento de manipulación, acceso indebido o extracción de información.
4. El respaldo generativo está habilitado.
5. Existen credenciales privadas y cuota disponible.
6. El proveedor responde dentro del tiempo máximo permitido.

El contexto enviado se limita a información verificada y a una ventana compacta del historial. El sistema no envía claves, datos personales innecesarios ni la conversación completa. También aplica límites por hora, día, tokens estimados, tiempo de espera y tamaño de salida.

Antes de aceptar una respuesta generativa, el backend verifica que no esté vacía, que permanezca dentro del dominio y que no afirme como oficiales valores o decisiones administrativas no registradas. Si Gemini falla, supera la cuota o produce una respuesta insegura, el usuario recibe orientación prudente y el error se registra sin exponer detalles técnicos.

## 9. Persistencia, aislamiento y seguridad

Las conversaciones y sus mensajes se almacenan en PostgreSQL. Cada conversación pertenece a un usuario autenticado y los endpoints filtran los registros por propietario. De esta manera, dos usuarios pueden usar el asistente simultáneamente sin compartir mensajes ni historiales.

El asistente también aplica:

- Autenticación obligatoria.
- Control por rol para respuestas y métricas internas.
- Bloqueo transaccional al registrar mensajes concurrentes.
- Caché con copias defensivas para evitar contaminación entre solicitudes.
- Límites de solicitudes por usuario.
- Detección de intentos de revelar instrucciones, claves o datos privados.
- Redacción de secretos, correos y teléfonos en registros técnicos.
- Protección del servicio Flask para uso local o mediante clave interna.

Estas medidas no eliminan todos los riesgos posibles, pero reducen los escenarios más relevantes para el alcance del proyecto y dejan trazabilidad para investigar fallos.

## 10. Estrategia de pruebas

La evaluación combina pruebas unitarias, integración, seguridad, resiliencia, concurrencia y regresión. Los proveedores externos se sustituyen por mocks durante las pruebas automatizadas para evitar costos y exposición de información.

Los casos incluyen:

- Preguntas conocidas y variaciones nuevas.
- Errores ortográficos y lenguaje no técnico.
- Preguntas ambiguas y fuera del dominio.
- Intentos de obtener información no autorizada.
- Gemini deshabilitado, sin cuota o con error.
- Persistencia y aislamiento de conversaciones.
- Solicitudes simultáneas con diferentes roles.
- Consistencia de respuestas locales.
- Ausencia de consumo externo para preguntas conocidas.

Resultados automatizados consolidados:

| Suite o escenario | Resultado |
|---|---:|
| Pruebas del módulo asistente | 77 pruebas y 8 subpruebas aprobadas |
| Regresión completa del backend | 206 pruebas y 14 subpruebas aprobadas |
| Solicitudes concurrentes del motor local | 600 de 600 exitosas |
| Errores en prueba concurrente | 0 |
| Contaminaciones de caché | 0 |

La prueba de concurrencia simula 20 trabajadores y solicitudes de residentes, vigilantes y administradores. Evalúa el motor local en el equipo de prueba; no sustituye una prueba distribuida de larga duración sobre infraestructura de producción.

## 11. Métricas y resultados

La medición principal usa las 120 preguntas del conjunto de prueba reservado y no llama a Gemini:

| Indicador | Resultado |
|---|---:|
| Precisión micro | 90.00 % |
| Recall macro | 90.00 % |
| F1 macro | 91.82 % |
| Respuesta local directa | 74 de 120, equivalente a 61.67 % |
| Solicitud de aclaración | 35 de 120, equivalente a 29.17 % |
| Respuesta segura | 5 de 120, equivalente a 4.17 % |
| Candidata a respaldo Gemini | 6 de 120, equivalente a 5.00 % |
| Decisiones que evitaron Gemini | 114 de 120, equivalente a 95.00 % |
| Llamadas reales a Gemini durante la evaluación | 0 |
| Respuestas locales directas incorrectas observadas | 0 |
| Consistencia en tres repeticiones | 100.00 % |

La cobertura local directa de 61.67 % no debe confundirse con el 95 % de dependencia evitada. El primer valor representa preguntas respondidas directamente con conocimiento local. El segundo también incluye aclaraciones y respuestas seguras que evitaron enviar una consulta innecesaria o riesgosa al proveedor.

El ahorro estimado fue de 348 612 tokens externos para el conjunto evaluado, con un promedio estimado de 3 058 tokens por consulta que evitó el proveedor. Esta cifra proviene del estimador interno y sirve para comparar estrategias; no corresponde a una factura real de Google.

En una observación complementaria de producción de 24 horas se registraron tres consultas, todas resueltas sin Gemini, y un ahorro estimado de 9 281 tokens. La muestra es demasiado pequeña para generalizar el comportamiento futuro y se presenta únicamente como evidencia de que la política local-first está activa en producción.

## 12. Interpretación de los resultados

Las métricas respaldan tres conclusiones técnicas:

1. El conocimiento local y las reglas híbridas resuelven una proporción importante de consultas sin depender de IA generativa.
2. El uso de aclaraciones reduce el riesgo de responder directamente cuando la intención no es suficientemente clara.
3. La combinación híbrida generaliza mejor en el conjunto evaluado que cada estrategia local aislada.

El resultado no significa que el asistente comprenda cualquier pregunta ni que Gemini sea innecesario. Las intenciones con menor F1 fueron gestión de avisos, clasificación de incidentes, reporte de incidentes y trámites administrativos. Las principales confusiones aparecen cuando una frase es demasiado corta o puede referirse tanto a un aviso como a un incidente.

## 13. Limitaciones

La evaluación tiene limitaciones que deben declararse ante el jurado:

- El dataset fue construido a partir del dominio y de las preguntas frecuentes de CommuSafe. Puede representar mejor las consultas previstas que expresiones completamente nuevas de usuarios reales.
- El conjunto de desafío contiene siete casos; debe ampliarse con consultas reales anonimizadas.
- La ausencia de respuestas directas incorrectas se observó en el conjunto evaluado y no garantiza error cero en operación futura.
- Las métricas de latencia local se obtuvieron con el motor cargado en el equipo de prueba. No equivalen al tiempo total del endpoint ni incluyen red o arranque en frío.
- La prueba concurrente valida aislamiento del motor local, pero no reemplaza pruebas distribuidas prolongadas.
- El ahorro de tokens es una estimación interna.
- La muestra operativa de producción de tres consultas es insuficiente para estimar porcentajes generales.
- El servicio Flask está implementado como opción arquitectónica, pero no está configurado actualmente en producción.
- La base de conocimiento requiere revisión continua cuando cambien normas, horarios, contactos o procedimientos.

## 14. Conclusiones

La mejora convierte al asistente de CommuSafe en una solución híbrida más controlable y defendible para el contexto del proyecto. El sistema conserva la flexibilidad de Gemini para casos no cubiertos, pero evita utilizarlo como respuesta automática para toda consulta. La base de conocimiento local aporta consistencia y trazabilidad; el motor entrenado mejora la comprensión de variaciones; y la estrategia de confianza permite reconocer incertidumbre antes de responder.

La evidencia disponible demuestra reducción de dependencia generativa en el conjunto evaluado, aislamiento entre usuarios, persistencia de conversaciones y funcionamiento seguro cuando el proveedor externo no está disponible. Estas conclusiones se limitan a las pruebas ejecutadas y no sustituyen la evaluación futura con una muestra mayor de usuarios reales.

## 15. Recomendaciones

- Recopilar consultas reales anonimizadas y aprobadas para ampliar los conjuntos de validación, prueba y desafío.
- Revisar periódicamente las intenciones con menor F1 y ajustar ejemplos sin reutilizar frases entre particiones.
- Mantener un flujo administrativo de revisión, aprobación, vigencia y versionado del conocimiento.
- Medir durante periodos más largos la cobertura local, aclaraciones, uso de Gemini, latencia y satisfacción del usuario.
- Configurar alertas de cuota y disponibilidad antes de aumentar el uso del respaldo generativo.
- Ejecutar pruebas de carga sobre el entorno desplegado si aumenta el número de usuarios.
- Evaluar el despliegue separado de Flask únicamente si las mediciones demuestran que aporta una ventaja operativa.
- Conservar respuestas prudentes para información que dependa de confirmación administrativa.

## 16. Evidencia reproducible

El resultado consolidado puede regenerarse sin usar IA externa:

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py generar_evidencia_tecnica_asistente
.\.venv\Scripts\python.exe -m pytest asistente -q
```

Documentos y artefactos relacionados:

- `docs/ASISTENTE_HIBRIDO.md`: arquitectura técnica detallada.
- `docs/AUDITORIA_ASISTENTE_VIRTUAL.md`: hallazgos, riesgos y controles aplicados.
- `docs/GESTION_CONOCIMIENTO_ASISTENTE.md`: mantenimiento y aprobación del conocimiento.
- `docs/PRUEBAS_ASISTENTE_HIBRIDO.md`: estrategia de pruebas y criterios de aceptación.
- `docs/SEGURIDAD_ASISTENTE.md`: controles de seguridad.
- `docs/evidencias/asistente_evidencia_tecnica_2026.md`: resumen de métricas para sustentación.
- `docs/evidencias/asistente_evidencia_tecnica_2026.json`: métricas completas, matriz de confusión y errores.
