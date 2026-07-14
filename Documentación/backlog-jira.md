# Backlog Jira — PlatLAB (Backend)

> Listo para importar/crear manualmente en Jira. Jerarquía: **Épica** (módulo) → **Historia** (HU o técnica) → **Tarea** (subtarea de implementación). Estimación en horas, asumiendo 1 desarrollador backend por tarea; ajustar según el tamaño real del equipo. Etiquetas sugeridas entre corchetes.

---

## Convenciones del tablero

| Campo | Valor |
|---|---|
| Tipo "Épica" | Un módulo de Arquitectura (`Authentication`, `Users`, `Laboratories`, etc.) |
| Tipo "Historia" | Una HU aprobada (`HV-04`, `HE-05`...) o una historia técnica sin HU de negocio (ej. setup de Docker) |
| Tipo "Tarea" | Subtarea técnica dentro de una Historia, alineada a una capa (Domain/Application/Infrastructure/Presentation/Tests) |
| Etiquetas | `[backend]` `[modulo:x]` `[sprint-N]` `[technical-debt]` si aplica |
| Estimación | Horas (columna "Est.") |

---

## Sprint 0 — Fundacional (previo al Sprint 1 del roadmap)

**Épica: Shared/Kernel**

| Historia | Tarea | Est. |
|---|---|---|
| Setup del proyecto | Inicializar proyecto Django con estructura modular (`modules/`, `config/`) | 4h |
| Setup del proyecto | Adaptar el `docker-compose.yml`/`Dockerfile` provisto por el servidor a los servicios necesarios (web, worker, beat, redis, postgres) | 4h |
| Setup del proyecto | Configurar variables de entorno (`.env.example`) y `settings/{base,dev,prod}.py` | 3h |
| Kernel de dominio | Implementar `BaseEntity`, `BaseValueObject`, `DomainEvent`, excepciones base | 4h |
| Kernel de aplicación | Implementar `BaseUseCase` (Template Method) | 3h |
| Kernel de infraestructura | Implementar `EventDispatcher` (registro y despacho de eventos) | 5h |
| Kernel de infraestructura | Implementar `BaseUnitOfWork` | 3h |
| Kernel de infraestructura | Configurar `RedisClient`, `EmailClient`, `StorageClient` | 5h |
| Documentación API | Configurar `drf-spectacular` (`/schema/`, `/docs/`) | 2h |
| Testing base | Configurar `pytest-django`, estructura de carpetas `tests/` por módulo | 3h |
| CI básico | Pipeline de lint + tests en cada push (GitHub Actions u otro definido en punto DevOps) | 4h |
| **Total Sprint 0** | | **40h** |

---

## Sprint 1 — Autenticación y estructura base

**Épica: Authentication**

| Historia | Tarea | Est. |
|---|---|---|
| HV-01 — Landing page | Endpoint/estructura base (si aplica desde backend: health-check público para que frontend valide disponibilidad) | 2h |
| HV-04 — Registro (email + OAuth) | Modelo `User` + `ProveedorAutenticacion` (módulo Users) | 3h |
| HV-04 | `RegistrarUsuarioUseCase` + validaciones (unicidad, password) | 4h |
| HV-04 | `OAuthLoginUseCase` + `GoogleOAuthAdapter` + `GitHubOAuthAdapter` | 6h |
| HV-04 | `VinculadorDeCuenta` (servicio de dominio, evita account takeover) | 3h |
| HV-04 | `RegisterView`, `OAuthCallbackView` + serializers | 4h |
| HV-04 | Tests unitarios (Use Cases) + integración (endpoints) | 5h |
| RF-02 — Login/JWT | `LoginUseCase` + `jwt_service.py` (wrapper SimpleJWT) | 4h |
| RF-02 | `RefreshTokenUseCase` + `refresh_token_store.py` (Redis, rotación + detección de reuso) | 6h |
| RF-02 | `LogoutUseCase` / `LogoutAllUseCase` (HE-14) | 3h |
| RF-02 | `JWTAuthenticationMiddleware` | 4h |
| RF-03 — Recuperación de contraseña | `SolicitarRecuperacionUseCase` + `ConfirmarRecuperacionUseCase` + templates de email | 5h |
| RF-02/03 | Tests unitarios + integración | 5h |
| **Total Sprint 1** | | **54h** |

---

## Sprint 2 — Catálogo de laboratorios

**Épica: Laboratories**

