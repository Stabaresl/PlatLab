# Sprint 4 — Punto 1: shadcn/ui + design tokens "Tactical Ops Console"

## ¿Qué es esto?

El punto de partida del rediseño visual completo del frontend: instalación
de shadcn/ui (componentes accesibles sobre Radix UI) + Tailwind CSS 4, y la
definición de un sistema de diseño propio — "Tactical Ops Console" — con
sus tokens (color, tipografía, espaciado, elevación, motion) y un puñado de
componentes compartidos que le dan personalidad a toda la plataforma.

## ¿Por qué es importante?

El frontend hasta este sprint funcionaba pero visualmente era genérico —
sin identidad propia. Para una plataforma de hacking ético/ciberseguridad,
la dirección elegida (consola de operaciones de un equipo de red-team:
negro OLED, un único acento ámbar de "sistema armado", cian de "dato/enlace",
esquinas achaflanadas en vez de bordes redondeados, marcos tipo retícula de
mira) refuerza el propósito del producto en vez de ser decoración genérica.
Se optó explícitamente por **no** usar animación ambiental constante en
todos lados — solo en puntos clave — para que no se sienta "de plantilla".

## ¿Qué se hizo exactamente?

### 1. Setup de shadcn/ui + Radix — `components.json`, `tsconfig`, `vite.config.ts`

Se inicializó shadcn/ui sobre el proyecto Vite + React 19 + Tailwind CSS 4
ya existente (config CSS-first, sin `tailwind.config.js`), con alias de
rutas (`@/...`) configurados en `tsconfig.app.json`/`tsconfig.json` y
`vite.config.ts`. Primitivas instaladas: `accordion`, `avatar`, `badge`,
`button`, `card`, `dialog`, `dropdown-menu`, `input`, `label`, `progress`,
`select`, `separator`, `skeleton`, `sonner` (toasts), `table`, `tabs`,
`textarea`, `tooltip` — quedan en `frontend/src/components/ui/`, editables
directamente (modelo de shadcn: el código se copia al proyecto, no es una
dependencia de node_modules cerrada).

### 2. Design tokens — `frontend/src/index.css`

Todo el sistema vive como variables CSS (`:root`), no como config de
Tailwind — coherente con Tailwind 4 CSS-first:

- **Color**: superficies OLED-first (`--canvas: #08090c`, capas de
  `--surface`/`--surface-raised`/`--surface-hover`), bordes en 3 niveles de
  intensidad, texto en 4 niveles de contraste, y la paleta de "señal": un
  único acento dominante ámbar (`--signal-amber: #ffb020`) + cian de
  dato/enlace + verde/rojo de estado (éxito/error) — deliberadamente
  **un solo acento dominante**, no una paleta arcoíris.
- **Tipografía**: tres familias con roles estrictos, no intercambiables —
  `Orbitron` **solo** para display (H1 de hero, números gigantes; usarlo en
  todos los H2/H3 fue probado y descartado por sentirse genérico),
  `JetBrains Mono` para todo el chrome de UI (nav, botones, badges, labels,
  encabezados de sección — es lo que le da la sensación de "consola"), y
  `Fira Sans` para cuerpo de texto largo, priorizando legibilidad real por
  sobre estética.
- **Elevación**: sombras de panel + dos "glows" de color (ámbar/cian) para
  estados destacados, sin depender de blur genérico.
- **Motion**: una curva de easing propia (`--ease-tactical`) y 4 duraciones
  con nombre (`instant`/`fast`/`med`/`slow`) en vez de valores mágicos
  repetidos en cada componente.

### 3. Componentes compartidos — `frontend/src/components/`

Piezas reutilizables que encarnan el sistema, usadas en todo el resto del
rediseño (puntos 2 y 3 de este sprint):

- **`MouseGlow`** (+ `trackGlow`/`untrackGlow`): un resplandor radial que
  sigue el cursor dentro de su contenedor — da sensación de "HUD reactivo"
  en paneles vivos (hero, panel de laboratorio activo) sin animar nada de
  forma constante. Respeta `prefers-reduced-motion` (no renderiza nada si
  el usuario lo pidió).
- **`ReticleFrame`**: marco de 4 esquinas tipo "retícula de mira" que
  decora paneles clave, puramente decorativo (`aria-hidden`), sin competir
  con el foco real del teclado.
- **`StatusDot`**: indicador de estado con variantes semánticas.
- **`CountUpStat`**: números que cuentan hacia arriba al entrar en
  viewport (estadísticas del landing).
- **`CyberGrid`**, **`MatrixRain`**, **`HeroBackground`**,
  **`ScanlineOverlay`**: fondos/efectos ambientales de baja opacidad,
  usados con moderación (no en todas las vistas a la vez).
- **`GlitchText`**: aberración cromática de texto al pasar el mouse, usada
  en títulos de headers de sección.
- **`ProgressRing`**, **`SectionHeading`**, **`TerminalHeader`**: piezas de
  layout reutilizadas por dashboards, catálogo y detalle de laboratorio.
- **`useReducedMotion`** (`hooks/`): hook compartido que todos los
  componentes con animación consultan antes de animar — accesibilidad
  tratada como requisito del sistema de diseño, no como parche por
  componente.

## ¿Qué NO incluye este punto?

- Aplicar el sistema a las páginas reales — eso es el punto 2 de este
  sprint. Este punto solo deja instalada la base y los componentes
  compartidos.
- La UI de resolución de laboratorios (terminales) — punto 3 de este
  sprint.

## En una frase

Se instaló shadcn/ui sobre Tailwind 4 y se definió, en variables CSS, un
sistema de diseño propio con identidad ("Tactical Ops Console") — color,
tipografía con roles estrictos, elevación y motion — junto con los
componentes compartidos que después reutiliza todo el resto del rediseño.
