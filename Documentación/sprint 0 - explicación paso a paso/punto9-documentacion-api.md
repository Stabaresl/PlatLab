# Sprint 0 — Punto 9: Documentación de API (drf-spectacular)

## ¿Qué es esto?

Es la herramienta que genera **automáticamente** la documentación de todos los endpoints de la API, a partir del código real del backend, sin que nadie tenga que escribirla ni mantenerla a mano.

## ¿Por qué es importante?

El equipo de frontend (y cualquier integrador externo) necesita saber exactamente qué endpoints existen, qué datos esperan recibir y qué devuelven, sin tener que leer el código del backend ni preguntarle constantemente al equipo backend. Una documentación escrita a mano se desactualiza rápido — alguien cambia un endpoint y se olvida de actualizar el documento. `drf-spectacular` resuelve esto generando la documentación directamente desde el código: si el código cambia, la documentación se actualiza sola.

Esto también habilita una interfaz interactiva (Swagger) donde cualquiera puede probar los endpoints directamente desde el navegador, sin necesitar herramientas adicionales como Postman.

## ¿Qué se hizo exactamente?

### 1. Se instaló y registró `djangorestframework` y `drf-spectacular`
Son las dos librerías necesarias: la primera (`Django REST Framework`) es la base sobre la que se construirán todos los endpoints de la API en los próximos sprints; la segunda genera la documentación a partir de ella.

### 2. Se configuró la paginación estándar
Se definió que todos los listados grandes de la API (catálogo de laboratorios, auditoría, etc.) usan paginación por cursor, tal como se definió en el documento de API — evita traer miles de registros de una sola vez, lo cual sería lento e ineficiente.

### 3. Se expusieron dos rutas públicas
- **`/api/v1/schema/`**: el archivo técnico (formato OpenAPI/YAML) que describe todos los endpoints — lo consumen herramientas automáticas, no personas.
- **`/api/v1/docs/`**: la interfaz visual (Swagger) donde cualquier persona del equipo puede ver y probar los endpoints desde el navegador.

Por ahora ambas rutas están vacías de contenido real (no hay endpoints todavía, esos se construyen a partir del Sprint 1) — pero la infraestructura para documentarlos automáticamente ya queda lista y funcionando.

## ¿Qué NO incluye este punto?

- Ningún endpoint real de negocio (login, catálogo, etc.) — la documentación se irá llenando sola a medida que se construyan en los próximos sprints.

## En una frase

Se dejó lista la herramienta que va a generar y mantener automáticamente la documentación de toda la API, disponible en una página web navegable, sin que nadie tenga que escribirla a mano.