| Historia | Tarea | Est. |
|---|---|---|
| HV-02 — Catálogo público | Modelos `Laboratorio`, `Tema`, `Sección` (esqueleto, sin flags aún) | 5h |
| HV-02 | `ListarLaboratoriosQuery` + `Specification` de filtros (`PorDificultad`, `PorTema`) | 5h |
| HV-02 | `LaboratorioViewSet` (listado) + `LaboratorioListItemSerializer` | 3h |
| HV-03 — Detalle y TOC público | `ObtenerDetalleLaboratorioQuery`, `ObtenerTOCQuery` | 4h |
| HV-03 | Regla de bloqueo de contenido según asignación/rol (validada en Application, no solo en Presentation) | 4h |
| HE-02 — Buscar/filtrar (autenticado) | Extender query para incluir estado de inscripción del estudiante | 3h |
| HI-01 — Ver catálogo completo (instructor) | Ajustar permisos para incluir labs propios en `borrador` | 2h |
| Índices de rendimiento | Crear índices `(estado, nivel_dificultad)`, `(tipo, instructor_id)` (migración) | 2h |
| Cache de catálogo | `CachedLaboratorioRepository` (Decorator sobre Redis, RNF-02.1/02.2) | 5h |
| Tests | Unitarios + integración de catálogo/filtros/cache | 6h |
| **Total Sprint 2** | | **39h** |

---

## Sprint 3 — Contenido, flags, progreso y secuencialidad

**Épica: Laboratories + Progress**

| Historia | Tarea | Est. |
|---|---|---|
| HE-03/HE-04/HE-08 — Secciones, contenido, TOC | Modelo `Sección` completo (`orden`, `contenido_teorico`, `tiene_practica`) | 3h |
| HE-03/HE-04 | `ObtenerContenidoSeccionQuery` (valida `ProgresoSeccion ≠ bloqueada`) | 4h |
| — | Modelos `Progreso`, `ProgresoSeccion` (State: bloqueada/en_progreso/completada) | 5h |
| — | `GestorDeSecuencia` (servicio de dominio, desbloqueo automático) | 5h |
| HE-05 — Validación de flags | Modelo `Flag` (hash, cifrado) + `DefinirFlagUseCase` (autoría, aunque se usa desde Sprint 4 por instructor) | 4h |
| HE-05 | `ValidadorDeFlag` (servicio de dominio) + `ValidarFlagUseCase` | 6h |
| HE-05 | `FlagValidationView` + rate limiting específico (20/min) | 4h |
| HE-06 — Pistas progresivas | `ContadorFallos` (VO) + lógica de desbloqueo de `AyudaProgresiva` (5/15 fallos) | 5h |
| HE-06 | `ObtenerPistaQuery` + `HintView` | 3h |
| HE-07 — Progreso automático | `IProgresoRepository` + persistencia atómica (Unit of Work) | 4h |
| HE-10 — Historial | Modelo `HistorialCompletitud` + `ObtenerHistorialQuery` | 3h |
| Tests | Unitarios (ValidadorDeFlag, GestorDeSecuencia) + integración (flujo completo UC-02) | 8h |
| **Total Sprint 3** | | **54h** |

---

## Sprint 4 — Instructor, asignaciones y administración básica

**Épica: Assignments + Users + Laboratories (autoría)**

| Historia | Tarea | Est. |
|---|---|---|
| HI-02 — Crear laboratorios propios | `CrearLaboratorioUseCase`, `CrearSeccionUseCase`, `EditarSeccionUseCase` | 6h |
| HI-02 | `content_sanitizer.py` (sanitización HTML del contenido, previene XSS) | 4h |
| HI-02 | `PublicarLaboratorioUseCase` (valida ≥1 flag por sección práctica) | 3h |
| HI-03 — Copiar laboratorio predeterminado | `DuplicadorDeLaboratorio` (servicio) + `DuplicarLaboratorioUseCase` | 5h |
| HI-04/HI-05 — Filtros instructor | `FiltrarEstudiantesQuery`, filtros de labs propios | 4h |
| HI-06 — Panel principal | `ObtenerDashboardQuery` (vista instructor, agregados de asignaciones) | 4h |
| HI-09 — Invitación a laboratorio | Modelo `Asignación` + `InvitarEstudiantesUseCase` | 4h |
| HI-09 | `AceptarInvitacionUseCase` (dispara `AssignmentAccepted` → crea `Progreso` inicial) | 5h |
| HI-09 | `RechazarInvitacionUseCase` | 2h |
| HI-09 | `InvitationViewSet`, `AssignmentViewSet` + permisos | 4h |
| HA-01 — CRUD de usuarios | `ListarUsuariosQuery`, `ActualizarUsuarioUseCase`, `DeshabilitarUsuarioUseCase`, `HabilitarUsuarioUseCase` | 6h |
| HA-01 | Regla de auto-protección (admin no puede deshabilitarse a sí mismo) | 2h |
| Tests | Unitarios + integración (autoría, invitación, aceptación, admin) | 8h |
| **Total Sprint 4** | | **57h** |

---

## Sprint 5 — Exámenes, reportes, notificaciones, editor visual, vencimientos

**Épica: Progress + Reports + Notifications + Users (Admin) + Assignments**

