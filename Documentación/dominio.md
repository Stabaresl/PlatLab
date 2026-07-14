# Modelo de Dominio — PlatLAB

> Documento definitivo (v2). Entidades, relaciones, agregados, value objects y servicios de dominio. Sin implementación — insumo directo para la fase de Arquitectura.

---

## 1. Entidades

| Entidad | Descripción | Agregado |
|---|---|---|
| User | Usuario del sistema (Estudiante, Instructor, Administrador) | User |
| ProveedorAutenticacion | Método de acceso vinculado a un User (email, Google, GitHub) | User |
| Laboratorio | Contenedor de secciones; tipo predeterminado/personalizado | Laboratorio |
| Sección | Unidad de contenido teórico/práctico, con orden | Laboratorio |
| Examen | Conjunto de Preguntas asociado a un laboratorio | Laboratorio |
| Pregunta | Enunciado + opciones/respuesta esperada, parte de un Examen | Laboratorio |
| Asignación | Vínculo Estudiante↔Laboratorio (invitación→aceptación→vencimiento) | Asignación |
| Progreso | Estado de avance de un estudiante sobre un laboratorio | Progreso |
| ProgresoSeccion | Estado por sección (bloqueada/en_progreso/completada) para un Progreso | Progreso |
| IntentoFlag | Registro de intentos (correcto/fallido) sobre una flag específica | Progreso |
| ResultadoExamen | Respuestas + puntaje de un intento de examen | Progreso |
| HistorialCompletitud | Registro append-only de cada completitud del laboratorio (soporta repetición sin perder histórico) | Progreso |
| Reporte | Incidencia técnica reportada por un estudiante | Reporte |
| AdjuntoReporte | Archivo opcional asociado a un Reporte | Reporte |
| Notificación | Mensaje dirigido a un usuario por un evento del sistema | Notificación |
| RegistroAuditoria | Entrada inmutable de auditoría (append-only) | RegistroAuditoria |

---

## 2. Value Objects

| Value Object | Descripción |
|---|---|
| Rol | Enum: Estudiante, Instructor, Administrador |
| Email | Validado, único |
| Flag | Valor cifrado + hash de comparación; nunca expuesto en claro |
| AyudaProgresiva | Texto de pista y texto de paso a paso, asociados a la Flag |
| NivelDificultad | Enum: básico, intermedio, avanzado |
| Tema | Etiqueta(s) temática(s) del laboratorio, usada en filtros |
| EstadoLaboratorio | Enum: borrador, publicado |
| TipoLaboratorio | Enum: predeterminado, personalizado (+ `origen_id` opcional si es copia) |
| EstadoAsignacion | Enum: pendiente, aceptada, rechazada, activa, vencida |
| VentanaVencimiento | Fecha/hora límite (almacenada en UTC) |
| EstadoReporte | Enum: abierto, en_revisión, resuelto, no_reproducible |
| ContadorFallos | Valor incremental por flag; dispara pista (5 fallos) y paso a paso (15 fallos totales) |
| Puntaje | Valor numérico + escala máxima, usado en ResultadoExamen e HistorialCompletitud |

---

## 3. Relaciones

- **User** (Instructor) 1 → N **Laboratorio** (solo tipo `personalizado`).
- **User** 1 → N **ProveedorAutenticacion** (un usuario puede tener email + Google + GitHub vinculados).
- **Laboratorio** 1 → N **Sección** → 0..1 **Flag** (con `AyudaProgresiva` embebida; solo secciones prácticas tienen flag).
- **Laboratorio** 1 → 0..1 **Examen** → 1 → N **Pregunta**.
- **Laboratorio** (personalizado) → 0..1 referencia a **Laboratorio** (predeterminado) como `origen` (relación de copia, no de composición).
- **User** (Estudiante) 1 → N **Asignación** → 1 **Laboratorio**; **Asignación** → 1 **User** (Instructor, quien invita).
- **Asignación** 1 → 1 **Progreso** (se crea al aceptar la invitación).
- **Progreso** 1 → N **ProgresoSeccion** (una por cada Sección del laboratorio asignado).
- **Progreso** 1 → N **IntentoFlag**.
- **Progreso** 1 → 0..N **ResultadoExamen** (uno por intento de examen).
- **Progreso** 1 → N **HistorialCompletitud** (uno por cada vez que el estudiante completa el laboratorio).
- **User** (Estudiante) 1 → N **Reporte** → 1 **Laboratorio**, 0..1 **Sección**.
- **Reporte** 1 → 0..1 **AdjuntoReporte**.
- **User** 1 → N **Notificación**.
- **RegistroAuditoria** → referencia polimórfica a la entidad afectada (User, Laboratorio, Asignación, etc.) + **User** actor.

