# Casos de Uso — PlatLAB

> Se documentan únicamente las funcionalidades con lógica de negocio, flujos alternos/excepciones relevantes o múltiples actores. Las funcionalidades de solo lectura/filtrado (catálogo, dashboards, historial, TOC) quedan cubiertas por sus criterios de aceptación en el documento de Historias de Usuario.

---

## UC-01 — Autenticación y gestión de cuenta
**HU relacionadas:** HV-04, RF-02, RF-03
**Actores:** Visitante, Estudiante, Instructor, Administrador

**Precondiciones:** El sistema tiene configurados los proveedores OAuth (Google, GitHub) y el servicio de envío de correo.

**Flujo principal (Registro con email):**
1. El visitante ingresa correo, contraseña y confirmación en el formulario de registro.
2. El sistema valida formato de correo, unicidad y política de contraseña (mínimo 8 caracteres, 1 mayúscula, 1 número).
3. El sistema crea el usuario con rol `Estudiante` por defecto y estado `activo`.
4. El sistema envía correo de verificación.
5. El usuario confirma su correo mediante el enlace recibido.
6. El sistema marca la cuenta como verificada y redirige al dashboard del estudiante.

**Flujo alternativo A1 — Registro con OAuth (Google/GitHub):**
1a. El visitante selecciona "Continuar con Google/GitHub".
2a. El sistema recibe el perfil OAuth (email, nombre) del proveedor.
3a. Si el email no existe en el sistema → crea usuario nuevo con rol `Estudiante`, marcado como verificado automáticamente (el proveedor ya validó el email).
4a. Si el email ya existe con una cuenta creada por password → el sistema vincula el proveedor OAuth a la cuenta existente (previa confirmación del usuario) y continúa el flujo desde el paso 6.

**Flujo alternativo A2 — Inicio de sesión:**
1b. El usuario ingresa credenciales o usa OAuth.
2b. El sistema valida credenciales y genera access token + refresh token (JWT).
3b. El sistema redirige según el rol: Estudiante → dashboard; Instructor → panel principal; Administrador → panel admin.

**Flujo alternativo A3 — Recuperación de contraseña:**
1c. El usuario solicita recuperación ingresando su correo.
2c. El sistema genera un token de un solo uso con expiración de 15 minutos y lo envía por correo.
3c. El usuario define nueva contraseña mediante el enlace; el sistema invalida el token tras su uso.

**Excepciones:**
- E1: Correo ya registrado en el paso 2 → el sistema muestra error específico sin confirmar si el email existe con otro proveedor (evitar enumeración de usuarios).
- E2: Token de recuperación expirado o ya usado → el sistema solicita generar uno nuevo.
- E3: 5 intentos fallidos de login en 15 minutos desde la misma IP/usuario → bloqueo temporal (RNF-01.4).
- E4: Colisión OAuth-password sin confirmación del usuario → el sistema NO vincula automáticamente; requiere verificación explícita para evitar takeover de cuenta.

**Postcondiciones:** Usuario autenticado con sesión válida (JWT) y rol asignado.

---

## UC-02 — Resolución de práctica (flags y pistas progresivas)
**HU relacionadas:** HE-05, HE-06, HE-07
**Actor:** Estudiante

**Precondiciones:** El estudiante tiene acceso vigente al laboratorio y se encuentra en una sección con práctica.

**Flujo principal:**
1. El estudiante escribe una flag en el campo de la sección práctica y la envía.
2. El sistema calcula el hash de la flag ingresada y lo compara contra el hash almacenado (la flag real nunca se expone).
3. Si coincide, el sistema marca la flag como resuelta, registra el intento como correcto, actualiza el progreso (HE-07) y desbloquea la siguiente sección/contenido si aplica.
4. El sistema persiste el estado inmediatamente (sin acción explícita de "guardar").

**Flujo alternativo A1 — Intento incorrecto:**
1a. El sistema registra el intento como fallido y aumenta el contador de fallos **específico de esa flag**.
2a. Si el contador llega a 5 → el sistema desbloquea y muestra una pista.
3a. Si el contador llega a 15 (5 + 10 adicionales) → el sistema desbloquea y muestra el paso a paso.
4a. Pistas y pasos mostrados se mantienen visibles acumulativamente (no se ocultan al desbloquear el siguiente nivel).

**Flujo alternativo A2 — Reanudación tras caída del sistema:**
1b. El estudiante recarga o vuelve a ingresar tras una interrupción.
2b. El sistema recupera el último estado persistido (sección, contador de fallos, pistas desbloqueadas) sin pérdida de progreso (RNF-03.3).

