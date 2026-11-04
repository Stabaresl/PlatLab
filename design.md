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
- `prefers-reduced-motion`: escenas 3D quietas (un cuadro), transiciones a fundido ≤150 ms. `MotionConfig reducedMotion="user"` en `main.tsx` lo aplica a framer-motion.
- Cada animación cuenta algo del dato; si no informa, no va. Piezas compartidas en `components/movimiento/`:
  - `Revelar`: entrada al hacer scroll (una vez), para secciones y tarjetas.
  - `BarraLlenado`: barra que se llena al verse; con `segmentos`, un tramo por elemento real ("3 de 5").
  - `NumeroAnimado`: cifra que cuenta hasta su valor (el valor real va en texto para lectores de pantalla).
- Patrones por pantalla:
  - Panel del estudiante: `NucleoProgreso` (three.js). Núcleo = estudiante, esfera en órbita = laboratorio, lunas = secciones. Al terminar un laboratorio la esfera viaja en espiral y se acopla; se anima solo la primera vez que se ve (localStorage).
  - Roadmap: conector verde entre terminados, señal que corre hacia el siguiente disponible (`.flujo-conector`), radar en el siguiente paso (`.radar-ping`), check que se dibuja en los completados.
  - Perfil: piezas equipadas flotando alrededor del avatar (`.flotar`), brillo único al aparecer un logro ganado, inventario con la colección completa (lo bloqueado dice qué logro lo da).
  - Urgencia: `.pulso-alerta` (opacidad) solo en vencimientos de ≤2 días.

## Fondo
- Dashboards, roadmap, perfil, catálogo, detalle de laboratorio y salas usan `FondoAscii` (`HeroBackground texture="ascii"`): lluvia de caracteres ámbar muy tenue, la misma de la tarjeta del encabezado, con un halo alrededor del puntero.
- Es un canvas fijo del tamaño de la ventana (portal a `<body>`, z-index 0): el contenido va en una capa `relative z-10`. El centro se atenúa con una máscara para no competir con los paneles.
- No va en la vista del laboratorio ni en el examen: ahí manda la concentración.

## Examen final
- Al empezar, el examen ocupa toda la pantalla (`ModoExamen`, portal con z-index 1100) y pide pantalla completa. Atrás muestra «No puedes salir del examen»; recargar o cerrar pide confirmación y entrega lo respondido (`fetch` con `keepalive`).
- Reglas del backend (`PoliticaDeIntentosExamen`): 3 intentos; tras 3 reprobados, 24 h de bloqueo con cuenta regresiva visible. Un intento abierto que no se entregó cuenta como 0. Se aprueba con 60 %, y solo aprobar cuenta como laboratorio terminado (dashboard, XP, salas).

## Avatar
- `AvatarPersonaje` (SVG): cada personaje predeterminado tiene rasgos propios (`lib/avatarRasgos.ts`) y cada tipo de cosmético se dibuja en su lugar del cuerpo. `vista="cabeza"` para la barra y el selector.
- El inventario tiene un probador: al señalar una pieza (aunque esté bloqueada) el avatar se la pone.

## Marca
- Isotipo `components/marca/IsoPlatlab.tsx`: marco de esquinas cortadas, núcleo ámbar y un satélite cian en órbita (el mismo lenguaje del núcleo de progreso). El satélite se mueve con JS; acelera al pasar el puntero.
- Logotipo `MarcaPlatlab`: isotipo + "PLAT::LAB" en JetBrains Mono con los "::" en ámbar; las letras se decodifican al cargar y al pasar el puntero.
- `public/favicon.svg` es la versión quieta del isotipo.

## Microinteracciones
- Éxito silencioso (el estado cambia en su sitio), sin toasts de celebración salvo logros.
- Copiar comando: el botón cambia a "Copiado" 1,5 s.
- `:focus-visible` visible e inmediato en todo lo interactivo.

## Reglas compartidas
- Sin cromo dibujado de ventana (puntos rojo/ámbar/verde, barras de navegador falsas). La consola muestra datos reales de la sesión (usuario@host, IP, estado), no decoración.
- Sin cifras inventadas: los números salen de la API o no se muestran.
- Funciona a 320 / 375 / 414 / 768 px sin scroll horizontal.
- Escenas three.js: carga diferida, `aria-hidden`, la misma información disponible en texto o tabla.
