# Sprint 4 — Punto 2: Rollout del rediseño (landing, auth, catálogo, detalle, dashboards)

## ¿Qué es esto?

La aplicación del sistema de diseño "Tactical Ops Console" (tokens +
componentes compartidos del punto 1) a **todas** las páginas existentes del
frontend: `WelcomePage` (landing), `LoginPage`/`SignUpPage` (auth),
`CatalogPage`, `LabDetailPage`, y los tres dashboards
(`StudentDashboard`/`InstructorDashboard`/`AdminDashboard`), más `Navbar` y
`Footer` compartidos.

## ¿Por qué es importante?

Un sistema de diseño que solo existe en componentes sueltos sin aplicarse
no cambia nada de lo que ve el usuario. Este punto es lo que efectivamente
transforma la experiencia — y hacerlo de una sola vez sobre todas las
páginas evita el problema de tener "una página nueva bonita" conviviendo
con el resto del sitio en el estilo viejo, lo cual se ve peor que no haber
rediseñado nada.

## ¿Qué se hizo exactamente?

- **`Navbar` / `Footer`**: reconstruidos con el chrome tipo consola
  (`JetBrains Mono`, marca de texto "GA::IA" con acento ámbar en `::`,
  achaflanado en vez de bordes redondeados) — se comparten en todas las
  páginas, así que cualquier cambio acá se propaga a todo el sitio.
- **`WelcomePage`**: hero con `MouseGlow`/`HeroBackground`, secciones
  "cómo funciona"/"características"/"en números" (con `CountUpStat`) y CTA
  final.
- **`LoginPage` / `SignUpPage`**: layout de dos paneles — panel de marca a
  la izquierda (imagen de fondo con overlay + `MatrixRain`/`CyberGrid` +
  `MouseGlow` + copy corto tipo "briefing"), formulario a la derecha con
  `ReticleFrame` alrededor de la card y los inputs de shadcn/ui
  (`Input`/`Label`/`Button`). El registro muestra en vivo qué reglas de
  contraseña ya cumple el usuario mientras escribe.
- **`CatalogPage` / `LabDetailPage`**: reconstruidas sobre `TerminalHeader`
  (barra de título estilo terminal, con "chrome" de tres puntos de colores
  y un prompt simulado) y tarjetas con `ReticleFrame`.
- **`StudentDashboard` / `InstructorDashboard` / `AdminDashboard`**: mismo
  `TerminalHeader` + `SectionHeading` por bloque + `ProgressRing` animado
  para el progreso del estudiante — cada rol conserva su información
  específica, pero los tres comparten exactamente el mismo lenguaje visual.
- **`AboutPage`**: alineada al mismo sistema (headers, tipografía, paneles).

Todas estas páginas comparten los mismos primitivos de layout
(`TerminalHeader`, `ReticleFrame`, `SectionHeading`) en vez de reinventar su
propio header — es lo que garantiza consistencia real entre vistas que
tienen contenido completamente distinto.

## Decisiones revertidas dentro de este mismo sprint

Como parte de este trabajo se evaluó incorporar el logo ilustrado real de
la marca (un diseño detallado tipo cuervo/águila mecánica con el wordmark
"PLATLAB") en el `Navbar`/`Footer` y en paneles hero/dashboards. Se probó
tanto como SVG vectorizado (autotrace del PNG original, que perdía todo el
detalle interno al no ser un vector nativo) como PNG recortado a distintos
tamaños:

- Como ícono pequeño (navbar/footer) el nivel de detalle del arte original
  lo volvía ilegible — se verificó de forma empírica (no solo a ojo)
  reduciendo la imagen a 32px y reescalándola con interpolación "nearest"
  para simular fielmente cómo se vería realmente a ese tamaño: el
  resultado era una mancha de píxeles irreconocible.
- Como imagen grande en paneles hero/dashboards, el fondo fotográfico
  oscuro del logo entraba en mal contraste con los fondos ya existentes de
  la plataforma.

**Decisión final**: se descartó el logo ilustrado por completo (de todas
las páginas donde se había probado) y se volvió a la marca de texto
("GA::IA" en `JetBrains Mono` con acento ámbar) en `Navbar`/`Footer`, que sí
funciona a cualquier tamaño y no depende de ningún asset de imagen. El
archivo PNG optimizado quedó disponible en `frontend/src/assets/` sin
referenciarse desde ningún componente, por si se retoma más adelante con
otro tratamiento (por ejemplo, un ícono simplificado derivado del logo en
vez del arte completo).

## ¿Qué NO incluye este punto?

- La UI específica de resolución de laboratorios (secciones, terminales,
  examen) — punto 3 de este sprint, construida sobre esta misma base pero
  documentada aparte porque introduce piezas propias (terminal simulada y
  real).

## En una frase

Se aplicó el sistema "Tactical Ops Console" a la totalidad del frontend
existente de una sola vez —landing, autenticación, catálogo, detalle y los
tres dashboards— logrando consistencia visual real entre vistas, e
incluyendo la decisión (tomada y revertida dentro del mismo sprint, con
evidencia concreta) de no usar el logo ilustrado de marca por problemas de
legibilidad a tamaño chico y de contraste a tamaño grande.
