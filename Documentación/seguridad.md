# Seguridad — PlatLAB

> Consolida las decisiones de seguridad ya tomadas en Dominio, Arquitectura, Base de Datos y API, y cierra los vacíos que faltaban (RBAC explícito, OWASP mapeado, cabeceras, CORS, gestión de archivos).

---

## 1. RBAC — Matriz de permisos

| Recurso / Acción | Visitante | Estudiante | Instructor | Administrador |
|---|---|---|---|---|
| Catálogo público (`GET /laboratories/`) | ✅ solo `publicado` | ✅ | ✅ + propios `borrador` | ✅ todos |
| Detalle + TOC de laboratorio | ✅ (sin contenido) | ✅ (sin contenido si no asignado) | ✅ | ✅ |
| Contenido de sección / flags | ❌ | ✅ solo si `ProgresoSeccion ≠ bloqueada` | ✅ (edición, solo propios) | ✅ (edición, solo predeterminados) |
| Crear laboratorio | ❌ | ❌ | ✅ tipo `personalizado` | ✅ tipo `predeterminado` |
| Duplicar laboratorio predeterminado | ❌ | ❌ | ✅ | ✅ (no aplica, ya es dueño) |
| Editar laboratorio predeterminado | ❌ | ❌ | ❌ (403, UC-05 E1) | ✅ |
| Invitar estudiantes / asignar | ❌ | ❌ | ✅ (a sus labs) | ❌ (fuera de su rol de negocio) |
| Aceptar/rechazar invitación | ❌ | ✅ (propia) | ❌ | ❌ |
| Validar flag / progreso | ❌ | ✅ (propio) | ❌ (solo lectura de sus estudiantes) | ❌ |
| Crear reporte | ❌ | ✅ | ❌ | ❌ |
| Gestionar reportes (cambiar estado) | ❌ | ❌ | ❌ | ✅ |
| CRUD de usuarios / roles | ❌ | ❌ | ❌ | ✅ |
| Consultar auditoría | ❌ | ❌ | ❌ | ✅ |

**Regla de implementación:** el permiso se valida en dos niveles — (1) `permission_classes` de DRF por rol (Presentation), y (2) reglas de propiedad dentro del Use Case (Application), ej. "instructor edita solo si `laboratorio.instructor_id == usuario.id`". El nivel 1 nunca es suficiente por sí solo (evita que un chequeo de rol correcto oculte una fuga de propiedad).

---

## 2. JWT

| Parámetro | Valor |
|---|---|
| Algoritmo | HS256 (o RS256 si se separa el emisor de tokens a futuro) |
| Expiración access token | 15 minutos |
| Expiración refresh token | 7 días |
| Rotación | Cada uso de refresh genera uno nuevo; el anterior queda invalidado (RF-07) |
| Detección de reuso | Si un refresh ya usado se reintenta, se invalida **toda la familia** de tokens de esa sesión (posible robo) |
| Almacenamiento recomendado (frontend) | Access token en memoria (no localStorage); refresh token en cookie `HttpOnly, Secure, SameSite=Strict` |
| Claims mínimos | `sub` (user_id), `rol`, `exp`, `jti` (para poder revocar individualmente) |

---

## 3. OAuth2 (Google / GitHub)

- Flujo: **Authorization Code + PKCE** (recomendado aunque el cliente sea una SPA conocida, mitiga interceptación del code).
- El backend valida el `state` recibido contra el emitido, para prevenir CSRF sobre el flujo de OAuth.
- Tras el callback, el backend resuelve el email verificado del proveedor y aplica la regla de `VinculadorDeCuenta` (Dominio v2): si el email ya existe con otro proveedor, requiere confirmación explícita del usuario antes de vincular (evita account takeover, UC-01 E4).
- Los `client_secret` de Google/GitHub se gestionan como variables de entorno (ver punto 9), nunca en código fuente.

---

## 4. Validación y Sanitización