**Excepciones:**
- E1: Envíos repetidos en menos de 1 segundo (posible scripting/fuerza bruta) → rate limiting específico sobre el endpoint de validación de flag.
- E2: Escritura concurrente desde dos pestañas del mismo usuario → el sistema aplica última escritura válida por timestamp, sin duplicar contadores de fallos.
- E3: Flag corrupta o sección eliminada tras la carga del estudiante → el sistema informa error y redirige al listado de secciones.

**Postcondiciones:** Progreso del estudiante actualizado y persistido; contador de fallos y pistas reflejan el estado real de sus intentos.

---

## UC-03 — Examen final de laboratorio
**HU relacionadas:** HE-09, HI-08
**Actores:** Estudiante, Instructor (variante personalizada)

**Precondiciones:** El estudiante completó todas las secciones del laboratorio.

**Flujo principal (laboratorio predeterminado):**
1. Al marcar la última sección como completada, el sistema habilita automáticamente el examen final.
2. El estudiante inicia el examen; el sistema presenta las preguntas definidas para ese laboratorio.
3. El estudiante responde y envía el examen.
4. El sistema califica automáticamente y registra el puntaje en el historial (HE-10).

**Flujo alternativo A1 — Laboratorio personalizado (con examen definido por instructor):**
1a. El instructor definió previamente las preguntas/criterios del examen al crear o copiar el laboratorio (HI-02/HI-03).
2a. El flujo del estudiante es idéntico al principal, pero las preguntas provienen de la configuración del instructor.

**Flujo alternativo A2 — Laboratorio personalizado sin examen configurado:**
1b. Si el instructor no definió examen, el sistema marca el laboratorio como "completado" directamente al finalizar secciones, sin bloquear al estudiante.

**Excepciones:**
- E1: El estudiante intenta acceder al examen sin haber completado todas las secciones → el sistema bloquea el acceso y muestra las secciones pendientes.
- E2: Pérdida de conexión durante el examen → el sistema autoguarda respuestas parciales; el estudiante puede continuar desde donde quedó (política de reintento pendiente de definir con negocio: intento único vs. reintentable).

**Postcondiciones:** Examen calificado y reflejado en el historial del estudiante; laboratorio marcado como completado.

---

## UC-04 — Creación de laboratorio personalizado
**HU relacionada:** HI-02
**Actor:** Instructor

**Precondiciones:** Usuario autenticado con rol Instructor.

**Flujo principal:**
1. El instructor inicia la creación de un nuevo laboratorio (nombre, descripción, nivel, temas).
2. El instructor agrega secciones en orden, con contenido teórico por sección.
3. El instructor define flags por sección práctica; el sistema cifra cada flag antes de almacenarla (RNF-01.5).
4. El instructor opcionalmente define un examen final (ver UC-03, A1).
5. El sistema guarda el laboratorio con estado `borrador`, propiedad del instructor, tipo `personalizado`.
6. El instructor publica el laboratorio (cambia estado a `publicado`), quedando disponible para asignación (UC-06).

**Flujo alternativo A1 — Edición posterior:**
1a. El instructor edita secciones/flags de un laboratorio ya publicado.
2a. El sistema versiona el cambio (para trazabilidad) sin afectar el progreso ya registrado de estudiantes en secciones no modificadas.

**Excepciones:**
- E1: Contenido con HTML/script potencialmente malicioso → el sistema sanitiza antes de almacenar y notifica si se removió contenido.
- E2: Intento de publicar sin al menos una flag por sección práctica → el sistema bloquea la publicación e indica las secciones incompletas.

**Postcondiciones:** Laboratorio personalizado disponible en el panel del instructor (HI-06), listo para asignar.

---

## UC-05 — Copia de laboratorio predeterminado
**HU relacionada:** HI-03
**Actor:** Instructor

**Precondiciones:** Existe al menos un laboratorio predeterminado publicado.

**Flujo principal:**
1. El instructor selecciona un laboratorio predeterminado del catálogo y elige "duplicar".
2. El sistema crea una copia completa (secciones, contenido, flags) marcada como `personalizado`, con campo `origen = predeterminado` y propietario = instructor.
3. El laboratorio predeterminado original permanece sin cambios y sigue siendo editable únicamente por Administrador (RF-31).
4. El instructor puede editar libremente su copia (ver UC-04, A1).

**Excepciones:**
- E1: El instructor intenta editar directamente el laboratorio predeterminado original (no una copia) → el sistema rechaza la operación con error 403 y sugiere duplicarlo.
- E2: Laboratorio predeterminado muy extenso (muchas secciones/flags) → duplicación asíncrona con notificación al finalizar, para no bloquear la UI.

