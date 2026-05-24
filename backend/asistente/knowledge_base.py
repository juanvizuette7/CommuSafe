"""Base de conocimiento interna para CommuBot.

Este archivo centraliza la informacion operativa usada por el asistente virtual.
La estructura permite ampliar el contenido sin modificar la logica de servicios.
"""

KNOWLEDGE_BASE_SECTIONS = [
    {
        "titulo": "Identidad y alcance de CommuSafe",
        "items": [
            "CommuSafe es la plataforma digital de apoyo para la gestion comunitaria y de seguridad del conjunto residencial Remansos del Norte.",
            "Remansos del Norte esta ubicado en Pasto, Narino, y funciona como conjunto residencial cerrado.",
            "Los actores principales del sistema son residentes, propietarios, arrendatarios, administracion, vigilancia y personal de apoyo autorizado.",
            "El objetivo de CommuSafe es centralizar reportes, seguimiento de incidentes, avisos, notificaciones, datos basicos de usuarios y orientacion digital del conjunto.",
            "El asistente virtual responde como orientador digital del conjunto y debe limitarse a informacion registrada en CommuSafe o procedimientos propios de Remansos del Norte.",
        ],
    },
    {
        "titulo": "Horarios y atencion administrativa",
        "items": [
            "La administracion atiende de lunes a viernes de 8:00 a. m. a 5:00 p. m. y sabados de 8:00 a. m. a 12:00 m.",
            "Porteria y vigilancia mantienen atencion operativa permanente para novedades de ingreso, seguridad y apoyo inmediato.",
            "Las solicitudes administrativas pueden estar relacionadas con certificados, paz y salvos, cuotas, recibos, novedades de datos, permisos, reservas o aclaraciones de convivencia.",
            "Las solicitudes simples suelen revisarse primero por administracion; los casos que requieren validacion documental o decision administrativa pueden tomar mas tiempo.",
            "Para una solicitud clara se recomienda indicar nombre, unidad residencial, descripcion concreta, fecha aproximada, soporte disponible y medio de contacto actualizado.",
            "Cuando el sistema no tenga valores exactos de pagos, sanciones o saldos, el asistente debe sugerir validar directamente con administracion.",
        ],
    },
    {
        "titulo": "Gestion de incidentes en CommuSafe",
        "items": [
            "Un incidente es cualquier novedad que requiere registro, revision o seguimiento dentro del conjunto.",
            "Desde la app movil, el usuario puede crear un reporte en la pestaña Incidentes usando el boton Nuevo.",
            "El reporte debe incluir titulo claro, categoria, descripcion, ubicacion de referencia y evidencia fotografica si esta disponible.",
            "CommuSafe permite adjuntar hasta tres imagenes como evidencia por incidente.",
            "Las categorias principales registradas en el sistema son Seguridad, Convivencia, Infraestructura y Emergencia.",
            "Ejemplos de convivencia: ruido excesivo, conflictos entre vecinos, molestias por mascotas, uso inadecuado de zonas comunes o incumplimiento de horarios.",
            "Ejemplos de seguridad: ingreso no autorizado, personas sospechosas, cerraduras forzadas, vehiculos no autorizados o novedades en puntos de acceso.",
            "Ejemplos de infraestructura: iluminacion danada, puertas con falla, citofonos, pasillos, zonas verdes, limpieza, mantenimiento o danos en zonas comunes.",
            "Ejemplos de emergencia: olor a gas, conato de incendio, accidente, riesgo inmediato para personas, inundacion critica o situacion que requiere atencion urgente.",
            "Los estados operativos visibles pueden incluir registrado, en proceso, resuelto y cerrado; el asistente puede explicarlos como pendiente/en revision, en proceso, resuelto o cerrado segun el contexto del usuario.",
            "Vigilancia y administracion pueden actualizar estados con comentarios para dejar trazabilidad.",
            "Si un incidente se repite, el residente debe crear un nuevo reporte o agregar evidencia si el flujo disponible lo permite, mencionando que es una situacion recurrente.",
            "Los reportes deben redactarse de forma respetuosa, objetiva y verificable, evitando insultos, acusaciones personales sin soporte o datos sensibles innecesarios.",
            "La prioridad se determina automaticamente por categoria: Emergencia y Seguridad son prioridad alta, Convivencia es prioridad media e Infraestructura es prioridad baja.",
        ],
    },
    {
        "titulo": "Convivencia comunitaria",
        "items": [
            "La convivencia se basa en respeto, comunicacion clara, cuidado de zonas comunes y cumplimiento de horarios de descanso.",
            "El horario de descanso de referencia es de 10:00 p. m. a 6:00 a. m.; durante ese periodo deben evitarse ruidos, musica alta, golpes o actividades que afecten a otros residentes.",
            "Para reuniones o actividades sociales se recomienda avisar a los vecinos cercanos, controlar volumen, respetar horarios y dejar limpias las areas utilizadas.",
            "Los conflictos entre vecinos deben registrarse con lenguaje respetuoso, describiendo hechos, fechas, lugares y evidencias disponibles.",
            "Cuando haya una situacion sensible, el asistente debe recomendar evitar confrontaciones directas y usar los canales de administracion o vigilancia.",
            "Los problemas recurrentes de ruido, mascotas, parqueaderos o visitantes deben reportarse con historial claro para facilitar seguimiento.",
        ],
    },
    {
        "titulo": "Visitantes, domiciliarios y proveedores",
        "items": [
            "El residente debe autorizar o confirmar el ingreso de visitantes, domiciliarios o proveedores cuando vigilancia lo requiera.",
            "Los datos basicos utiles para autorizar ingreso son nombre del visitante, documento si aplica, unidad a la que se dirige, placa del vehiculo si ingresa con carro o moto, motivo de visita y hora aproximada.",
            "Para domiciliarios se recomienda estar atento al llamado de porteria y recibirlos en el punto autorizado si el procedimiento del conjunto lo exige.",
            "Para proveedores o personal externo se recomienda informar previamente el tipo de servicio, horario estimado y datos de contacto.",
            "Vigilancia puede solicitar confirmacion cuando el visitante no esta anunciado, los datos no coinciden, hay ingreso vehicular o existe una novedad de seguridad.",
            "Los residentes son responsables de orientar a sus visitantes sobre respeto de zonas comunes, parqueaderos y horarios.",
        ],
    },
    {
        "titulo": "Parqueaderos",
        "items": [
            "Los parqueaderos asignados deben usarse respetando limites, circulacion interna, senalizacion y espacios de otros residentes.",
            "Un vehiculo mal ubicado, sin autorizacion o bloqueando el paso puede reportarse como incidente de convivencia o seguridad segun el riesgo.",
            "Si un vehiculo bloquea el paso, se recomienda informar a porteria y registrar el reporte con ubicacion, placa si es visible y evidencia fotografica si es seguro tomarla.",
            "Los visitantes con vehiculo deben seguir la indicacion de vigilancia y ubicarse solo en espacios permitidos.",
            "Danos, rayones, cerraduras forzadas o novedades en parqueaderos deben reportarse indicando torre, zona, nivel o punto exacto de referencia.",
        ],
    },
    {
        "titulo": "Mascotas",
        "items": [
            "Las mascotas deben transitar con correa o control adecuado en zonas comunes.",
            "Los propietarios deben recoger excrementos y evitar que la mascota cause danos, ruidos persistentes o situaciones de riesgo.",
            "Si una mascota se extravia, el residente puede reportar la novedad con descripcion, foto, ultima ubicacion vista y datos de contacto.",
            "Si una mascota genera molestias por ruido, agresividad o falta de limpieza, el reporte debe ser respetuoso y describir frecuencia, hora y lugar.",
            "El asistente debe recomendar primero una comunicacion respetuosa si es viable y, si el problema persiste, registrar el incidente en CommuSafe.",
        ],
    },
    {
        "titulo": "Zonas comunes",
        "items": [
            "Las zonas comunes deben usarse con responsabilidad, limpieza y respeto por otros residentes.",
            "El horario de referencia para areas comunes es de 6:00 a. m. a 10:00 p. m., salvo indicacion administrativa diferente registrada por aviso.",
            "Si existe reserva de espacios, el residente debe validar disponibilidad y condiciones con administracion.",
            "Los danos en zonas comunes deben reportarse con ubicacion exacta, descripcion y evidencia si esta disponible.",
            "Despues de reuniones o actividades, los usuarios deben cuidar aseo, ruido y estado de los elementos comunes.",
            "El asistente no debe confirmar reservas, costos o disponibilidad exacta si no estan registrados en CommuSafe.",
        ],
    },
    {
        "titulo": "Mantenimiento, danos y evidencias",
        "items": [
            "Danos en iluminacion, puertas, cerraduras, citofonos, pasillos, zonas verdes, limpieza o zonas comunes se reportan desde Incidentes.",
            "CommuSafe no administra camaras de vigilancia como modulo funcional. La evidencia fotografica se refiere a imagenes adjuntas por usuarios al reportar incidentes.",
            "Para mantenimiento se recomienda indicar que elemento falla, donde esta ubicado, desde cuando ocurre, si afecta seguridad o movilidad y si hay evidencia.",
            "Un dano privado dentro de un apartamento normalmente debe gestionarse por el residente; un dano en pasillos, accesos, zonas verdes o elementos comunes puede registrarse como infraestructura.",
            "El seguimiento se consulta entrando al detalle del incidente, donde se muestra estado, historial y comentarios de responsables.",
        ],
    },
    {
        "titulo": "Avisos y comunicados",
        "items": [
            "Los avisos se consultan en la seccion Alertas o Notificaciones de CommuSafe.",
            "Los comunicados pueden tratar sobre mantenimiento, cortes de servicios, reuniones, pagos, recomendaciones de convivencia, novedades de seguridad o instrucciones administrativas.",
            "Un aviso informativo solo comunica una novedad; una solicitud con accion requerida indica que el residente debe realizar un paso concreto o contactar a administracion.",
            "Administracion y vigilancia pueden enviar avisos a todos o a usuarios seleccionados segun el flujo autorizado.",
            "Algunos avisos pueden programarse de forma recurrente por dias, por ejemplo recordatorios de recoleccion de basura o mantenimiento periodico.",
            "Es importante revisar avisos porque pueden contener cambios temporales de horarios, recomendaciones de seguridad o instrucciones del conjunto.",
        ],
    },
    {
        "titulo": "Pagos y temas administrativos",
        "items": [
            "El asistente puede orientar sobre el proceso general de consulta, pero no debe inventar valores de cuotas, saldos, intereses, multas o fechas exactas si no estan registrados.",
            "Para paz y salvos, certificados, recibos, novedades de cartera o confirmacion de pagos, se recomienda contactar a administracion por los canales oficiales del conjunto.",
            "Si el usuario pregunta por un valor exacto, la respuesta debe indicar que no se encuentra un valor exacto registrado en CommuSafe y sugerir validarlo con administracion.",
            "Las novedades de datos personales deben actualizarse por los canales habilitados en el sistema o solicitar apoyo a administracion.",
        ],
    },
    {
        "titulo": "Uso de la plataforma CommuSafe",
        "items": [
            "Para iniciar sesion se usa el correo registrado y la contrasena asignada por administracion o el responsable autorizado.",
            "Si el usuario no puede ingresar, debe verificar correo y contrasena; si el problema continua, debe solicitar apoyo a administracion.",
            "Para crear un reporte: entrar a Incidentes, tocar Nuevo, elegir categoria, escribir descripcion, agregar ubicacion, adjuntar evidencia opcional y enviar.",
            "Para consultar el estado de un reporte: abrir Incidentes, seleccionar el caso y revisar estado, historial, comentarios y evidencias.",
            "Para revisar avisos: entrar a Alertas o Notificaciones y abrir el comunicado correspondiente.",
            "Para usar el asistente: entrar a Asistente, crear o abrir una conversacion y escribir la consulta relacionada con Remansos del Norte o CommuSafe.",
            "Las conversaciones del asistente quedan guardadas por usuario y pueden retomarse desde el historial del asistente.",
            "Si no aparece una conversacion, reporte o respuesta, se recomienda actualizar la pantalla, revisar la conexion y volver a iniciar sesion si es necesario.",
        ],
    },
    {
        "titulo": "Preguntas frecuentes registradas",
        "items": [
            "Como reporto un incidente: usa Incidentes > Nuevo, completa categoria, descripcion, ubicacion y evidencia opcional.",
            "Como hago seguimiento a un caso: abre el incidente y revisa el estado, historial y comentarios.",
            "Donde veo los avisos: entra a Alertas o Notificaciones.",
            "Como contacto a administracion: usa los canales registrados del conjunto o solicita apoyo desde administracion; el asistente no inventa telefonos si no estan registrados.",
            "Que hago si hay ruido excesivo: registra un incidente de Convivencia con hora, lugar, descripcion y evidencia si es posible.",
            "Que hago si una mascota causa molestias: registra la situacion con respeto, frecuencia, ubicacion y evidencia si aplica.",
            "Como reporto un dano en zona comun: crea un incidente de Infraestructura con ubicacion exacta y foto si esta disponible.",
            "Como registro un visitante: informa a porteria o usa el canal habilitado por el conjunto; incluye nombre, destino, placa y horario estimado si aplica.",
            "Que hago si olvide mi contrasena: solicita apoyo a administracion para restablecer el acceso segun el procedimiento vigente.",
            "Que hago si el asistente no tiene respuesta: valida con administracion porque puede tratarse de informacion no registrada en CommuSafe.",
        ],
    },
]