### Regla de secuencialidad (obligatoria)
Las secciones se completan en **orden estricto**. Máquina de estados de `ProgresoSeccion`:

```
bloqueada → en_progreso → completada
```

- Solo la primera sección de un Progreso nace en `en_progreso`; el resto nace en `bloqueada`.
- Al completar la sección `N` (última flag resuelta), se desbloquea automáticamente la sección `N+1`.
- El TOC (HE-08) permite navegar libremente hacia secciones `completada` o la `en_progreso` actual, pero **no** hacia secciones `bloqueada`.
- El examen final solo se habilita cuando todas las `ProgresoSeccion` del laboratorio están en `completada`.

---

## 4. Agregados

| Agregado raíz | Incluye | Justificación del límite de consistencia |
|---|---|---|
| **User** | ProveedorAutenticacion, Rol, Email | Identidad y autenticación son consistentes por sí solas |
| **Laboratorio** | Sección, Flag, Examen, Pregunta | Se edita/publica como unidad atómica; sus partes no existen sin él |
| **Asignación** | Estado, VentanaVencimiento | Ciclo de vida propio (invitación→vencimiento), independiente del contenido del laboratorio |
| **Progreso** | ProgresoSeccion, IntentoFlag, ResultadoExamen, HistorialCompletitud | Cambia con alta frecuencia (cada intento); separado de Asignación para evitar contención de escritura |
| **Reporte** | AdjuntoReporte | Ciclo de vida propio, actores distintos (Estudiante/Administrador) |
| **Notificación** | — | Efímera, sin reglas de negocio complejas; no debe acoplarse a otros agregados |
| **RegistroAuditoria** | — | Append-only; nunca se modifica ni se referencia como parte de otro agregado |

---

## 5. Servicios de Dominio

| Servicio | Responsabilidad | Por qué no vive en una entidad |
|---|---|---|
| **ValidadorDeFlag** | Compara flag ingresada vs. hash almacenado; incrementa `ContadorFallos`; determina si corresponde desbloquear pista o paso a paso | Cruza **Laboratorio** (Flag) y **Progreso** (ContadorFallos) — dos agregados distintos |
| **GestorDeSecuencia** | Desbloquea la siguiente `ProgresoSeccion` cuando la actual pasa a `completada` | Coordina dos instancias de `ProgresoSeccion` dentro del mismo agregado `Progreso` |
| **DuplicadorDeLaboratorio** | Crea una copia `personalizado` a partir de un `predeterminado`, preservando inmutabilidad del original | Crea un nuevo agregado **Laboratorio** a partir de otro; no es responsabilidad de la entidad origen |
| **CalificadorDeExamen** | Evalúa respuestas contra `Pregunta`, genera `ResultadoExamen` y actualiza `HistorialCompletitud` | Cruza **Laboratorio** (Preguntas) y **Progreso** (resultado del estudiante) |
| **GestorDeVencimientos** | Evalúa `Asignación`es activas contra su fecha límite y las transiciona a `vencida`, revocando acceso | Invocado por un proceso externo (scheduler), no por acción directa de un actor |
| **DespachadorDeNotificaciones** | Traduce eventos de dominio (invitación creada, vencimiento próximo, reporte resuelto) en `Notificación`es | Reacciona a eventos de múltiples agregados; no pertenece a ninguno en particular |
| **RegistradorDeAuditoria** | Crea entradas de `RegistroAuditoria` ante operaciones sensibles (login, cambio de rol, CRUD de laboratorio, etc.) | Transversal a todos los agregados; invocado desde múltiples casos de uso sin acoplarlos entre sí |
| **VinculadorDeCuenta** | Asocia un nuevo `ProveedorAutenticacion` a un `User` existente | Previene account takeover; requiere confirmación explícita del usuario, no vive en la entidad User |

---

## 6. Estado de cierre

Sin puntos abiertos. Secuencialidad de secciones confirmada como **obligatoria**.

**Trazabilidad:** cada entidad/servicio aquí definido responde directamente a una HU o Caso de Uso ya aprobados (ver `historias-usuario-completas.md` y `casos-de-uso.md`).
