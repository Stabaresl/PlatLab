# Base de Datos — PlatLAB (PostgreSQL)

> Modelo ER derivado directamente del Dominio v2 y los módulos de Arquitectura. Un módulo = un esquema/prefijo de tablas, respetando el aislamiento ya definido (ningún módulo referencia con FK directa las tablas internas de otro; las referencias cruzadas son por `id` suelto, validado en Application).

---

## 1. Tablas por módulo

### Módulo: Users

**users_user**
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| email | varchar(255) | UNIQUE, NOT NULL |
| username | varchar(50) | UNIQUE, NULL (permite invitar por username, HI-09) |
| nombre_completo | varchar(200) | NOT NULL (requerido para filtros de HI-04) |
| password_hash | varchar(255) | NULL (nulo si el usuario solo usa OAuth) |
| rol | enum(estudiante, instructor, administrador) | NOT NULL, default `estudiante` |
| is_active | boolean | NOT NULL, default true |
| date_joined | timestamp | NOT NULL |
| last_login | timestamp | NULL |

**users_proveedorautenticacion**
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users_user, NOT NULL |
| proveedor | enum(email, google, github) | NOT NULL |
| proveedor_uid | varchar(255) | NOT NULL |
| created_at | timestamp | NOT NULL |

- **Restricción única compuesta:** `(user_id, proveedor)` — un usuario no puede vincular el mismo proveedor dos veces.
- **Restricción única:** `(proveedor, proveedor_uid)` — un mismo UID de Google/GitHub no puede vincularse a dos cuentas distintas.

---

### Módulo: Laboratories

**laboratories_laboratorio**
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| nombre | varchar(200) | NOT NULL |
| descripcion | text | NOT NULL |
| nivel_dificultad | enum(basico, intermedio, avanzado) | NOT NULL |
| estado | enum(borrador, publicado) | NOT NULL, default `borrador` |
| tipo | enum(predeterminado, personalizado) | NOT NULL |
| origen_id | UUID | FK → laboratories_laboratorio (self), NULL |
| instructor_id | UUID | NULL (id suelto a users_user; NULL si es predeterminado) |
| created_at / updated_at | timestamp | NOT NULL |

- **Constraint CHECK:** `tipo = 'predeterminado' → instructor_id IS NULL` (un predeterminado no tiene dueño instructor).
- **Constraint CHECK:** `origen_id` solo permitido si `tipo = 'personalizado'`.
- **Regla adicional (no expresable como CHECK simple, requiere subconsulta):** `origen_id` debe apuntar a un laboratorio con `tipo = 'predeterminado'`. Se valida en `DuplicadorDeLaboratorio` (capa Domain/Application), no en PostgreSQL.

**laboratories_tema** (catálogo de temas, evita grupos repetitivos)
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| nombre | varchar(100) | UNIQUE |

**laboratories_laboratorio_tema** (N:M)
| laboratorio_id | tema_id |
|---|---|
| FK → laboratorio | FK → tema |
PK compuesta `(laboratorio_id, tema_id)`.

**laboratories_seccion**
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| laboratorio_id | UUID | FK → laboratorio, NOT NULL |
| titulo | varchar(200) | NOT NULL |
| contenido_teorico | text | NOT NULL |
| orden | integer | NOT NULL |
| tiene_practica | boolean | NOT NULL, default false |

- **Restricción única:** `(laboratorio_id, orden)` — no dos secciones con el mismo orden en un mismo laboratorio.

**laboratories_flag** (relación 1:1 con sección práctica)
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| seccion_id | UUID | FK → seccion, UNIQUE, NOT NULL |
| flag_hash | varchar(255) | NOT NULL (bcrypt/argon2 del valor real) |
| pista_texto | text | NULL |
| paso_a_paso_texto | text | NULL |

**laboratories_examen**
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| laboratorio_id | UUID | FK → laboratorio, UNIQUE (1:1) |

**laboratories_pregunta**
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| examen_id | UUID | FK → examen, NOT NULL |
| enunciado | text | NOT NULL |
| tipo | enum(opcion_multiple) | NOT NULL |
| opciones | jsonb | NULL (solo si `opcion_multiple`) |
| respuesta_hash | varchar(255) | NOT NULL |

---

### Módulo: Assignments