| Punto de entrada | Riesgo | Mitigación |
|---|---|---|
| Contenido teórico de secciones (editor WYSIWYG, HA-02) | XSS almacenado | Sanitización server-side con whitelist de tags/atributos (ej. `bleach` en Python) antes de persistir; nunca confiar en el sanitizado del frontend |
| Adjuntos de reporte (`AdjuntoReporte`) | Subida de archivo malicioso | Validación de tipo MIME real (no por extensión), límite de tamaño, almacenamiento fuera del webroot, sin ejecución (ej. S3/MinIO con `Content-Disposition: attachment`) |
| Todos los serializers de entrada (DRF) | Inyección, datos malformados | Validación de tipo/longitud/formato en el serializer antes de llegar a Application; nunca se construyen queries con concatenación de strings (ORM parametrizado por defecto) |
| Flags ingresadas por estudiante | Fuerza bruta / scripting | Rate limiting específico (ya definido en API §12) + comparación por hash constante en tiempo (evita timing attacks triviales) |
| Campos `respuestas` (jsonb) en exámenes | Inyección de estructuras inesperadas | Validación de schema del JSON contra las `Pregunta` reales del examen antes de persistir |

---

## 5. Rate Limiting (resumen, detalle completo en API §12)

| Ámbito | Límite |
|---|---|
| Login | 5 intentos / 15 min por IP+usuario |
| Recuperación de contraseña | 3 solicitudes / hora por email |
| Validación de flag | 20 intentos / minuto por usuario+sección |
| Global (catch-all) | 100 requests/minuto por IP, para endpoints públicos no cubiertos arriba (catálogo, health) |

---

## 6. Auditoría (resumen, detalle completo en BD §"audit_registroauditoria")

- Registro append-only de: login, cambio de rol, deshabilitar usuario, CRUD de laboratorio, publicación, duplicación, aceptación/rechazo de invitación, vencimiento, cambio de estado de reporte.
- Retención mínima 6 meses (RNF-01.8) — **esto no cambia**, es una política de retención de datos, distinta al ciclo de versionado de la API que sí se ajustó a 1 mes.
- Acceso exclusivo de Administrador, vía `/audit/` (API §10).

---

## 7. OWASP Top 10 (2021) — mapeo a controles de PlatLAB

| Categoría OWASP | Control aplicado en PlatLAB |
|---|---|
| **A01 — Broken Access Control** | RBAC de dos niveles (§1); validación de propiedad en Application, no solo en Presentation |
| **A02 — Cryptographic Failures** | Passwords con bcrypt/argon2; flags cifradas + hash de comparación (nunca en claro); HTTPS obligatorio en todos los endpoints |
| **A03 — Injection** | ORM parametrizado (Django); sanitización de contenido WYSIWYG (§4); validación de schema en `respuestas` de examen |
| **A04 — Insecure Design** | Secuencialidad obligatoria de secciones y bloqueo de examen sin completar (reglas de dominio, no solo de UI); separación estricta predeterminado/personalizado |
| **A05 — Security Misconfiguration** | `DEBUG=False` en producción, cabeceras de seguridad (§8), CORS restringido (§8), gestión de secretos vía variables de entorno (§9) |
| **A06 — Vulnerable and Outdated Components** | Escaneo de dependencias (Dependabot/pip-audit) — se detalla en DevOps, punto 15 |
| **A07 — Identification and Authentication Failures** | JWT con expiración corta + rotación (§2), rate limiting en login (§5), OAuth2 con PKCE (§3) |
| **A08 — Software and Data Integrity Failures** | Auditoría append-only (§6); versionado de contenido vía metadata de auditoría (BD §5) |
| **A09 — Security Logging and Monitoring Failures** | `RegistradorDeAuditoria` transversal (Dominio v2); dashboard de rendimiento/errores (HA-04) |
| **A10 — Server-Side Request Forgery (SSRF)** | No aplica hoy (no hay funcionalidad que haga fetch de URLs arbitrarias por el usuario); se reevalúa si `LabEnvironments` se implementa a futuro |

---

## 8. Cabeceras de seguridad y CORS

| Cabecera | Valor |
|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` (previene clickjacking, RNF-01.1) |
| `Content-Security-Policy` | Restrictiva, sin `unsafe-inline` para scripts |
| `CORS` | Whitelist explícita del dominio del frontend (React), sin `*` en producción |

---

## 9. Gestión de secretos

`SECRET_KEY` de Django, credenciales de PostgreSQL, `client_secret` de OAuth y credenciales SMTP se gestionan como **variables de entorno**, inyectadas vía Docker Compose (o el mecanismo que defina el servidor de pregrado) — nunca versionadas en el repositorio. Detalle de implementación completo en **punto 15: DevOps**.

## Estado
✅ Seguridad consolidada. Ningún control queda huérfano de una decisión previa — todo remite a Dominio v2, Arquitectura, BD o API ya aprobados.
