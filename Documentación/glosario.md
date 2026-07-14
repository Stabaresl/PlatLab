# Glosario — PlatLAB

> Referencia única de términos, conceptos, plantillas y siglas usados en todo el proyecto. Pensado para onboarding rápido de cualquier miembro del equipo.

---

## 1. Nomenclatura de identificadores

| Prefijo | Significa | Ejemplo | Dónde vive |
|---|---|---|---|
| `HV-` | Historia de Usuario — Visitante | HV-04 | `historias-usuario-completas.md` |
| `HE-` | Historia de Usuario — Estudiante | HE-05 | ídem |
| `HI-` | Historia de Usuario — Instructor | HI-09 | ídem |
| `HA-` | Historia de Usuario — Administrador | HA-02 | ídem |
| `RF-` | Requisito Funcional | RF-09 | ídem |
| `RNF-` | Requisito No Funcional | RNF-01.5 | ídem |
| `UC-` | Caso de Uso | UC-02 | `casos-de-uso.md` |

---

## 2. Plantillas usadas en el proyecto

**Historia de Usuario:**
```
Como <Rol>
Quiero <Objetivo>
Para <Beneficio>

Prioridad: Alta/Media/Baja | Sprint: N
Criterios de aceptación: [...]
Dependencias: [...]
Riesgos: [...]
```

**Caso de Uso:**
```
Actor(es):
Precondiciones:
Flujo principal: (numerado)
Flujos alternativos: (A1, A2...)
Excepciones: (E1, E2...)
Postcondiciones:
```

**Formato de respuesta general del proyecto (definido en CLAUDE.md):**
```
Objetivo → Análisis → Decisiones → Resultado → Próximo Paso
```

---

## 3. Conceptos de Domain-Driven Design (DDD)

| Término | Definición | Ejemplo en PlatLAB |
|---|---|---|
| **Entidad** | Objeto con identidad propia que persiste en el tiempo, aunque sus atributos cambien | `Laboratorio`, `Progreso` |
| **Value Object (VO)** | Objeto sin identidad propia, definido solo por sus valores; inmutable | `Flag`, `Tema`, `EstadoAsignacion` |
| **Agregado** | Grupo de entidades/VOs que se tratan como una unidad de consistencia transaccional, con una raíz (Aggregate Root) | `Laboratorio` (raíz) agrupa `Sección`, `Flag`, `Examen` |
| **Servicio de Dominio** | Lógica de negocio que no pertenece naturalmente a una sola entidad, porque cruza varios agregados | `ValidadorDeFlag`, `DuplicadorDeLaboratorio` |
| **Domain Event** | Hecho relevante de negocio ya ocurrido, usado para desacoplar efectos secundarios entre módulos | `FlagValidated`, `AssignmentAccepted` |
| **Repository** | Interfaz que abstrae el acceso a persistencia de un agregado, para que Domain no conozca la base de datos | `ILaboratorioRepository` |
| **Unit of Work (UoW)** | Coordina que varias operaciones de escritura sobre el mismo agregado se confirmen (o reviertan) como una sola transacción | Guardar `Progreso` + `ProgresoSeccion` juntos |
| **Bounded Context** | Límite explícito donde un modelo de dominio es válido y consistente; en PlatLAB, cada módulo es un bounded context | `Laboratories`, `Progress`, etc. |

---

## 4. Capas de Clean Architecture

| Capa | Contiene | Regla clave |
|---|---|---|
| **Domain** | Entidades, VOs, Servicios de Dominio, Domain Events, interfaces de Repository | No conoce ninguna otra capa ni framework |
| **Application** | Casos de Uso (Commands) y Queries, DTOs, validadores | Orquesta Domain, no contiene reglas de negocio propias |
| **Infrastructure** | Modelos ORM, implementación de Repository/UoW, clientes externos (email, storage, Redis) | Implementa las interfaces que Domain define (Dependency Inversion) |
| **Presentation** | Views/ViewSets (DRF), Serializers, Permissions, URLs | Traduce HTTP ↔ DTOs de Application |

**Regla de dependencia:** las capas externas dependen de las internas, nunca al revés.

---

## 5. Patrones de diseño usados

| Patrón | Qué resuelve | Dónde se usa en PlatLAB |
|---|---|---|
| **Factory Method** | Encapsula la construcción de un objeto complejo | `DuplicadorDeLaboratorio`, creación de `Progreso` inicial |
| **Adapter** | Normaliza una interfaz externa distinta a la esperada internamente | `GoogleOAuthAdapter`, `GitHubOAuthAdapter` |
| **Decorator** | Añade comportamiento a un objeto sin modificar su clase | `CachedLaboratorioRepository` (cache sobre el repositorio real) |
| **Proxy** | Representa un objeto sin implementación real aún, o controla el acceso a otro objeto | Interfaz de `LabEnvironments` (reservado) |
| **Strategy** | Permite intercambiar un algoritmo según el contexto | `CalificadorDeExamen` (distinta calificación por tipo de pregunta) |
| **Observer** | Notifica a varios interesados cuando algo ocurre, sin acoplarlos | Domain Events (`Audit` y `Notifications` escuchando eventos) |
| **State** | Modela formalmente los estados válidos y sus transiciones | `ProgresoSeccion` (bloqueada→en_progreso→completada) |
| **Command** | Encapsula una operación de escritura como un objeto | `ValidarFlagCommand`, `AsignarLaboratorioCommand` |
| **Template Method** | Define el esqueleto de un algoritmo, dejando pasos específicos a las subclases | `BaseUseCase` (validar→ejecutar→persistir→emitir eventos) |
| **Repository** | Ver DDD arriba | — |
| **Unit of Work** | Ver DDD arriba | — |
| **Specification** | Encapsula un criterio de filtrado componible | Filtros de catálogo (`PorDificultad`, `PorTema`) |
| **CQRS (ligero)** | Separa operaciones de lectura (Query) de escritura (Command) donde el modelo difiere | Dashboards vs. Use Cases de escritura |
| **Dependency Injection (DI)** | Provee las dependencias de un objeto desde afuera, en vez de que las cree él mismo | Todo Use Case recibe sus repositorios por constructor |
| **Event Driven** | Arquitectura basada en reaccionar a eventos en vez de llamadas directas | Comunicación asíncrona entre módulos vía Celery |

