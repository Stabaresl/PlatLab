# Correcciones Hechas — PlatLAB

> Documento resumen de todas las correcciones aplicadas a la documentación del equipo de desarrollo, para que cualquier miembro del equipo entienda QUÉ cambió y POR QUÉ.

---

## Resumen

Se auditaron los **10 archivos** de la carpeta `documentación_equipo de desarrollo/` contra la base canónica del proyecto (`casos-de-uso.md` e `historias-de-usuario.md` en la raíz). Se corrigieron inconsistencias, contradicciones y omisiones. Al final, **todos los archivos quedaron renombrados con el sufijo `-actualizado`** para identificar las versiones corregidas.

---

## Archivos Creados / Renombrados

| Archivo Original | Archivo Final | Cambios |
|---|---|---|
| `casos-de-uso.md` | `casos-de-uso-actualizado.md` | 7 correcciones |
| `historias-usuario-completas-correccion.md` | `historias-de-usuario-actualizado.md` | 7 correcciones |
| `api.md` | `api-actualizado.md` | 5 correcciones |
| `seguridad.md` | `seguridad-actualizado.md` | 1 corrección |
| `base-de-datos.md` | `base-de-datos-actualizado.md` | 1 corrección |
| `dominio.md` | `dominio-actualizado.md` | 1 corrección |
| `glosario.md` | `glosario-actualizado.md` | 1 corrección |
| `backend.md` | `backend-actualizado.md` | 1 corrección |
| `estructura-carpetas.md` | `estructura-carpetas-actualizado.md` | 1 corrección |
| (SVG intacto) | (sin cambios) | Sin cambios |

---

## Correcciones por Archivo

### `casos-de-uso-actualizado.md`

| # | Qué cambió | Por qué |
|---|---|---|
| 1 | **UC-01**: se agregó `HV-05` a las HU relacionadas | Faltaba la historia de usuario "Recuperación de contraseña", que sí existe en el canónico |
| 2 | **UC-02**: se aclaró que las secciones son **secuenciales obligatorias** (no se puede saltar a una sección sin haber completado la anterior) | El canónico ya había tomado esta decisión de negocio; el documento del equipo estaba desactualizado |
| 3 | **UC-02, excepción E1**: se agregó referencia a `RNF-01.9` con valores exactos (30 intentos/min por usuario, 10/min por flag, HTTP 429) | El canónico definió un rate limit específico para flags que no estaba cuantificado en el documento del equipo |
| 4 | **UC-03, flujo A1**: se especificó que el examen es de **opción múltiple**, entre **1 y 15 preguntas**, con **calificación automática** | El canónico definió el formato del examen; el equipo lo tenía genérico ("preguntas/criterios") |
| 5 | **UC-04, paso 4**: se detalló que el examen opcional es de opción múltiple, 1-15 preguntas, con opciones y respuesta correcta | Coherencia con UC-03 |
| 6 | **UC-06**: se reestructuró COMPLETAMENTE (ver detalle abajo) | Era la contradicción más grave |
| 7 | **UC-10**: se agregó `HA-06` a las HU relacionadas | Faltaba la historia "Crear laboratorio predeterminado" |

#### Detalle de la corrección de UC-06 (la más importante)

**Antes (versión del equipo):**
- Título: "Invitación y asignación de laboratorio **con vencimiento**"
- Flujo principal: el instructor **debía** definir una fecha de vencimiento (obligatorio)
- HU relacionadas: solo `HI-07, HI-09`
- Sin opción de modificar el vencimiento después

**Ahora (versión corregida):**
- Título: "Invitación y asignación de laboratorio"
- Flujo principal: **asignación sin vencimiento** (acceso permanente)
- Flujo alternativo A1: asignación **con vencimiento** (opcional, el instructor elige)
- Flujo alternativo A3: **modificar vencimiento después de asignado** (agregar, quitar o modificar)
- HU relacionadas: `HI-07, HI-09, HE-13`

**Motivo:** El canónico define que el vencimiento es **opcional**, no obligatorio. El equipo había invertido la regla de negocio.

---

### `historias-de-usuario-actualizado.md`

