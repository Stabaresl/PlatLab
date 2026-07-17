# Backend — PlatLAB

> Traduce cada Caso de Uso ya aprobado en componentes concretos de Application/Infrastructure/Presentation, por módulo. Sin código — nombres de clases y responsabilidades únicamente.

---

## 0. Shared / Kernel

| Capa | Componentes |
|---|---|
| **Domain** | `BaseEntity`, `BaseValueObject`, `DomainEvent` (clase base), excepciones base (`BusinessRuleViolationError`, `NotFoundError`, `ConflictError`) heredadas por todos los módulos |
| **Application** | `BaseUseCase` (Template Method: validar entrada → ejecutar lógica de dominio → persistir vía Unit of Work → despachar eventos) |
| **Infrastructure** | `EventDispatcher` (registra listeners por tipo de evento y los invoca — hoy en memoria/síncrono vía Celery para efectos asíncronos; mañana reemplazable por un bus real sin tocar Domain/Application), `BaseUnitOfWork`, `RedisClient`, `EmailClient`, `StorageClient` |

Todos los módulos dependen de `Shared`; `Shared` no depende de ningún módulo (regla ya fijada en Arquitectura).

---

## 1. Authentication

| Capa | Componentes |
|---|---|
| **Casos de uso (Application)** | `RegistrarUsuarioUseCase`, `LoginUseCase`, `OAuthLoginUseCase` (usa `VinculadorDeCuenta`), `RefreshTokenUseCase`, `LogoutUseCase`, `LogoutAllUseCase`, `SolicitarRecuperacionUseCase`, `ConfirmarRecuperacionUseCase`, `VerificarEmailUseCase` |
| **Repositorios** | `IUserRepository` *(interfaz definida en Users, consumida vía su Application Service)*, `IRefreshTokenRepository` (implementado sobre **Redis**, no Postgres — almacena la familia de tokens con TTL igual a la expiración del refresh) |
| **Controladores** | `RegisterView`, `LoginView`, `OAuthCallbackView`, `TokenRefreshView`, `LogoutView`, `PasswordResetView`, `EmailVerificationView` |
| **DTOs (Application, framework-agnostic)** | `RegistroDTO`, `LoginDTO`, `TokenPairDTO`, `OAuthProfileDTO` |
| **Serializers (Presentation/DRF, mapean HTTP↔DTO)** | `RegistroRequestSerializer`, `LoginRequestSerializer`, `TokenResponseSerializer`, `PasswordResetSerializer` |

---

## 2. Users

| Capa | Componentes |
|---|---|
| **Casos de uso** | `ObtenerPerfilQuery`, `ActualizarPerfilUseCase`, `ListarUsuariosQuery` (filtros nombre/rol/activo), `ObtenerUsuarioQuery`, `ActualizarUsuarioUseCase` (rol/datos, con regla de auto-protección UC-08 E1), `DeshabilitarUsuarioUseCase`, `HabilitarUsuarioUseCase` |
| **Repositorios** | `IUserRepository` (compartida con Authentication, misma interfaz) |
| **Controladores** | `MeView`, `UserViewSet` (admin CRUD) |
| **DTOs** | `PerfilDTO`, `UsuarioListItemDTO`, `UsuarioDetalleDTO`, `ActualizarUsuarioRequestDTO` |

---

## 3. Laboratories

| Capa | Componentes |
|---|---|
| **Casos de uso** | `ListarLaboratoriosQuery`, `ObtenerDetalleLaboratorioQuery`, `ObtenerTOCQuery`, `CrearLaboratorioUseCase`, `EditarLaboratorioUseCase`, `PublicarLaboratorioUseCase`, `DuplicarLaboratorioUseCase` (usa `DuplicadorDeLaboratorio`), `CrearSeccionUseCase`, `EditarSeccionUseCase`, `DefinirFlagUseCase`, `CrearExamenUseCase`, `AgregarPreguntaUseCase` |
| **Repositorios** | `ILaboratorioRepository`, `ISeccionRepository`, `IExamenRepository` (todos dentro del mismo agregado, pueden compartir una sola `ILaboratorioRepository` con métodos anidados) |
| **Controladores** | `LaboratorioViewSet`, `SeccionViewSet` (nested bajo laboratorio), `FlagView` (write-only), `ExamenViewSet` |
| **DTOs** | `LaboratorioListItemDTO`, `LaboratorioDetalleDTO` (varía según rol/asignación), `TOCDTO`, `CrearLaboratorioRequestDTO`, `SeccionRequestDTO`, `DefinirFlagRequestDTO` (nunca se serializa `valor` de vuelta) |

---

## 4. Assignments

| Capa | Componentes |
|---|---|
| **Casos de uso** | `InvitarEstudiantesUseCase`, `AceptarInvitacionUseCase` (crea `Progreso` inicial vía evento `AssignmentAccepted`), `RechazarInvitacionUseCase`, `ModificarVencimientoUseCase`, `ListarAsignacionesQuery`, `FiltrarEstudiantesQuery` |
| **Repositorios** | `IAsignacionRepository` |
| **Controladores** | `InvitationViewSet`, `AssignmentViewSet` |
| **DTOs** | `InvitarRequestDTO`, `AsignacionDTO`, `EstudianteFiltroDTO` |

---

## 5. Progress

