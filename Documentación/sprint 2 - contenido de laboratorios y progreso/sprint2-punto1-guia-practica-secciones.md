# Sprint 2 — Punto 1: Guía práctica (consola simulada) en las Secciones

## ¿Qué es esto?

Hasta este punto una `Sección` de laboratorio con práctica (`tiene_practica=True`)
solo tenía una `Flag` que validar, pero ningún contenido que le explicara al
estudiante *qué hacer* antes de intentar esa flag. Este punto agrega
`EntornoPractica`: una guía paso a paso, con una **consola simulada**
opcional, que el instructor autoría junto con la sección.

## ¿Por qué es importante?

Sin esto, la experiencia de resolver una sección práctica era "acá tenés un
campo de texto, adiviná la flag" — no había guía, ni sensación de estar en
una terminal, ni forma de que el instructor enseñara el paso a paso del
ataque. `EntornoPractica` le da a cada sección la sensación de "tener una
VM" (estilo HackerRank/TryHackMe) sin necesitar todavía infraestructura real
de aislamiento — eso llega recién en el Sprint 3 con `lab_environments`.

## ¿Qué se hizo exactamente?

### 1. Nuevos Value Objects (Domain) — `value_objects.py`
- **`ComandoSimulado`**: un par `comando` / `salida` — cuando el estudiante
  tipea `comando` en la consola simulada del frontend, ve `salida`. No
  ejecuta nada real.
- **`EntornoPractica`**: agrupa un `prompt` (ej. `root@lab:~#`), un `banner`
  opcional y la lista completa de `ComandoSimulado` que arma el instructor.
  Cualquier comando no listado en el guion lo resuelve el frontend con un
  mensaje genérico de "comando no encontrado" — el instructor no necesita
  cubrir todos los casos posibles, solo el camino feliz del ataque que está
  enseñando.

### 2. Campo en la entidad `Seccion` (Domain) — `entities.py`
`Seccion` gana un campo `entorno_practica: EntornoPractica | None`, además de
`imagen_practica` (una captura/diagrama opcional que acompaña la guía).

### 3. Persistencia (Infrastructure) — `models.py`, `mappers.py`, migraciones
- Migración `0004_seccionmodel_entorno_practica_and_more`: agrega el campo
  JSON `entorno_practica` a `SeccionModel`.
- Migración `0005_seccionmodel_imagen_practica`: agrega `imagen_practica`
  (imagen subida, vía `storage_client` del kernel compartido).
- `mappers.py` traduce `EntornoPractica`/`ComandoSimulado` (dataclasses de
  dominio) ↔ el JSON guardado en la columna — sin esto el ORM no sabe cómo
  serializar objetos de dominio arbitrarios.

### 4. Casos de uso y API (Application/Presentation)
- `CrearSeccionUseCase` y `EditarSeccionUseCase` aceptan ahora
  `entorno_practica` en su DTO, así el instructor lo define al crear/editar
  la sección desde el editor de laboratorio.
- `serializers.py` expone `entorno_practica` (con sus `comandos` anidados) e
  `imagen_practica` tanto en la lectura del detalle de sección como en el
  contenido que consume el estudiante al resolver el laboratorio.

## ¿Qué NO incluye este punto?

- Ejecución real de comandos — eso es exclusivamente el módulo
  `lab_environments` (Sprint 3), que sí levanta un contenedor Docker real.
- Validación de la flag en sí — sigue siendo responsabilidad de
  `ValidarFlagUseCase` (módulo `progress`), sin cambios en este punto.
- UI de la terminal simulada en el frontend — ver Sprint 4
  (`SimulatedTerminal.tsx`).

## En una frase

Se le dio a cada sección práctica una guía paso a paso con consola simulada
autoría por el instructor, sentando el modelo de datos (`EntornoPractica` /
`ComandoSimulado`) que después el Sprint 3 complementa con una terminal real
y el Sprint 4 renderiza en el frontend.