**assignments_asignacion**
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| estudiante_id | UUID | NOT NULL (id suelto a users_user) |
| laboratorio_id | UUID | NOT NULL (id suelto a laboratories_laboratorio) |
| instructor_id | UUID | NULL (quien invita) |
| estado | enum(pendiente, aceptada, rechazada, activa, vencida) | NOT NULL, default `pendiente` |
| fecha_invitacion | timestamp | NOT NULL |
| fecha_vencimiento | timestamp (UTC) | NULL |
| fecha_respuesta | timestamp | NULL |

- **Restricción única:** `(estudiante_id, laboratorio_id)` con estado activo — evita asignaciones duplicadas (regla de UC-06, E2).
- **Constraint CHECK:** `fecha_vencimiento IS NULL OR fecha_vencimiento > fecha_invitacion`.
- **Índice:** `(estado, fecha_vencimiento)` — usado por `GestorDeVencimientos` para el job periódico (UC-07).

---

### Módulo: Progress

**progress_progreso**
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| asignacion_id | UUID | UNIQUE, NOT NULL (id suelto a assignments_asignacion, 1:1) |
| fecha_inicio | timestamp | NOT NULL |
| ultima_actividad | timestamp | NOT NULL |

**progress_progresoseccion**
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| progreso_id | UUID | FK → progreso, NOT NULL |
| seccion_id | UUID | NOT NULL (id suelto a laboratories_seccion) |
| estado | enum(bloqueada, en_progreso, completada) | NOT NULL, default `bloqueada` |
| fecha_completado | timestamp | NULL |

- **Restricción única:** `(progreso_id, seccion_id)`.
- **Índice:** `(progreso_id, estado)` — usado para calcular si un examen puede habilitarse (todas `completada`).

**progress_intentoflag**
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| progreso_id | UUID | FK → progreso, NOT NULL |
| seccion_id | UUID | NOT NULL |
| resultado | boolean | NOT NULL |
| timestamp | timestamp | NOT NULL |

- **Índice compuesto:** `(progreso_id, seccion_id, timestamp)` — soporta el cálculo de `ContadorFallos` (HE-06) sin escanear toda la tabla.

**progress_resultadoexamen**
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| progreso_id | UUID | FK → progreso, NOT NULL |
| examen_id | UUID | NOT NULL |
| respuestas | jsonb | NOT NULL |
| puntaje | numeric(5,2) | NOT NULL |
| fecha | timestamp | NOT NULL |

**progress_historialcompletitud**
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| progreso_id | UUID | FK → progreso, NOT NULL |
| numero_intento | integer | NOT NULL |
| puntaje | numeric(5,2) | NULL |
| fecha_completado | timestamp | NOT NULL |

- **Restricción única:** `(progreso_id, numero_intento)`.

---

### Módulo: Reports

**reports_reporte**
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| estudiante_id | UUID | NOT NULL |
| laboratorio_id | UUID | NOT NULL |
| seccion_id | UUID | NULL |
| descripcion | text | NOT NULL, CHECK `length(descripcion) >= 10` |
| estado | enum(abierto, en_revision, resuelto, no_reproducible) | NOT NULL, default `abierto` |
| fecha_creacion | timestamp | NOT NULL |
| fecha_resolucion | timestamp | NULL |

**reports_adjunto**
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| reporte_id | UUID | FK → reporte, NOT NULL |
| archivo_url | varchar(500) | NOT NULL |
| nombre_archivo | varchar(255) | NOT NULL |
| tamano_kb | integer | NOT NULL |

---

### Módulo: Notifications

**notifications_notificacion**
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | NOT NULL |
| tipo | enum(invitacion, vencimiento_proximo, reporte_resuelto, laboratorio_publicado) | NOT NULL |
| mensaje | text | NOT NULL |
| leida | boolean | NOT NULL, default false |
| canal | enum(in_app, email) | NOT NULL |
| entidad_tipo | varchar(100) | NULL (ej. `asignacion`, `reporte` — permite deep-link desde el frontend) |
| entidad_id | UUID | NULL |
| fecha_creacion | timestamp | NOT NULL |

- **Índice:** `(user_id, leida)` — para el listado de notificaciones pendientes por usuario.

---

### Módulo: Audit

**audit_registroauditoria**
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID | PK |
| actor_id | UUID | NULL (nulo si es acción del sistema, ej. `GestorDeVencimientos`) |
| accion | varchar(100) | NOT NULL (ej. `login`, `user.role_changed`, `laboratory.published`) |
| entidad_tipo | varchar(100) | NOT NULL |
| entidad_id | UUID | NOT NULL |
| timestamp | timestamp | NOT NULL |
| ip | inet | NULL |
| metadata | jsonb | NULL |