| Capa | Componentes |
|---|---|
| **Casos de uso** | `ObtenerDashboardQuery`, `ObtenerDetalleProgresoQuery`, `ObtenerContenidoSeccionQuery` (valida `ProgresoSeccion ≠ bloqueada`), `ValidarFlagUseCase` (usa `ValidadorDeFlag` + `GestorDeSecuencia`), `ObtenerPistaQuery`, `EnviarExamenUseCase` (usa `CalificadorDeExamen`), `ObtenerHistorialQuery` |
| **Repositorios** | `IProgresoRepository` (incluye `ProgresoSeccion`, `IntentoFlag`, `ResultadoExamen`, `HistorialCompletitud` como parte del mismo agregado) |
| **Controladores** | `ProgressDashboardView`, `ProgressDetailView`, `SectionContentView`, `FlagValidationView`, `HintView`, `ExamSubmissionView`, `HistoryView` |
| **DTOs** | `DashboardDTO`, `ProgresoDetalleDTO`, `ContenidoSeccionDTO`, `ValidarFlagRequestDTO`/`ValidarFlagResponseDTO`, `PistaDTO`, `EnviarExamenRequestDTO`, `ResultadoExamenDTO`, `HistorialDTO` |

---

## 6. Reports

| Capa | Componentes |
|---|---|
| **Casos de uso** | `CrearReporteUseCase`, `ListarReportesPropiosQuery`, `ListarReportesQuery` (admin, filtros), `CambiarEstadoReporteUseCase` |
| **Repositorios** | `IReporteRepository` (incluye `AdjuntoReporte`) |
| **Controladores** | `ReportViewSet` |
| **DTOs** | `CrearReporteRequestDTO` (multipart), `ReporteDTO`, `CambiarEstadoRequestDTO` |

---

## 7. Notifications

| Capa | Componentes |
|---|---|
| **Casos de uso (expuestos)** | `ListarNotificacionesQuery`, `MarcarLeidaUseCase` |
| **Casos de uso (internos, sin endpoint)** | `DespacharNotificacionUseCase` — invocado por el `DespachadorDeNotificaciones` al reaccionar a eventos de dominio (Assignments, Reports, Progress) |
| **Repositorios** | `INotificacionRepository` |
| **Controladores** | `NotificationViewSet` |
| **DTOs** | `NotificacionDTO` |

---

## 8. Audit

| Capa | Componentes |
|---|---|
| **Casos de uso (expuestos)** | `ConsultarAuditoriaQuery` (filtros actor/acción/fecha) |
| **Casos de uso (internos, sin endpoint)** | `RegistrarAuditoriaUseCase` — invocado por `RegistradorDeAuditoria` al escuchar cualquier evento de dominio relevante |
| **Repositorios** | `IAuditoriaRepository` (solo `save()` y `find()`, sin `update()`/`delete()` — refuerza append-only también a nivel de interfaz) |
| **Controladores** | `AuditViewSet` (solo lectura) |
| **DTOs** | `RegistroAuditoriaDTO` |

---

## 9. Sistema (transversal, sin módulo propio)

| Componente | Tipo | Responsabilidad |
|---|---|---|
| `CerrarAsignacionesVencidasJob` | Celery Beat task | Ejecuta `GestorDeVencimientos` periódicamente (UC-07) — no tiene controlador HTTP |
| `HealthCheckView` | Controlador | `/health/` — verifica conexión a PostgreSQL y Redis |

---

## 10. Middleware (cross-cutting, aplica a todos los módulos)

| Middleware | Responsabilidad | Se ejecuta en |
|---|---|---|
| `JWTAuthenticationMiddleware` | Valida el Bearer token, resuelve el usuario autenticado y su rol antes de llegar al controlador | Toda request, salvo rutas públicas explícitas |
| `AuditContextMiddleware` | Captura `actor_id` e `ip` de la request y los expone en un contexto (context-var) para que `RegistradorDeAuditoria` no dependa de pasar el request manualmente a través de las capas | Toda request autenticada |
| `RateLimitMiddleware` | Aplica los límites definidos en Seguridad §5 (login, recuperación, validación de flag, global) | Endpoints específicos + catch-all |
| `ExceptionHandlerMiddleware` | Traduce excepciones de dominio (`BusinessRuleViolation`, `NotFoundError`, `ConflictError`, etc.) al formato estándar de error de API §2, evitando que un `try/except` se repita en cada controlador | Toda request |
| `CORSMiddleware` | Aplica la whitelist de orígenes definida en Seguridad §8 | Toda request |
| `RequestLoggingMiddleware` | Log estructurado de tiempo de respuesta por endpoint, insumo para el dashboard de rendimiento (HA-04) | Toda request |

**Orden de ejecución (entrada de request):** CORS → RateLimit → JWTAuthentication → AuditContext → *(controlador → Application → Domain → Infrastructure)* → ExceptionHandler (en la salida, si algo falla) → RequestLogging.

---

## 11. Regla general de dependencia (recordatorio de Arquitectura)

Ningún **Controlador** invoca **Domain** directamente. Ningún **Caso de Uso** importa un modelo Django. Todo Caso de Uso recibe sus repositorios por **Dependency Injection** (constructor), nunca los instancia — es lo que permite testear cada Caso de Uso con repositorios en memoria sin levantar PostgreSQL.

## Estado
✅ Backend definido para los 8 módulos activos + componentes de Sistema. `LabEnvironments` sigue sin Application/Infrastructure — solo el stub de interfaz reservado en Dominio v2.
