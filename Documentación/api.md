# API REST — PlatLAB

> REST por defecto, versionado por URL. Base: `https://<host>/api/v1/`

---

## 1. Principios generales

| Aspecto | Definición |
|---|---|
| **Versionado** | Prefijo `/api/v1/` en todas las rutas. Al introducir `v2`, `v1` se mantiene activo **máximo 1 mes**, anunciado con header `Deprecation: true` y `Sunset: <fecha>`. Ciclo corto justificado: mismo equipo controla frontend y backend, desplegados juntos por sprint. |
| **Formato** | JSON (`application/json`) en request y response. |
| **Paginación** | Cursor-based en listados grandes (catálogo, auditoría); `?limit=20&cursor=...`. Respuesta incluye `next`, `previous`, `results`. |
| **Filtros** | Query params combinables, ej. `?dificultad=avanzado&tema=redes`. |
| **Autenticación** | JWT Bearer (`Authorization: Bearer <access_token>`) en todo endpoint salvo los explícitamente públicos (catálogo visitante, auth). |
| **Autorización** | RBAC por rol + reglas de propiedad (ej. instructor solo edita sus propios laboratorios) validadas en Application, no solo en Presentation. |
| **Documentación** | Autogenerada con `drf-spectacular`, expuesta en `/api/v1/schema/` y `/api/v1/docs/`. |

---