---

## 6. Términos específicos del dominio PlatLAB

| Término | Significado |
|---|---|
| **Laboratorio predeterminado** | Creado por un Administrador, disponible para todos los instructores como base |
| **Laboratorio personalizado** | Creado por un Instructor desde cero, o copiado (duplicado) de uno predeterminado |
| **Flag** | Cadena secreta que el estudiante debe encontrar/enviar para validar que resolvió una práctica; se almacena cifrada, nunca en claro |
| **AyudaProgresiva** | Pista (a los 5 fallos) y paso a paso (a los 15 fallos) asociados a una flag |
| **ContadorFallos** | Contador de intentos fallidos de una flag específica; dispara el desbloqueo de `AyudaProgresiva` |
| **Secuencialidad obligatoria** | Regla de negocio: una sección no puede iniciarse hasta completar la anterior |
| **ProgresoSeccion** | Estado de una sección para un estudiante específico: `bloqueada` → `en_progreso` → `completada` |
| **HistorialCompletitud** | Registro de cada vez que un estudiante completa un laboratorio (permite repetirlo sin perder el historial) |
| **Asignación** | Vínculo entre un estudiante y un laboratorio, con ciclo de vida invitación→aceptación/rechazo→vencimiento |
| **LabEnvironments** | Módulo reservado (sin implementación) para una futura extensión con VMs/contenedores vulnerables en vivo |

---

## 7. Siglas y acrónimos técnicos

| Sigla | Significado |
|---|---|
| **DDD** | Domain-Driven Design |
| **SOLID** | Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion |
| **DRY** | Don't Repeat Yourself |
| **KISS** | Keep It Simple, Stupid |
| **YAGNI** | You Aren't Gonna Need It |
| **SoC** | Separation of Concerns |
| **CQRS** | Command Query Responsibility Segregation |
| **DTO** | Data Transfer Object |
| **ORM** | Object-Relational Mapping |
| **CRUD** | Create, Read, Update, Delete |
| **REST** | Representational State Transfer |
| **API** | Application Programming Interface |
| **SPA** | Single Page Application |
| **JWT** | JSON Web Token |
| **OAuth2** | Open Authorization 2.0 (estándar de autorización delegada) |
| **PKCE** | Proof Key for Code Exchange (extensión de seguridad para OAuth2 en clientes públicos) |
| **RBAC** | Role-Based Access Control |
| **CORS** | Cross-Origin Resource Sharing |
| **OWASP** | Open Web Application Security Project |
| **SSRF** | Server-Side Request Forgery |
| **XSS** | Cross-Site Scripting |
| **CSRF** | Cross-Site Request Forgery |
| **SQLi** | SQL Injection |
| **MIME** | Multipurpose Internet Mail Extensions (tipo real de un archivo) |
| **TTL** | Time To Live (tiempo de expiración de un dato en cache) |
| **C4 Model** | Modelo de diagramas de arquitectura por niveles: Contexto, Contenedores, Componentes, Código |
| **ER / ERD** | Entidad-Relación / Entity-Relationship Diagram |
| **3FN / 3NF** | Tercera Forma Normal (normalización de base de datos) |
| **DBML** | Database Markup Language (usado en dbdiagram.io) |
| **UUID** | Universally Unique Identifier |
| **PK / FK** | Primary Key / Foreign Key |
| **APM** | Application Performance Monitoring |

---

## 8. Stack tecnológico — qué es cada herramienta

| Herramienta | Rol en PlatLAB |
|---|---|
| **Django** | Framework backend en Python, base del monolito modular |
| **Django REST Framework (DRF)** | Construye la API REST sobre Django |
| **PostgreSQL** | Base de datos relacional, persistencia principal |
| **Redis** | Cache de catálogo, broker de Celery, almacenamiento de familias de refresh tokens |
| **Celery** | Ejecuta tareas asíncronas (notificaciones, exportación de reportes) |
| **Celery Beat** | Scheduler que dispara tareas periódicas (`GestorDeVencimientos`) |
| **SimpleJWT** | Librería para emitir/validar JWT en DRF |
| **django-allauth** | Maneja el flujo OAuth2 con Google y GitHub |
| **django-simple-history** | Apoya la trazabilidad de cambios (complementa `audit_registroauditoria`) |
| **drf-spectacular** | Genera la documentación OpenAPI/Swagger de la API |
| **pytest-django** | Framework de testing para el backend |
| **Docker / Docker Compose** | Contenerización y orquestación de los servicios (web, worker, Redis, Postgres) |

## Estado
✅ Glosario cerrado. Se actualiza si en Testing/DevOps (puntos pendientes) aparecen términos nuevos.