**Postcondiciones:** Nueva copia editable en el panel del instructor, trazable a su origen predeterminado.

---

## UC-06 — Invitación y asignación de laboratorio con vencimiento
**HU relacionadas:** HI-07, HI-09
**Actores:** Instructor, Estudiante

**Precondiciones:** El instructor tiene un laboratorio propio (creado o copiado) publicado.

**Flujo principal:**
1. El instructor selecciona el laboratorio y elige estudiante(s) a invitar (por email o username).
2. El instructor define fecha/hora de vencimiento del acceso.
3. El sistema crea la invitación en estado `pendiente` y notifica al estudiante (UC-11).
4. El estudiante revisa la invitación y la **acepta**.
5. El sistema otorga acceso al laboratorio y comienza a contar el plazo hacia el vencimiento definido.
6. El estudiante accede y practica normalmente (UC-02).

**Flujo alternativo A1 — Rechazo de invitación:**
1a. El estudiante rechaza la invitación.
2a. El sistema marca la invitación como `rechazada` y no otorga acceso; notifica al instructor (opcional, según política de negocio).

**Flujo alternativo A2 — Vencimiento del acceso:**
1b. El sistema evalúa periódicamente (job programado) las asignaciones activas contra su fecha de vencimiento.
2b. Al cumplirse la fecha, el sistema revoca el acceso automáticamente (ver UC-07) y notifica al estudiante próximo a vencer (24h antes, HE-13).

**Excepciones:**
- E1: Invitación a un email no registrado en la plataforma → el sistema genera una invitación pendiente que se resuelve automáticamente si el usuario se registra con ese correo, o se define reenvío manual.
- E2: Instructor invita a un estudiante que ya tiene acceso vigente al mismo laboratorio → el sistema informa el estado actual sin duplicar la asignación.
- E3: Diferencia de zona horaria entre servidor y cliente al definir vencimiento → el sistema normaliza y almacena en UTC, mostrando conversión local en la UI.

**Postcondiciones:** Estudiante con acceso vigente y con fecha de expiración clara; instructor con visibilidad del estado de sus invitaciones (HI-04).

---

## UC-07 — Cierre automático de laboratorios vencidos
**HU relacionada:** RF-32
**Actor:** Sistema (proceso programado, sin actor humano)

**Precondiciones:** Existen asignaciones con fecha de vencimiento definida (UC-06).

**Flujo principal:**
1. Un job programado (Celery beat) se ejecuta periódicamente (ej. cada 15 minutos).
2. El sistema identifica asignaciones cuya fecha de vencimiento ya se cumplió y siguen `activas`.
3. El sistema revoca el acceso del estudiante a ese laboratorio (estado pasa a `vencido`).
4. El sistema registra el evento en el log de auditoría (UC-12).
5. El sistema notifica al estudiante que el acceso fue cerrado (HE-13).

**Excepciones:**
- E1: El estudiante tenía una sesión activa dentro del laboratorio en el momento del cierre → el sistema permite terminar la acción en curso (ej. envío de flag ya iniciado) antes de bloquear el siguiente acceso.
- E2: Fallo del job programado → reintento automático en la siguiente ejecución; alerta al monitoreo si falla repetidamente (HA-04).

**Postcondiciones:** Acceso revocado de forma consistente sin intervención manual; evento auditable.

---

## UC-08 — Gestión de usuarios por administrador
**HU relacionada:** HA-01
**Actor:** Administrador

**Precondiciones:** Usuario autenticado con rol Administrador.

**Flujo principal:**
1. El administrador busca un usuario (estudiante o instructor) por nombre/correo.
2. El administrador edita datos, cambia rol o deshabilita la cuenta.
3. El sistema aplica el cambio y registra la acción en auditoría (actor, acción, timestamp, IP) (UC-12).

**Flujo alternativo A1 — Deshabilitar usuario:**
1a. El sistema marca al usuario como `inactivo` (soft-delete); no elimina su histórico de progreso ni laboratorios creados.
2a. El usuario deshabilitado no puede iniciar sesión; recibe mensaje explicativo si lo intenta.

**Excepciones:**
- E1: El administrador intenta deshabilitarse o quitarse el rol de administrador a sí mismo → el sistema bloquea la operación (previene bloqueo total del sistema).
- E2: Cambio de rol de Instructor a Estudiante cuando tiene laboratorios propios activos con estudiantes asignados → el sistema advierte el impacto (laboratorios quedan huérfanos) y solicita confirmación explícita.

