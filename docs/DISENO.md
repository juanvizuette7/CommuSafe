# Diseño Visual e Identidad de CommuSafe

## 1. Objetivo visual

La identidad visual de CommuSafe debe comunicar seguridad, control, confianza y respuesta rápida. El sistema no debe verse genérico ni académico en el mal sentido; debe proyectar una imagen profesional comparable a un producto real listo para adopción por una comunidad residencial.

## 2. Paleta de colores

### 2.1 Colores base

| Uso | Color | Hex |
| --- | --- | --- |
| Primario | Azul marino profundo | `#1A1A2E` |
| Secundario | Azul medio | `#16213E` |
| Acento | Azul eléctrico | `#0F3460` |
| Alerta / emergencia | Rojo vibrante | `#E94560` |
| Resuelto / éxito | Verde | `#10B981` |
| Fondo principal | Claro frío | `#F8FAFC` |

### 2.2 Colores de apoyo recomendados

| Uso | Hex |
| --- | --- |
| Texto principal oscuro | `#0F172A` |
| Texto secundario | `#475569` |
| Borde suave | `#CBD5E1` |
| Superficie blanca translúcida | `rgba(255, 255, 255, 0.72)` |
| Sombra azulada sutil | `rgba(15, 52, 96, 0.15)` |

## 3. Reglas de aplicación del color

- `#1A1A2E` será el color dominante en navegación, sidebar, encabezados principales y botones primarios.
- `#16213E` se usará como base para bloques secundarios, overlays y paneles oscuros.
- `#0F3460` servirá para resaltes, tabs activas, iconografía de acción y enlaces destacados.
- `#E94560` se reservará para incidentes críticos, alertas y acciones destructivas.
- `#10B981` se aplicará a estados resueltos, cierres exitosos y confirmaciones.
- `#F8FAFC` será el fondo principal de pantallas y contenedores amplios para mantener limpieza visual.

## 4. Tipografía

### 4.1 Web

- Fuente principal: `Inter`.
- Alternativa aprobada: `Poppins`.
- Uso recomendado:
  - títulos: peso 700;
  - subtítulos: peso 600;
  - texto normal: peso 400 o 500;
  - cifras de dashboard: peso 700 u 800.

### 4.2 Flutter

- Base tipográfica: Material Design.
- Se priorizará una jerarquía limpia con tamaños consistentes, buen espaciado y contraste alto.

## 5. Estilo general

La interfaz seguirá un lenguaje visual moderno y sobrio con los siguientes rasgos:

- Glassmorphism suave en tarjetas clave.
- Gradientes discretos en cabeceras y bloques de destaque.
- Bordes redondeados entre 12 px y 16 px.
- Sombras suaves y amplias, nunca agresivas.
- Espaciado generoso para evitar saturación.
- Microinteracciones visibles pero sobrias en botones, badges y tarjetas.

## 6. Superficies y contenedores

### 6.1 Tarjetas

- Fondo blanco translúcido o blanco sólido con ligera opacidad.
- Borde fino con tono gris azulado.
- Radio de borde de 14 px.
- Sombra suave con desplazamiento bajo.
- Espaciado interno cómodo para lectura rápida.

### 6.2 Cabeceras

- Gradiente sutil desde `#1A1A2E` hacia `#0F3460`.
- Título grande con texto claro.
- Subtexto en blanco con opacidad reducida.
- Elementos de acción alineados y bien separados.

### 6.3 Botones

- Primario:
  - fondo `#1A1A2E`;
  - texto blanco;
  - hover o pressed con transición hacia `#0F3460`.
- Secundario:
  - fondo translúcido;
  - borde visible;
  - texto oscuro.
- Peligro:
  - fondo `#E94560`;
  - texto blanco.

## 7. Componentes clave

### 7.1 Tarjeta de incidente

Debe ser uno de los componentes más cuidados del sistema.

Contenido mínimo:

- título del incidente;
- categoría;
- ubicación;
- fecha y hora;
- badge de prioridad;
- badge de estado;
- resumen breve;
- acceso al detalle.

Reglas visuales:

- El badge de prioridad cambia de color:
  - baja: azul suave;
  - media: ámbar o azul medio;
  - alta: naranja o rojo suave;
  - crítica: rojo `#E94560`.
- El estado debe verse claramente diferenciado del nivel de prioridad.
- La composición debe permitir escaneo rápido en desktop y móvil.

### 7.2 Timeline de historial de cambios

Debe comunicar trazabilidad y orden.

Reglas visuales:

- Línea vertical sutil.
- Nodos con color según tipo de evento.
- Tarjetas o bloques asociados a cada hito.
- Fecha, hora, actor y comentario claramente visibles.
- El evento más reciente debe destacar visualmente sin romper consistencia.

### 7.3 Interfaz de chat del asistente virtual

Reglas visuales:

- Burbujas modernas con radios altos.
- Mensajes del usuario alineados a la derecha con color de acento.
- Mensajes del asistente alineados a la izquierda sobre superficie clara.
- Campo de entrada limpio, ancho y cómodo.
- Indicadores de carga y envío sutiles.

### 7.4 Dashboard administrativo

Debe ser atractivo y útil, no solo funcional.

Elementos visuales esperados:

- tarjetas KPI con cifras grandes;
- gráfico o bloques de tendencia;
- distribución por estados y categorías;
- lista reciente de incidentes críticos;
- filtros visibles y elegantes.

## 8. Lineamientos de experiencia de usuario

- Toda la interfaz debe estar en español claro y consistente.
- Los estados vacíos deben orientar al usuario con tono profesional.
- Los formularios deben tener validación visible y mensajes concretos.
- La jerarquía visual debe permitir detectar incidentes críticos en pocos segundos.
- Debe existir consistencia visual entre panel web y app móvil, aunque cada plataforma use componentes nativos o propios.

## 9. Microinteracciones

- Transiciones de 150 ms a 220 ms en hover, focus y pressed.
- Elevación ligera al pasar sobre tarjetas clicables.
- Cambio de color suave en badges y botones.
- Skeleton loaders o indicadores de carga elegantes cuando corresponda.

## 10. Accesibilidad y legibilidad

- Contraste suficiente entre texto y fondo.
- Tamaños de fuente legibles en móvil.
- Zonas táctiles amplias para acciones críticas.
- Los colores no deben ser la única señal de estado; siempre deben acompañarse de texto o iconografía.

## 11. Aplicación visual por superficie

### 11.1 Panel web

- Sidebar oscura con fuerte presencia de marca.
- Área de contenido clara y aireada.
- Métricas con visual limpio y profesional.
- Tablas con estilo moderno, encabezados claros y filtros visibles.

### 11.2 App Flutter

- Pantallas con bloques limpios, tarjetas redondeadas y llamadas a la acción claras.
- Navegación inferior o híbrida según rol.
- Formularios con agrupación visual por secciones.
- Vista de detalle de incidente con jerarquía muy marcada entre resumen, evidencias e historial.

## 12. Resultado visual esperado

El producto debe transmitir:

- seguridad institucional;
- capacidad de respuesta;
- orden operativo;
- confianza para residentes;
- solidez suficiente para una sustentación académica de alto nivel.