| # | Qué cambió | Por qué |
|---|---|---|
| 1 | **HV-05**: token de recuperación cambió de **1 hora** a **15 minutos** | El canónico (UC-01) define 15 min por seguridad. 1 hora es una ventana de ataque 4x mayor |
| 2 | **HE-03**: se eliminó el riesgo "pendiente de negocio" y se confirmó que las secciones son **secuenciales obligatorias** | La decisión ya fue tomada en UC-02 |
| 3 | **HI-07**: se cambió de "asignar **con** límite de tiempo" a "**con o sin** límite de tiempo". Se agregó que el instructor puede **agregar, modificar o quitar** el vencimiento después de asignado | Coherencia con UC-06 y RF-24 |
| 4 | **HI-08**: se especificó que el examen es de **opción múltiple, 1-15 preguntas**, con opciones y respuesta correcta, calificación automática | El canónico definió el formato; el equipo lo tenía genérico |
| 5 | **RF-24**: se agregó "(opcional)" y la capacidad de modificar el vencimiento después de asignado | Coherencia con UC-06 e HI-07 |
| 6 | **Se agregó RNF-01.9**: rate limiting específico para flags (30/min usuario, 10/min flag, HTTP 429) | El canónico lo definió; al equipo le faltaba |
| 7 | **Resumen**: RNF count pasó de **25 a 26** | Por la adición de RNF-01.9 |
| 8 | **Emojis de secciones de rol**: se agregaron 👤 🎓 👨‍🏫 🔧 a los headers de rol | Se perdieron en la copia. El canónico los tiene, contenido idéntico, solo formato visual |

---

### `api-actualizado.md`

| # | Qué cambió | Por qué |
|---|---|---|
| 1 | **Rate limiting de flags** (§12): cambió de "20 intentos/min por usuario+sección" a **"30 intentos/min por usuario, 10 intentos/min por flag (RNF-01.9)"** | Coherencia con RNF-01.9 del canónico |
| 2 | **`/auth/logout-all/`**: se eliminó la referencia a `HE-14` | HE-14 **no existe** en ninguna de las 33 HU. Se reemplazó por una descripción textual |
| 3 | **`/auth/refresh/`**: se eliminó referencia a `RF-07` | RF-07 es "Dashboard del estudiante", no tiene relación con JWT |
| 4 | **`/auth/password-reset/`**: se corrigió referencia de `RF-04` a `RF-03` | RF-04 es "Roles y permisos", RF-03 es "Recuperación de contraseña" |
| 5 | **Endpoint de modificar vencimiento**: se agregó `PATCH /assignments/invitations/{id}/expiration/` | UC-06 A3 define este flujo; no existía en la API |
| 6 | **Código HTTP para sección bloqueada**: se cambió de **403** a **422 `BUSINESS_RULE_VIOLATION`** | La secuencialidad es una regla de negocio, no un permiso. El propio documento usa 422 para casos similares |
| 7 | **Health endpoint**: se corrigió referencia de `RF-28` a `RF-29` | RF-28 es "Dashboard de métricas de negocio" (usuarios, labs activos). Un health check no expone métricas de negocio — RF-29 "Dashboard de rendimiento" (tiempos de respuesta, uptime) es más afín. Coherencia con trazabilidad HA-04→RF-29 del canónico |

---

### `seguridad-actualizado.md`

| # | Qué cambió | Por qué |
|---|---|---|
| 1 | **Rate limiting de flags** (§5): cambió de "20 intentos/min por usuario+sección" a **"30 intentos/min por usuario, 10 intentos/min por flag (RNF-01.9)"** | Coherencia con RNF-01.9 y api.md |

---

### `base-de-datos-actualizado.md`

| # | Qué cambió | Por qué |
|---|---|---|
| 1 | **`laboratories_pregunta.tipo`**: se eliminó `abierta` del enum, quedó solo `opcion_multiple` | El canónico solo define exámenes de opción múltiple por ahora. Si se necesita pregunta abierta a futuro, se agrega |

---

### `dominio-actualizado.md` y `glosario-actualizado.md`

| # | Qué cambió | Por qué |
|---|---|---|
| 1 | Se actualizaron todas las referencias de `historias-usuario-completas.md` a `historias-de-usuario.md` | El archivo fue renombrado en la base canónica |

---

### `backend-actualizado.md` y `estructura-carpetas-actualizado.md`

| # | Qué cambió | Por qué |
|---|---|---|
| 1 | **Se agregó `ModificarVencimientoUseCase`** a la tabla de Assignments | El endpoint `PATCH .../expiration/` existe en la API, pero no había un caso de uso correspondiente |
| 2 | **Se agregó `modificar_vencimiento.py`** a la estructura de carpetas de Assignments | Coherencia con el caso de uso agregado en backend.md |

---

## Resumen Final

| Tipo de Corrección | Cantidad |
|---|---|
| Contradicciones de regla de negocio corregidas (CRITICAL) | 3 |
| Información desactualizada actualizada (WARNING) | 12 |
| Referencias rotas o incorrectas corregidas | 6 |
| Omisiones de contenido agregadas | 6 |
| Formato visual restaurado | 1 |
| Coherencia entre archivos restaurada | √ |

**Todos los archivos en `documentación_equipo de desarrollo/` están ahora sincronizados con la base canónica del proyecto.**
