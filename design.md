# Design — PlatLAB

Sistema de diseño fijo de la app. Toda pantalla nueva o rediseñada lo lee antes
de escribir código. Se amplía este archivo; no se reinventa por página.

## Género
Atmosférico: herramienta técnica de uso nocturno. Lienzo oscuro, consola como
protagonista, color solo para estado y acción.

## Familias de estructura
- **Marketing** (bienvenida, sobre PlatLAB): héroe con un objeto 3D focal (three.js) + secciones de texto.
- **App** (dashboards, salas, admin): banco de trabajo. Encabezado funcional pequeño, contenido en paneles, sin héroes.
- **Laboratorio**: estudio dividido. Guía (visión general → tareas numeradas → resultado esperado) a la izquierda, consola fija a la derecha; en móvil, apilado.
- **Tablas** (usuarios, tableros): índice tabular denso, una fila por entidad, acciones al final de la fila.

## Tema (tokens existentes en `frontend/src/index.css`)
- Lienzo `--canvas` · superficies `--surface`, `--surface-raised`, `--surface-hover`, `--surface-sunken`
- Bordes `--border-hairline`, `--border-default`, `--border-strong`
- Texto `--text-heading`, `--text-base`, `--text-muted`, `--text-dim`
- Señales con significado fijo: `--signal-amber` acción principal y "en curso" · `--signal-cyan` información y foco · `--signal-green` completado · `--signal-red` error o peligro. No se usan como decoración.
- Tonos derivados con `color-mix(in srgb, var(--signal-x) N%, transparent)`, nunca hex/rgba nuevos sueltos.

## Tipografía
- Display: Orbitron 700/900, mayúsculas, solo títulos cortos. Recta (nunca itálica).
- Texto: Fira Sans 400/500/600.
- Mono: JetBrains Mono 400/500/700 para consola, códigos, datos y etiquetas.

## Espaciado y forma
Escala de Tailwind (4 pt). Esquinas cortadas `chamfer` / `chamfer-sm` (marca de la casa); `--radius: 3px` para lo demás.

## Movimiento
- `--ease-tactical`, duraciones `--dur-fast` (180 ms) / `--dur-med` (320 ms).
- Solo `transform` y `opacity`. Entrada por fundido corto; nada de rebotes.
- `prefers-reduced-motion`: escenas 3D quietas (un cuadro), transiciones a fundido ≤150 ms.

## Microinteracciones
- Éxito silencioso (el estado cambia en su sitio), sin toasts de celebración salvo logros.
- Copiar comando: el botón cambia a "Copiado" 1,5 s.
- `:focus-visible` visible e inmediato en todo lo interactivo.

## Reglas compartidas
- Sin cromo dibujado de ventana (puntos rojo/ámbar/verde, barras de navegador falsas). La consola muestra datos reales de la sesión (usuario@host, IP, estado), no decoración.
- Sin cifras inventadas: los números salen de la API o no se muestran.
- Funciona a 320 / 375 / 414 / 768 px sin scroll horizontal.
- Escenas three.js: carga diferida, `aria-hidden`, la misma información disponible en texto o tabla.