**Postcondiciones:** Estado del usuario actualizado; acción trazable en auditoría.

---

## UC-09 — Reporte y gestión de incidencias
**HU relacionadas:** HE-12, HA-05
**Actores:** Estudiante, Administrador

**Precondiciones:** El estudiante se encuentra dentro de un laboratorio con problema detectado.

**Flujo principal:**
1. El estudiante completa el formulario de reporte (descripción, sección afectada, adjunto opcional).
2. El sistema crea el reporte en estado `abierto` y notifica al administrador.
3. El administrador revisa el reporte, lo marca `en revisión` y toma acción correctiva.
4. El administrador cierra el reporte marcándolo `resuelto`.
5. El sistema notifica al estudiante que su reporte fue resuelto (HE-13).

**Flujo alternativo A1 — Reporte rechazado/no reproducible:**
1a. El administrador marca el reporte como `no reproducible` con comentario.
2a. El sistema notifica al estudiante con el motivo.

**Excepciones:**
- E1: Reporte sin descripción mínima (ej. <10 caracteres) → el sistema rechaza el envío y solicita más detalle (mitiga spam).
- E2: Múltiples reportes del mismo estudiante en corto periodo sobre el mismo laboratorio → el sistema los agrupa como posibles duplicados para revisión del administrador.

**Postcondiciones:** Reporte con ciclo de vida completo y trazable; estudiante informado del resultado.

---

## UC-10 — Editor visual de contenido (laboratorios predeterminados)
**HU relacionada:** HA-02
**Actor:** Administrador

**Precondiciones:** Usuario autenticado con rol Administrador.

**Flujo principal:**
1. El administrador crea o abre un laboratorio predeterminado en el editor WYSIWYG.
2. El administrador agrega/edita secciones con texto enriquecido, imágenes y bloques de código.
3. El administrador define flags por sección (el sistema las cifra antes de guardar, igual que en UC-04).
4. El administrador publica los cambios.

**Excepciones:**
- E1: HTML generado por el editor contiene scripts o atributos peligrosos → el sistema sanitiza automáticamente antes de persistir.
- E2: Un instructor intenta acceder a este editor sobre un laboratorio predeterminado → acceso denegado (reutiliza la regla de UC-05, E1).

**Postcondiciones:** Laboratorio predeterminado actualizado, disponible en catálogo público (HV-02) y para copia (UC-05).

---

## UC-11 — Sistema de notificaciones
**HU relacionada:** HE-13
**Actor:** Sistema (disparado por eventos de otros casos de uso)

**Disparadores:**
- Invitación creada (UC-06) → notifica al estudiante invitado.
- Vencimiento próximo, 24h antes (UC-06/UC-07) → notifica al estudiante.
- Reporte resuelto o rechazado (UC-09) → notifica al estudiante.

**Flujo principal:**
1. Un evento de negocio ocurre (ej. invitación creada).
2. El sistema encola la notificación (Celery + Redis) para no bloquear la operación que la origina.
3. El worker procesa la cola y entrega la notificación (in-app y/o email).
4. El estudiante visualiza la notificación en su panel; puede marcarla como leída.

**Excepciones:**
- E1: Falla el envío de correo (proveedor caído) → reintento con backoff exponencial; la notificación in-app se entrega igualmente.
- E2: Usuario con notificaciones deshabilitadas (si se habilita esa preferencia a futuro) → se registra el evento pero no se envía email, solo in-app.

**Postcondiciones:** Usuario informado del evento sin impacto en el rendimiento del flujo original.

---

## UC-12 — Auditoría y logging
**HU relacionada:** RF-33
**Actor:** Sistema (transversal); Administrador (consulta)

**Flujo principal (registro):**
1. Cualquier operación sensible ocurre (login, cambio de rol, CRUD de laboratorio, deshabilitación de usuario, acceso a flags).
2. El sistema registra automáticamente: actor, acción, entidad afectada, timestamp, IP.
3. El registro se almacena de forma append-only (no editable).

**Flujo principal (consulta):**
1. El administrador accede al panel de auditoría.
2. El administrador filtra por usuario, tipo de acción o rango de fechas.
3. El sistema retorna los registros paginados.

**Excepciones:**
- E1: Volumen alto de logs → rotación/archivado periódico sin pérdida de registros dentro del periodo de retención (≥6 meses).
- E2: Intento de acceso a auditoría por rol distinto de Administrador → acceso denegado.

**Postcondiciones:** Trazabilidad completa de operaciones sensibles, consultable por el administrador.
