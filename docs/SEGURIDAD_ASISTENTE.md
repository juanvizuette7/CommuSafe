# Seguridad del asistente hibrido de CommuSafe

## Alcance

Este documento registra las medidas aplicadas al backend del asistente virtual CommuBot para proteger conversaciones, consultas, metricas, contexto, base de conocimiento y uso de IA externa. No se realizaron cambios de frontend.

## Medidas aplicadas

| Riesgo | Medida aplicada | Resultado |
|---|---|---|
| Exposicion de metricas internas | `/api/asistente/health/` entrega informacion detallada solo a administradores, vigilantes o staff. Residentes reciben un estado operativo simple. | Evita exponer cache, modelo, cuotas y metricas tecnicas a usuarios finales. |
| Manipulacion del contexto | El endpoint legado marca el historial enviado por cliente como no confiable. Solo conserva mensajes de usuario, descarta instrucciones sospechosas y limita volumen. | Un cliente no puede inyectar mensajes falsos del asistente para alterar la IA. |
| Prompt injection | Se detectan frases como ignorar instrucciones, revelar prompt, mostrar claves, token JWT, API key o modo desarrollador. | El asistente responde de forma segura sin llamar a Gemini/Anthropic. |
| Secretos en logs tecnicos | `AsistenteRespuestaLog.mensaje` redacted emails, telefonos colombianos, API keys, tokens y claves antes de persistir. | La trazabilidad no conserva secretos pegados accidentalmente por usuarios. |
| Preguntas ambiguas | Las aclaraciones muestran opciones numeradas y naturales dentro de la respuesta. | El usuario puede elegir una opcion sin ver detalles tecnicos. |
| Informacion pendiente de validacion | Las respuestas que requieren confirmacion administrativa agregan una nota clara si la respuesta original no lo indicaba. | El asistente evita presentar datos no confirmados como definitivos. |
| Dependencia de IA externa | Gemini/Anthropic siguen siendo respaldo controlado y no se usan para preguntas conocidas ni intentos de manipulacion. | Menor consumo, menos riesgo de respuestas inventadas. |
| Aislamiento por rol | Las conversaciones se filtran por `usuario=request.user`; residentes solo tienen contexto agregado de sus propios incidentes. | Un usuario no puede leer conversaciones ni contexto de otro usuario. |
| Abuso del asistente | Se conservan throttles por usuario para chat y lectura. | Reduce spam y consumo innecesario de procesamiento/IA. |

## Flujo seguro de respuesta

1. Se valida y limpia el mensaje recibido.
2. Si el mensaje intenta manipular instrucciones, revelar secretos o pedir datos internos, se responde localmente con una negativa segura.
3. Se intenta respuesta local con base de conocimiento verificada.
4. Si hay ambiguedad, se devuelve aclaracion con opciones utiles.
5. Si falta informacion verificada, se orienta a confirmar con administracion.
6. Solo si el caso pertenece al dominio y no hay respuesta local suficiente, se usa IA externa con historial filtrado, timeout, cuota y validacion de salida.
7. La respuesta se registra con datos sensibles redactados.

## Pruebas verificadas

Comando:

```powershell
cd backend
python -m pytest asistente/tests.py -q
```

Resultado:

```text
75 passed, 8 subtests passed
```

Prueba de resiliencia:

```powershell
python manage.py probar_resiliencia_asistente --requests 80 --workers 8
```

Resultado real:

```text
240 solicitudes, 12 workers, 240 exitosas, 0 errores, 0 contaminaciones de cache, p95 1.788 ms, sin uso de IA externa.
```

Casos cubiertos:

- Residentes no reciben metricas internas del health.
- Administradores reciben health detallado.
- Prompt injection no llega a IA externa.
- Secretos pegados por usuario se redactan en logs.
- Historial legado no confiable no suplanta mensajes del asistente.
- Aclaraciones muestran opciones utiles.
- Consultas fuera del dominio reciben respuesta segura.

## Consideraciones de operacion

- El servicio Flask auxiliar debe permanecer en `127.0.0.1` o protegido con `COMMUSAFE_NLP_SERVICE_KEY`.
- Las variables `GEMINI_API_KEY`, `LLM_API_KEY`, `SECRET_KEY` y credenciales Firebase deben configurarse solo por variables de entorno.
- Las conversaciones persistentes son datos de usuario y deben tratarse como informacion privada.
- Si administracion cambia horarios, telefonos o reglas internas, la base local debe actualizarse y validarse con `python manage.py validar_base_conocimiento`.