- **Tabla append-only:** sin UPDATE ni DELETE permitidos a nivel de aplicación (permiso revocado también a nivel de rol de base de datos).
- **Índices:** `(entidad_tipo, entidad_id)`, `(actor_id)`, `(timestamp)` — para las tres formas de consulta que exige HA/UC-12.

---

## 2. Cardinalidades (resumen)

| Relación | Cardinalidad |
|---|---|
| User — ProveedorAutenticacion | 1 : N |
| Laboratorio — Sección | 1 : N |
| Sección — Flag | 1 : 0..1 |
| Laboratorio — Examen | 1 : 0..1 |
| Examen — Pregunta | 1 : N |
| Laboratorio — Laboratorio (origen) | 1 : N (auto-referencia) |
| Laboratorio — Tema | N : M |
| Asignación — Progreso | 1 : 1 |
| Progreso — ProgresoSeccion | 1 : N |
| Progreso — IntentoFlag | 1 : N |
| Progreso — ResultadoExamen | 1 : N |
| Progreso — HistorialCompletitud | 1 : N |
| Reporte — Adjunto | 1 : 0..1 |
| User — Notificación | 1 : N |

---

## 3. Normalización

- El modelo cumple **3FN**: no hay dependencias transitivas (ej. `nivel_dificultad` no repite atributos de `laboratorio`), y los grupos repetitivos se resolvieron con tablas propias (`tema`, `laboratorio_tema` en vez de una columna `temas` separada por comas).
- **Denormalización deliberada:** `progress_resultadoexamen.respuestas` y `progress_historialcompletitud` usan `jsonb` para las respuestas del examen — es un snapshot histórico que no debe normalizarse en más tablas porque su estructura depende del examen vigente al momento del intento, no debe cambiar retroactivamente si el instructor edita el examen después.
- Las referencias cruzadas entre módulos (`estudiante_id`, `laboratorio_id`, etc.) son **IDs sueltos, sin FK de base de datos entre esquemas de módulos distintos** — es la traducción a nivel de BD de la regla de aislamiento entre módulos ya fijada en Arquitectura §8. La integridad referencial cruzada se garantiza en la capa Application, no en PostgreSQL.

---

## 4. Índices adicionales de rendimiento (RNF-02)

| Tabla | Índice | Motivo |
|---|---|---|
| laboratories_laboratorio | `(estado, nivel_dificultad)` | Filtro de catálogo (HV-02/HE-02) |
| laboratories_laboratorio | `(tipo, instructor_id)` | Panel del instructor (HI-06) |
| assignments_asignacion | `(estudiante_id, estado)` | Dashboard del estudiante (HE-01) |
| progress_progreso | `(asignacion_id)` | Ya cubierto por UNIQUE, reutilizado por el dashboard |
| audit_registroauditoria | `(timestamp DESC)` | Consulta reciente por defecto en el panel de auditoría |

## 5. Versionado de contenido (UC-04, A1)

No se crea una tabla `laboratories_version` dedicada (evita una tabla extra sin uso frecuente, YAGNI). En su lugar, cada edición de un laboratorio publicado dispara un evento auditado (`laboratory.content_edited`) que persiste en `audit_registroauditoria.metadata` un snapshot con el diff (secciones/flags modificadas, autor, timestamp). Es suficiente para trazabilidad (HI-02 nota de riesgo) sin duplicar el modelo de contenido.

## 6. Nota de implementación — UUID

Se usa UUID como PK en todas las tablas por consistencia entre módulos aislados (sin depender de IDs autoincrementales que colisionarían al extraer un módulo a microservicio). Recomendación práctica: usar **UUIDv7** (ordenable por tiempo) en vez de UUIDv4 puro, para mantener la localidad de los índices B-tree y evitar fragmentación — Django lo soporta vía librerías como `uuid7` o generando el valor en la capa Infrastructure antes del insert.

## Estado
✅ Modelo ER completo y revisado, alineado 1:1 con Dominio v2 y Arquitectura. 4 vacíos corregidos (nombre/username de usuario, deep-link de notificaciones, regla de origen validada en Application, versionado vía auditoría). Sin entidades para `LabEnvironments` (módulo reservado, sin tablas aún).