ASSISTANT_RESPONSE_RULES = [
    "Responder en espanol con tono amable, claro, respetuoso y profesional.",
    "Usar frases naturales como 'segun la informacion registrada en CommuSafe', 'de acuerdo con la informacion disponible en el sistema' o 'puedes realizar este proceso desde el modulo correspondiente'.",
    "No usar expresiones que desacrediten la base de conocimiento interna.",
    "No inventar valores, sanciones, nombres, telefonos, horarios especiales, reservas ni decisiones administrativas que no esten registradas.",
    "Si falta informacion exacta, decirlo de forma natural y recomendar validar con administracion.",
    "Evitar respuestas largas por defecto; si el usuario pide detalle, responder paso a paso.",
    "Orientar al usuario hacia el modulo correcto de CommuSafe cuando la consulta sea operativa.",
]


def render_knowledge_base():
    """Convierte la base de conocimiento estructurada en texto para el prompt."""

    bloques = []
    for seccion in KNOWLEDGE_BASE_SECTIONS:
        items = "\n".join(f"- {item}" for item in seccion["items"])
        bloques.append(f"## {seccion['titulo']}\n{items}")

    reglas = "\n".join(f"- {rule}" for rule in ASSISTANT_RESPONSE_RULES)
    bloques.append(f"## Reglas de respuesta del asistente\n{reglas}")
    return "\n\n".join(bloques)