## 2. Formato estándar de error

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "La solicitud contiene datos inválidos.",
    "details": [
      { "field": "email", "message": "Este correo ya está registrado." }
    ]
  }
}
```

| Código HTTP | `error.code` | Cuándo se usa |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Datos de entrada inválidos (serializer) |
| 401 | `UNAUTHENTICATED` | Token ausente, inválido o expirado |
| 403 | `FORBIDDEN` | Autenticado pero sin permiso (rol o propiedad) |
| 404 | `NOT_FOUND` | Recurso inexistente |
| 409 | `CONFLICT` | Ej. asignación duplicada, email ya registrado |
| 422 | `BUSINESS_RULE_VIOLATION` | Ej. examen sin secciones completas, edición de predeterminado por instructor |
| 429 | `RATE_LIMITED` | Rate limiting excedido (login, validación de flag) |
| 500 | `INTERNAL_ERROR` | Error no controlado |

---

## 3. Autenticación

| Endpoint | Método | Descripción | Público |
|---|---|---|---|
| `/auth/register/` | POST | Registro con email/password (HV-04) | Sí |
| `/auth/oauth/{provider}/` | POST | Callback OAuth (`google`\|`github`) — recibe `code`, retorna JWT | Sí |
| `/auth/login/` | POST | Login email/password → `{access, refresh}` | Sí |
| `/auth/refresh/` | POST | Rota refresh token, detecta reuso (RF-07) | Sí (requiere refresh válido) |
| `/auth/logout/` | POST | Invalida el refresh token actual | No |
| `/auth/logout-all/` | POST | Invalida todos los refresh tokens del usuario (HE-14) | No |
| `/auth/password-reset/` | POST | Solicita token de recuperación (RF-04) | Sí |
| `/auth/password-reset/confirm/` | POST | Confirma nueva contraseña con token | Sí |
| `/auth/verify-email/{token}/` | GET | Verifica correo tras registro | Sí |

**DTO — Registro:**
```json
// Request
{ "email": "ana@uni.edu", "password": "Segura123", "password_confirm": "Segura123", "nombre_completo": "Ana Pérez" }
// Response 201
{ "id": "uuid", "email": "ana@uni.edu", "rol": "estudiante", "email_verificado": false }
```
**Validaciones:** email único y formato válido; password ≥8 car., 1 mayúscula, 1 número; `password == password_confirm`.
**Errores:** 400 (formato), 409 (email ya registrado — mensaje genérico para evitar enumeración).

**DTO — Login:**
```json
// Response 200
{ "access": "jwt...", "refresh": "jwt...", "expires_in": 900, "rol": "estudiante" }
```
**Errores:** 401 (credenciales inválidas), 429 (5 intentos fallidos en 15 min → bloqueo, RNF-01.4).

---

## 4. Users

| Endpoint | Método | Descripción | Permisos |
|---|---|---|---|
| `/users/me/` | GET | Perfil propio | Autenticado |
| `/users/me/` | PATCH | Editar perfil propio (no rol) | Autenticado |
| `/users/` | GET | Listar/filtrar usuarios (`?nombre=&rol=&activo=`) | Admin (HA-01) |
| `/users/{id}/` | GET | Detalle de usuario | Admin |
| `/users/{id}/` | PATCH | Editar rol/datos | Admin |
| `/users/{id}/disable/` | POST | Deshabilitar (soft-delete) | Admin |
| `/users/{id}/enable/` | POST | Reactivar | Admin |

**Validaciones clave:** un admin no puede deshabilitarse ni quitarse su propio rol (UC-08, E1) → 422 `BUSINESS_RULE_VIOLATION`.

---

## 5. Laboratories

| Endpoint | Método | Descripción | Permisos |
|---|---|---|---|
| `/laboratories/` | GET | Catálogo con filtros `?dificultad=&tema=` | Público (solo `publicado`); Instructor ve también sus `borrador` |
| `/laboratories/{id}/` | GET | Detalle (descripción, nivel, temas). Sin asignación (visitante o estudiante): sin contenido de secciones — mismo nivel de acceso para ambos, nunca menos para el estudiante | Público / Según rol |
| `/laboratories/{id}/toc/` | GET | Tabla de contenido (solo títulos) | Público |
| `/laboratories/` | POST | Crear laboratorio (`tipo` se infiere del rol: Instructor→personalizado, Admin→predeterminado) | Instructor, Admin |
| `/laboratories/{id}/` | PATCH | Editar (bloqueado si `predeterminado` y actor no es Admin, UC-05 E1) | Instructor (propio), Admin |
| `/laboratories/{id}/publish/` | POST | `borrador` → `publicado` (valida ≥1 flag por sección práctica) | Instructor (propio), Admin |
| `/laboratories/{id}/duplicate/` | POST | Copia un predeterminado (UC-05) | Instructor |
| `/laboratories/{id}/sections/` | POST | Crear sección | Instructor (propio), Admin |
| `/laboratories/{id}/sections/{section_id}/` | PATCH | Editar sección | Instructor (propio), Admin |
| `/laboratories/{id}/sections/{section_id}/flag/` | PUT | Definir/actualizar flag + pistas (write-only, nunca se retorna en GET) | Instructor (propio), Admin |
| `/laboratories/{id}/exam/` | POST | Crear examen | Instructor (propio), Admin |
| `/laboratories/{id}/exam/questions/` | POST | Agregar pregunta | Instructor (propio), Admin |

**DTO — Crear sección:**
```json
{ "titulo": "Inyección SQL básica", "contenido_teorico": "...", "orden": 3, "tiene_practica": true }
```
**Validaciones:** `orden` único dentro del laboratorio (409 si colisiona); si `tiene_practica=true`, la publicación exige flag asociada.

**DTO — Definir flag:**
```json
{ "valor": "FLAG{sql_1nj3ct10n}", "pista": "Revisa el parámetro `id` del formulario", "paso_a_paso": "1. Prueba ' OR 1=1--  2. ..." }
```
El backend calcula el hash y **nunca** retorna `valor` en ninguna respuesta posterior (RNF-01.5).

---

## 6. Assignments

| Endpoint | Método | Descripción | Permisos |
|---|---|---|---|
| `/assignments/invitations/` | POST | Invitar estudiante(s) a un laboratorio, con `fecha_vencimiento` (HI-07, HI-09) | Instructor |
| `/assignments/invitations/{id}/accept/` | POST | Aceptar — crea `Progreso` inicial (UC-06) | Estudiante (destinatario) |
| `/assignments/invitations/{id}/reject/` | POST | Rechazar | Estudiante (destinatario) |
| `/assignments/` | GET | Listar asignaciones propias (instructor: las que creó; estudiante: las suyas) | Instructor, Estudiante |
| `/assignments/students/` | GET | Filtrar estudiantes por nombre/avance/laboratorio (HI-04) | Instructor |

**DTO — Invitar:**
```json
{ "laboratorio_id": "uuid", "estudiantes": ["email_o_username", "..."], "fecha_vencimiento": "2026-08-01T23:59:00Z" }
```
**Validaciones:** `fecha_vencimiento > ahora`; laboratorio debe estar `publicado`; 409 si el estudiante ya tiene asignación activa a ese laboratorio (UC-06, E2).

---

## 7. Progress

| Endpoint | Método | Descripción | Permisos |
|---|---|---|---|
| `/progress/me/` | GET | Dashboard del estudiante (HE-01) | Estudiante |
| `/progress/{assignment_id}/` | GET | Detalle de progreso (secciones, estados) | Estudiante (propio), Instructor (si es su asignación) |
| `/progress/{assignment_id}/sections/{section_id}/` | GET | Contenido teórico de la sección (HE-04). 403 si `ProgresoSeccion.estado = bloqueada` | Estudiante (propio) |
| `/progress/{assignment_id}/sections/{section_id}/flag/` | POST | Validar flag (UC-02) | Estudiante (propio) |
| `/progress/{assignment_id}/sections/{section_id}/hint/` | GET | Obtener pista/paso a paso ya desbloqueados | Estudiante (propio) |
| `/progress/{assignment_id}/exam/` | POST | Enviar respuestas del examen (UC-03) | Estudiante (propio) |
| `/progress/{assignment_id}/history/` | GET | Historial de completitudes (HE-10, HE-11) | Estudiante (propio) |

**DTO — Validar flag:**
```json
// Request
{ "valor": "FLAG{sql_1nj3ct10n}" }
// Response 200 (correcta)
{ "correcto": true, "seccion_desbloqueada": "uuid-siguiente-seccion" }
// Response 200 (incorrecta, con pista desbloqueada)
{ "correcto": false, "intentos_fallidos": 5, "pista_disponible": true, "pista": "Revisa el parámetro `id`..." }
```
**Errores:** 403 si la sección está `bloqueada` para ese estudiante (secuencialidad obligatoria); 429 si excede el rate limit específico del endpoint (UC-02, E1).

**DTO — Enviar examen:**
```json
{ "respuestas": [{ "pregunta_id": "uuid", "respuesta": "opcion_b" }] }
```
**Validaciones:** todas las `ProgresoSeccion` deben estar `completada` (422 si no, UC-03 E1).

---

## 8. Reports

| Endpoint | Método | Descripción | Permisos |
|---|---|---|---|
| `/reports/` | POST | Crear reporte (HE-12) | Estudiante |
| `/reports/me/` | GET | Mis reportes y su estado | Estudiante |
| `/reports/` | GET | Listar/filtrar todos (`?estado=&laboratorio=`) | Admin (HA-05) |
| `/reports/{id}/` | PATCH | Cambiar estado (`en_revision`, `resuelto`, `no_reproducible`) | Admin |

**DTO — Crear reporte:**
```json
{ "laboratorio_id": "uuid", "seccion_id": "uuid", "descripcion": "El flag no valida aunque es correcta", "adjunto": "<multipart file>" }
```
**Validaciones:** `descripcion` ≥10 caracteres (400 si no).

---

## 9. Notifications

| Endpoint | Método | Descripción | Permisos |
|---|---|---|---|
| `/notifications/` | GET | Listar propias (`?leida=false`) | Autenticado |
| `/notifications/{id}/read/` | PATCH | Marcar como leída | Autenticado (propio) |

---

## 10. Audit

| Endpoint | Método | Descripción | Permisos |
|---|---|---|---|
| `/audit/` | GET | Listar con filtros `?actor=&accion=&desde=&hasta=` | Admin |

---

## 11. Sistema

| Endpoint | Método | Descripción | Público |
|---|---|---|---|
| `/health/` | GET | Estado de BD/dependencias (HA-04, RF-28) | Sí |
| `/schema/` | GET | Especificación OpenAPI | Sí |

---

## 12. Rate limiting aplicado (RNF-01.4, extendido)

| Endpoint | Límite |
|---|---|
| `/auth/login/` | 5 intentos / 15 min por IP+usuario |
| `/auth/password-reset/` | 3 solicitudes / hora por email |
| `/progress/*/flag/` | 20 intentos / minuto por usuario+sección (evita scripting sobre UC-02) |

## Estado
✅ API definida sobre los 8 módulos activos + Sistema. `LabEnvironments` no expone endpoints aún (módulo reservado).