| Historia | Tarea | Est. |
|---|---|---|
| HE-09/HI-08 — Examen final | Modelos `Examen`, `Pregunta`, `ResultadoExamen` | 4h |
| HE-09/HI-08 | `CalificadorDeExamen` (Strategy por tipo de pregunta) + `EnviarExamenUseCase` | 6h |
| HI-07 — Asignación con vencimiento | `VentanaVencimiento` (VO) + validación en `InvitarEstudiantesUseCase` | 3h |
| RF-32 — Cierre automático | `GestorDeVencimientos` + `CerrarAsignacionesVencidasJob` (Celery Beat) | 5h |
| HE-11 — Repetir laboratorio | Ajuste de `HistorialCompletitud` para permitir reintentos sin perder histórico | 3h |
| HE-12/HA-05 — Reportes | Modelos `Reporte`, `AdjuntoReporte` + `CrearReporteUseCase` | 4h |
| HE-12/HA-05 | `storage_adapter.py` (validación MIME real, límite de tamaño) | 4h |
| HA-05 | `CambiarEstadoReporteUseCase` + `ReportViewSet` (admin) | 3h |
| HE-13 — Notificaciones | Modelo `Notificación` + `event_listeners.py` (suscripción a eventos) | 5h |
| HE-13 | `email_channel.py`, `in_app_channel.py`, `celery_tasks.py` (envío asíncrono) | 5h |
| HE-13 | `NotificationViewSet` + `MarcarLeidaUseCase` | 2h |
| HA-02 — Editor visual (WYSIWYG) | Endpoint de edición de contenido para laboratorios predeterminados + reutilización de `content_sanitizer.py` | 5h |
| HA-03 — Dashboard de usuarios | Query agregada (usuarios por rol, labs activos, tasa de completitud) | 4h |
| Auditoría | Modelo `RegistroAuditoria` + `event_listeners.py` (suscripción a TODOS los eventos) + `ConsultarAuditoriaQuery` | 6h |
| Tests | Unitarios + integración (examen, reportes, notificaciones, auditoría) | 10h |
| **Total Sprint 5** | | **69h** |

---

## Sprints 6–8 — Autoría de contenido y estabilización

> Según el roadmap del PDF, estos sprints son principalmente de **carga de contenido real** (labs temáticos) por parte de instructores/administradores usando las herramientas ya construidas — no son sprints de nuevo desarrollo backend, salvo ajustes que surjan de QA.

**Épica: Laboratories (contenido) + QA general**

| Historia | Tarea | Est. |
|---|---|---|
| Carga de contenido | Soporte/ajustes al equipo de contenido mientras cargan labs reales (predeterminados) | 8h/sprint |
| QA funcional | Corrección de bugs reportados en pruebas internas de cada módulo | 12h/sprint |
| Refinamiento UX-API | Ajustes de contrato de API detectados al integrar con frontend real | 8h/sprint |
| **Total por sprint (x3)** | | **~28h** c/u |

---

## Sprint 9 — Rendimiento, cierre y despliegue

**Épica: Infraestructura / Sistema**

| Historia | Tarea | Est. |
|---|---|---|
| HA-04 — Dashboard de rendimiento | `RequestLoggingMiddleware` + endpoint de métricas agregadas (tiempos de respuesta, errores) | 5h |
| RNF-02.4 — Pruebas de carga | Diseñar y ejecutar pruebas Locust sobre catálogo, validación de flag, dashboard | 8h |
| RNF-06.3 — Cobertura de tests | Cerrar brechas de cobertura hasta ≥80% en Domain/Application | 10h |
| Seguridad | Revisión final OWASP Top 10 (checklist de Seguridad §7) + pentesting interno básico | 8h |
| DevOps | Configurar backups automáticos de PostgreSQL, monitoreo (`/health/`), variables de entorno en producción | 6h |
| Documentación | Congelar documentación técnica (API, BD, Arquitectura) para entrega institucional | 4h |
| Despliegue | Migración de datos, despliegue a producción en el servidor de pregrado, validación post-deploy | 6h |
| **Total Sprint 9** | | **47h** |

---

## Resumen de esfuerzo estimado

| Sprint | Horas estimadas |
|---|---|
| Sprint 0 (fundacional) | 40h |
| Sprint 1 | 54h |
| Sprint 2 | 39h |
| Sprint 3 | 54h |
| Sprint 4 | 57h |
| Sprint 5 | 69h |
| Sprints 6–8 (x3) | ~84h (28h c/u) |
| Sprint 9 | 47h |
| **Total backend** | **~444h** |

## Notas para Jira
- Cada fila de "Tarea" en este documento = una **Sub-task** de Jira dentro de su Historia.
- Cada "Historia" con ID (`HE-05`, `HI-02`...) debe crearse como **Story**, con la descripción/criterios de aceptación ya definidos en `historias-usuario-completas.md` (copiar/pegar directo).
- Vincular cada Story a su Épica de módulo y añadir el link a `casos-de-uso.md` (UC correspondiente) en la descripción, para que el desarrollador tenga el flujo detallado sin salir de Jira.
- Las estimaciones asumen **1 desarrollador por tarea, trabajando secuencialmente**; con más de un desarrollador backend, varias tareas dentro del mismo sprint son paralelizables (ya que pertenecen a módulos con bajo acoplamiento, según Arquitectura §8).
