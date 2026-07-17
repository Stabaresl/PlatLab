# Historias de Usuario, RF y RNF — PlatLAB

> Documento maestro y definitivo. Consolida el backlog del equipo con Prioridad, Sprint y criterios de aceptación expandidos para cada Historia de Usuario. Versión 2.0 — Inconsistencias corregidas.

---

## 1. Historias de Usuario

### 👤 Visitante (No autenticado)

#### HV-01 — Landing page
**Como** visitante, **quiero** ver una landing page con bienvenida, login y registro, **para** conocer el propósito de la plataforma antes de decidir registrarme.

- **Prioridad:** Alta | **Sprint:** 1
- **Criterios de aceptación:**
  - Página pública accesible sin autenticación.
  - Incluye propuesta de valor, CTA de login y CTA de registro.
  - Responsiva (RNF-05.1); carga < 3s (RNF-02.1).
- **Dependencias:** Ninguna
- **Riesgos:** Contenido genérico con baja conversión a registro.

#### HV-02 — Catálogo público
**Como** visitante, **quiero** ver el catálogo completo de laboratorios con filtros por dificultad y tema, **para** explorar lo disponible antes de registrarme.

- **Prioridad:** Alta | **Sprint:** 2
- **Criterios de aceptación:**
  - Lista todos los laboratorios predeterminados publicados.
  - Filtros combinables por dificultad y tema; paginado.
  - No muestra laboratorios en estado borrador.
- **Dependencias:** HV-01, RF-05
- **Riesgos:** Exponer demasiado detalle reduce incentivo a registrarse.

#### HV-03 — Detalle y TOC público
**Como** visitante, **quiero** ver la descripción y la tabla de contenido de cualquier laboratorio, **para** evaluar si me interesa antes de registrarme.

- **Prioridad:** Alta | **Sprint:** 2
- **Criterios de aceptación:**
  - Muestra descripción, nivel, temas y TOC (solo títulos de sección).
  - **No** expone contenido teórico ni práctico (flags); intento de acceso redirige a registro.
  - El bloqueo se valida en backend, no solo en frontend.
- **Dependencias:** HV-02
- **Riesgos:** Fuga de contenido si la restricción solo se aplica en la UI.

#### HV-04 — Registro
**Como** visitante, **quiero** registrarme con correo electrónico, Google o GitHub, **para** acceder al contenido completo de los laboratorios.

- **Prioridad:** Alta | **Sprint:** 1
- **Criterios de aceptación:**
  - Registro con email valida unicidad y política de contraseña.
  - OAuth Google/GitHub crea o vincula cuenta según email verificado.
  - Rol asignado por defecto: Estudiante.
- **Dependencias:** Ninguna
- **Riesgos:** Colisión de cuentas si el email de OAuth coincide con una cuenta existente por password (definir estrategia de vinculación).

#### HV-05 — Recuperación de contraseña
**Como** visitante, **quiero** recuperar mi contraseña olvidada mediante un enlace enviado a mi correo, **para** poder acceder a mi cuenta si olvido mis credenciales.

- **Prioridad:** Alta | **Sprint:** 1
- **Criterios de aceptación:**
  - Formulario "olvidé mi contraseña" solicita el email registrado.
  - Envía un enlace de recuperación válido por 15 minutos.
  - El enlace permite establecer una nueva contraseña.
  - Aplica rate limiting (RNF-01.4) para evitar abusos.
- **Dependencias:** HV-04
- **Riesgos:** Enlaces de recuperación interceptados (requiere HTTPS, RNF-01.3).

---

### 🎓 Estudiante

#### HE-01 — Dashboard de progreso
**Como** estudiante, **quiero** un dashboard con mi progreso general y los laboratorios en los que estoy inscrito, **para** saber por dónde retomar.

- **Prioridad:** Alta | **Sprint:** 5
- **Criterios de aceptación:**
  - Muestra % de progreso global y estado de labs en curso.
  - Acceso directo a "continuar" cada laboratorio.
- **Dependencias:** HE-07, HI-09
- **Riesgos:** Cálculo inconsistente si un laboratorio inscrito es eliminado o despublicado.

#### HE-02 — Buscar y filtrar laboratorios
**Como** estudiante, **quiero** buscar y filtrar laboratorios por dificultad (básico, intermedio, avanzado) y por tema, **para** encontrar los que me interesan.

- **Prioridad:** Alta | **Sprint:** 2
- **Criterios de aceptación:**
  - Igual a HV-02, autenticado, mostrando estado de inscripción por card.
- **Dependencias:** HV-02
- **Riesgos:** —

#### HE-03 — Navegación por secciones
**Como** estudiante, **quiero** entrar a un laboratorio y ver sus secciones organizadas, **para** navegar entre teoría y práctica ordenadamente.

- **Prioridad:** Alta | **Sprint:** 3
- **Criterios de aceptación:**
  - Secciones en el orden definido por el laboratorio, de navegación **secuencial obligatoria**: no se puede saltar a una sección sin haber completado la anterior.
  - Indicador visual por sección: completada / pendiente / bloqueada.
- **Dependencias:** HE-02
- **Riesgos:** —

#### HE-04 — Contenido teórico
**Como** estudiante, **quiero** leer el contenido teórico de cada sección, **para** aprender los conceptos antes de ponerlos a prueba.

- **Prioridad:** Alta | **Sprint:** 3
- **Criterios de aceptación:**
  - Renderiza contenido enriquecido de la sección.
  - Marca la sección como "vista" al abrirla.
- **Dependencias:** HE-03
- **Riesgos:** Contenido con imágenes pesadas afecta el tiempo de carga (RNF-02.1).

#### HE-05 — Validación de flags
**Como** estudiante, **quiero** escribir flags en un campo y enviarlas para validación automática, **para** demostrar que completé correctamente cada práctica.

- **Prioridad:** Alta | **Sprint:** 3
- **Criterios de aceptación:**
  - Campo de texto por sección práctica.
  - Validación server-side contra hash de la flag (RNF-01.5); nunca se expone la flag real.
  - Responde en < 1s (RNF-02.3).
  - Registra cada intento (correcto/incorrecto) para alimentar HE-06.
- **Dependencias:** HE-04
- **Riesgos:** Fuerza bruta sobre el campo de flag (requiere rate limiting específico, extensión de RNF-01.4).

#### HE-06 — Pistas progresivas
**Como** estudiante, **quiero** recibir una pista si fallo una flag más de 5 veces, y el paso a paso si fallo 10 veces más, **para** no quedarme trabado.

- **Prioridad:** Media | **Sprint:** 3
- **Criterios de aceptación:**
  - Contador de fallos por flag (se resetea por flag, no por sección).
  - 5 fallos → pista; 15 fallos totales (5+10) → paso a paso.
  - Pistas y pasos se muestran acumulativamente, no se ocultan entre sí.
- **Dependencias:** HE-05
- **Riesgos:** Estudiantes "farmeando" fallos intencionalmente para desbloquear la solución (aceptado como diseño pedagógico).

#### HE-07 — Progreso automático
**Como** estudiante, **quiero** que mi progreso se guarde automáticamente, **para** retomar el laboratorio donde lo dejé al volver.

- **Prioridad:** Alta | **Sprint:** 3
- **Criterios de aceptación:**
  - Toda acción relevante (sección vista, flag resuelta) persiste sin acción explícita de "guardar".
  - Recuperable tras cierre de sesión o caída del sistema (RNF-03.3).
- **Dependencias:** HE-04, HE-05
- **Riesgos:** Escrituras concurrentes si el estudiante tiene múltiples pestañas abiertas.

#### HE-08 — Tabla de contenido navegable
**Como** estudiante, **quiero** una tabla de contenido en cada laboratorio, **para** saltar directamente a la sección que quiero repasar.

- **Prioridad:** Media | **Sprint:** 3
- **Criterios de aceptación:**
  - Lista de secciones con salto directo y estado (vista/pendiente/completada).
- **Dependencias:** HE-03
- **Riesgos:** —

#### HE-09 — Examen final (laboratorio predeterminado)
**Como** estudiante, **quiero** presentar un examen final al completar todas las secciones de un laboratorio, **para** validar mis conocimientos.

- **Prioridad:** Media | **Sprint:** 5
- **Criterios de aceptación:**
  - Se habilita solo cuando todas las secciones están completadas.
  - Evalúa el laboratorio completo, no repite literalmente flags ya resueltas.
  - Calificación queda registrada en el historial (HE-10).
- **Dependencias:** HE-07
- **Riesgos:** Definir política de reintento (intento único vs. reintentable).

#### HE-10 — Historial de laboratorios
**Como** estudiante, **quiero** ver mi historial de laboratorios completados con puntajes, **para** medir mi avance a largo plazo.

- **Prioridad:** Media | **Sprint:** 5
- **Criterios de aceptación:**
  - Lista labs completados, fecha, puntaje, tiempo invertido; ordenable/filtrable.
  - Incluye tanto labs predeterminados como personalizados asignados.
- **Dependencias:** HE-07, HE-09, HI-08
- **Riesgos:** —

#### HE-11 — Repetir contenido
**Como** estudiante, **quiero** repetir cualquier laboratorio o sección ya completada, **para** repasar cuando lo necesite.

- **Prioridad:** Baja | **Sprint:** 5
- **Criterios de aceptación:**
  - El reintento no sobrescribe el puntaje histórico original (o se define política de "mejor puntaje").
- **Dependencias:** HE-07
- **Riesgos:** Ambigüedad sobre si el repaso cuenta para las métricas del instructor.

#### HE-12 — Reporte de problemas
**Como** estudiante, **quiero** reportar un problema técnico en un laboratorio, **para** que el administrador lo revise.

- **Prioridad:** Media | **Sprint:** 5
- **Criterios de aceptación:**
  - Formulario con descripción, sección afectada y adjunto opcional.
  - Notifica al administrador (RF-18).
  - Estudiante puede ver el estado de su reporte (abierto/resuelto).
- **Dependencias:** HE-03
- **Riesgos:** Spam de reportes sin validación mínima de contenido.

#### HE-13 — Notificaciones
**Como** estudiante, **quiero** recibir notificaciones cuando me inviten a un laboratorio, cuando esté por vencer o cuando resuelvan mi reporte, **para** estar al tanto de mi actividad en la plataforma.

- **Prioridad:** Media | **Sprint:** 5
- **Criterios de aceptación:**
  - Notificación in-app y/o email según el evento.
  - Aviso de vencimiento configurable (ej. 24h antes).
  - Entrega asíncrona, no bloquea el flujo que la origina.
- **Dependencias:** HI-07, HI-09, HE-12
- **Riesgos:** Requiere cola de mensajería (Celery + Redis) para no bloquear requests.

---

### 👨‍🏫 Instructor

#### HI-01 — Ver catálogo completo
**Como** instructor, **quiero** ver los laboratorios predeterminados del catálogo general y mis propios laboratorios, **para** conocer todo el material disponible.

- **Prioridad:** Media | **Sprint:** 4
- **Criterios de aceptación:**
  - Muestra laboratorios predeterminados publicados + laboratorios propios (incluyendo borradores).
  - No muestra laboratorios de otros instructores.
- **Dependencias:** HV-02
- **Riesgos:** —

#### HI-02 — Crear laboratorios propios
**Como** instructor, **quiero** crear mis propios laboratorios con secciones, contenido y flags, **para** diseñar material personalizado para mis estudiantes.

- **Prioridad:** Alta | **Sprint:** 4
- **Criterios de aceptación:**
  - CRUD de laboratorio con secciones, contenido teórico y flags asociadas.
  - Flags almacenadas cifradas (RNF-01.5).
  - El lab creado queda marcado como "personalizado", propiedad del instructor.
- **Dependencias:** RF-04 (rol Instructor)
- **Riesgos:** Validación de contenido malicioso/XSS en el editor de texto enriquecido.

#### HI-03 — Copiar laboratorio predeterminado
**Como** instructor, **quiero** hacer una "copia" de un laboratorio predeterminado, **para** asignarlo a mis estudiantes sin modificar el original.

- **Prioridad:** Alta | **Sprint:** 4
- **Criterios de aceptación:**
  - Acción "duplicar" crea una copia editable vinculada al instructor.
  - El laboratorio predeterminado original permanece inalterado (RF-31).
  - La copia queda marcada como "personalizado, origen: predeterminado".
- **Dependencias:** HI-01, HI-02
- **Riesgos:** Impacto en almacenamiento por duplicación de contenido/flags.

#### HI-04 — Filtrar estudiantes
**Como** instructor, **quiero** filtrar estudiantes por nombre, avance o laboratorio, **para** dar seguimiento personalizado.

- **Prioridad:** Media | **Sprint:** 4
- **Criterios de aceptación:**
  - Filtros combinables; solo estudiantes con labs asignados por ese instructor.
- **Dependencias:** HI-09
- **Riesgos:** —

#### HI-05 — Filtrar mis laboratorios
**Como** instructor, **quiero** filtrar mis laboratorios por nombre, fecha o dificultad, **para** organizarme.

- **Prioridad:** Baja | **Sprint:** 4
- **Criterios de aceptación:**
  - Filtros combinables sobre labs propios (creados o copiados).
- **Dependencias:** HI-02, HI-03
- **Riesgos:** —

#### HI-06 — Panel principal
**Como** instructor, **quiero** ver en mi página principal todos los laboratorios que tengo asociados, **para** tener un panel de control rápido.

- **Prioridad:** Alta | **Sprint:** 4
- **Criterios de aceptación:**
  - Lista labs propios con métricas rápidas: estudiantes inscritos, % completitud promedio.
- **Dependencias:** HI-02, HI-07, HI-09
- **Riesgos:** —

#### HI-07 — Asignación con límite de tiempo
**Como** instructor, **quiero** asignar un laboratorio a estudiantes con o sin límite de tiempo, **para** controlar el acceso y que se cierre automáticamente al vencer si lo definí.

- **Prioridad:** Media | **Sprint:** 5
- **Criterios de aceptación:**
  - El instructor elige si la asignación tiene o no vencimiento.
  - Si tiene vencimiento: define fecha/hora; tras vencer, el acceso se bloquea automáticamente (RF-32).
  - El instructor puede agregar, modificar o quitar el vencimiento después de asignado.
  - El estudiante ve el tiempo restante si hay vencimiento definido.
- **Dependencias:** HI-09
- **Riesgos:** Inconsistencias de zona horaria entre servidor y cliente.

#### HI-08 — Examen final personalizado
**Como** instructor, **quiero** crear un examen final para mis laboratorios personalizados, **para** evaluar a mis estudiantes al completarlos.

- **Prioridad:** Media | **Sprint:** 5
- **Criterios de aceptación:**
  - El examen es de **opción múltiple**, con un mínimo de **1 pregunta** y un máximo de **15 preguntas**.
  - Por cada pregunta define las opciones y marca la respuesta correcta.
  - Se presenta al estudiante al completar las secciones del laboratorio personalizado.
  - El sistema califica automáticamente comparando las respuestas contra las correctas definidas.
- **Dependencias:** HI-02
- **Riesgos:** —

#### HI-09 — Invitación a laboratorio
**Como** instructor, **quiero** invitar estudiantes a mis laboratorios asignados, **para** que puedan aceptar o rechazar el acceso al contenido.

- **Prioridad:** Alta | **Sprint:** 4
- **Criterios de aceptación:**
  - Invitación enviada por email o username.
  - Solo tras aceptar, el estudiante obtiene acceso.
  - Notifica al estudiante (HE-13).
- **Dependencias:** HI-02, HI-03
- **Riesgos:** Invitaciones a emails no registrados (definir flujo: pre-registro o invitación pendiente).

---

### 🔧 Administrador

#### HA-01 — CRUD de usuarios
**Como** administrador, **quiero** un CRUD completo de usuarios (estudiantes e instructores), **para** gestionar quién tiene acceso a la plataforma.

- **Prioridad:** Alta | **Sprint:** 4
- **Criterios de aceptación:**
  - Crear, editar, ver, deshabilitar y cambiar rol (RF-26).
  - Deshabilitar no elimina el histórico de progreso.
  - Cada acción queda auditada (RF-33).
- **Dependencias:** RF-04
- **Riesgos:** Auto-deshabilitación accidental de la propia cuenta de administrador (debe bloquearse).

#### HA-02 — Editor visual de contenido
**Como** administrador, **quiero** una interfaz visual para crear contenido de laboratorios (tipo editor WYSIWYG o similar), **para** publicar material sin escribir código.

- **Prioridad:** Media | **Sprint:** 5
- **Criterios de aceptación:**
  - Editor tipo procesador de texto (RNF-05.3), sin necesidad de código.
  - Soporta texto enriquecido, imágenes y bloques de código.
  - Permite crear/editar secciones, contenido y flags de laboratorios predeterminados.
- **Dependencias:** HI-02 (reutiliza el modelo de laboratorio)
- **Riesgos:** Sanitización del HTML generado (XSS).

#### HA-03 — Dashboard de usuarios
**Como** administrador, **quiero** un dashboard de usuarios registrados, **para** ver métricas de la plataforma.

- **Prioridad:** Media | **Sprint:** 5
- **Criterios de aceptación:**
  - Totales por rol, labs activos, labs más populares, tasa de completitud (RF-28).
- **Dependencias:** HA-01, HI-02
- **Riesgos:** —

#### HA-04 — Dashboard de rendimiento
**Como** administrador, **quiero** un dashboard de rendimiento de la aplicación, **para** monitorear su estado.

- **Prioridad:** Baja | **Sprint:** 9
- **Criterios de aceptación:**
  - Tiempos de respuesta, uptime y tasa de errores (RF-29).
  - Alineado con pruebas de carga Locust (RNF-02.4).
- **Dependencias:** RF-33 (logging)
- **Riesgos:** Requiere instrumentación (APM) adicional al backend.

#### HA-06 — Crear laboratorio predeterminado
**Como** administrador, **quiero** crear laboratorios predeterminados desde cero con secciones, contenido teórico, flags y examen, **para** publicar material base en el catálogo general.

- **Prioridad:** Alta | **Sprint:** 5
- **Criterios de aceptación:**
  - CRUD completo del laboratorio usando el editor visual (HA-02).
  - El laboratorio creado queda marcado como "predeterminado".
  - Solo el administrador y el equipo de contenidos pueden editarlo (RF-31).
  - Los instructores pueden copiarlo (HI-03) pero no modificarlo.
- **Dependencias:** HA-02
- **Riesgos:** —


#### HA-05 — Gestión de reportes
**Como** administrador, **quiero** ver los reportes de problemas enviados por estudiantes, **para** gestionar y resolver incidentes.

- **Prioridad:** Media | **Sprint:** 5
- **Criterios de aceptación:**
  - Lista reportes con estado (abierto/en revisión/resuelto).
  - Cambiar estado dispara notificación al estudiante (HE-13).
- **Dependencias:** HE-12
- **Riesgos:** —

---

## 2. Requisitos Funcionales (RF)

| ID | Requerimiento | Descripción | Actor relacionado |
|---|---|---|---|
| RF-01 | Registro de usuarios | El sistema debe permitir el registro de usuarios mediante correo electrónico, Google OAuth y GitHub OAuth. | Visitante |
| RF-02 | Inicio de sesión | El sistema debe autenticar usuarios registrados y redirigirlos según su rol (estudiante, instructor, administrador). | Visitante, Estudiante, Instructor, Admin |
| RF-03 | Recuperación de contraseña | El sistema debe permitir la recuperación de contraseña mediante el envío de un enlace al correo registrado. | Estudiante, Instructor, Admin |
| RF-04 | Roles y permisos | El sistema debe gestionar tres roles: estudiante, instructor y administrador, cada uno con permisos específicos. | Sistema |
| RF-05 | Catálogo público de laboratorios | El sistema debe mostrar un catálogo de laboratorios accesible sin autenticación, con nombre, descripción, nivel, temas y tabla de contenido. | Visitante |
| RF-06 | Filtros de catálogo | El sistema debe permitir filtrar laboratorios por dificultad y por tema. | Visitante, Estudiante |
| RF-07 | Dashboard del estudiante | El sistema debe mostrar al estudiante un dashboard con su progreso general y los laboratorios en los que está inscrito. | Estudiante |
| RF-08 | Visualización de laboratorio | El sistema debe mostrar las secciones de un laboratorio con contenido teórico y práctico, organizadas en orden y con TOC navegable. | Estudiante |
| RF-09 | Validación de flags | El sistema debe permitir al estudiante escribir una flag y validarla automáticamente contra la respuesta correcta. | Estudiante |
| RF-10 | Sistema de pistas progresivas | El sistema debe mostrar una pista tras 5 intentos fallidos, y el paso a paso tras 10 intentos fallidos adicionales (15 totales). | Estudiante |
| RF-11 | Persistencia de progreso | El sistema debe guardar automáticamente el progreso del estudiante (secciones visitadas, flags resueltas, puntajes). | Estudiante |
| RF-12 | Retomar laboratorio | El sistema debe permitir retomar un laboratorio desde la última sección no completada. | Estudiante |
| RF-13 | Repetir contenido | El sistema debe permitir repetir cualquier laboratorio o sección ya completada. | Estudiante |
| RF-14 | Examen final (predeterminado) | El sistema debe presentar un examen final al completar todas las secciones de un laboratorio predeterminado. | Estudiante |
| RF-15 | Examen final (personalizado) | El sistema debe permitir al instructor crear un examen final para sus laboratorios personalizados. | Instructor, Estudiante |
| RF-16 | Notificaciones al estudiante | El sistema debe notificar invitaciones, vencimientos próximos y resolución de reportes. | Estudiante |
| RF-17 | Historial de laboratorios | El sistema debe mostrar el historial de laboratorios completados con puntajes. | Estudiante |
| RF-18 | Reporte de problemas | El sistema debe permitir reportar un problema técnico y notificar al administrador. | Estudiante, Admin |
| RF-19 | CRUD de laboratorios (instructor) | El sistema debe permitir crear, editar y eliminar laboratorios propios con secciones, contenido, flags y exámenes. | Instructor |
| RF-20 | Copia de laboratorio predeterminado | El sistema debe permitir duplicar un laboratorio predeterminado sin modificar el original. | Instructor |
| RF-21 | Filtros de estudiantes (instructor) | El sistema debe permitir filtrar estudiantes por nombre, avance o laboratorio asignado. | Instructor |
| RF-22 | Filtros de laboratorios (instructor) | El sistema debe permitir filtrar laboratorios propios por nombre, fecha o dificultad. | Instructor |
| RF-23 | Panel principal del instructor | El sistema debe mostrar todos los laboratorios asociados al instructor en su página principal. | Instructor |
| RF-24 | Asignación con límite de tiempo (opcional) | El sistema debe permitir al instructor asignar un laboratorio con o sin fecha de vencimiento, y modificar ese vencimiento después de asignado. Al cumplirse la fecha, el acceso se bloquea. | Instructor, Estudiante |
| RF-25 | Invitación a laboratorio | El sistema debe enviar invitación al estudiante y requerir su aceptación para acceder. | Instructor, Estudiante |
| RF-26 | CRUD de usuarios (admin) | El sistema debe permitir crear, editar, visualizar, deshabilitar y cambiar el rol de usuarios. | Admin |
| RF-27 | Editor de contenido visual | El sistema debe proveer una interfaz WYSIWYG para crear/editar contenido de laboratorios. | Admin |
| RF-28 | Dashboard de métricas (admin) | El sistema debe mostrar usuarios registrados, laboratorios activos, más populares y tasas de completitud. | Admin |
| RF-29 | Dashboard de rendimiento (admin) | El sistema debe mostrar métricas de rendimiento (tiempos de respuesta, uptime, errores). | Admin |
| RF-30 | Gestión de reportes (admin) | El sistema debe permitir ver, gestionar y cerrar reportes de problemas. | Admin |
| RF-31 | Roles en contenido predeterminado | El sistema debe proteger los laboratorios predeterminados contra edición por instructores. | Admin, Instructor |
| RF-32 | Cierre automático de laboratorios vencidos | El sistema debe desactivar automáticamente el acceso al cumplirse la fecha de vencimiento. | Sistema |
| RF-33 | Sistema de logging y auditoría | El sistema debe registrar operaciones sensibles y permitir su consulta por el administrador. | Admin, Sistema |

---

## 3. Requisitos No Funcionales (RNF)

### RNF-01 Seguridad (Crítico)
| ID | Requerimiento |
|---|---|
| RNF-01.1 | Protección contra OWASP Top 10: SQLi, XSS (reflejado, almacenado, DOM-based), CSRF, clickjacking. |
| RNF-01.2 | Contraseñas con hash seguro (bcrypt o Argon2). |
| RNF-01.3 | HTTPS en todos los endpoints. |
| RNF-01.4 | Rate limiting en endpoints de autenticación. |
| RNF-01.5 | Flags cifradas en BD, nunca expuestas en respuestas de la API. |
| RNF-01.6 | Entornos de laboratorio aislados de la red interna. |
| RNF-01.7 | Validación de entrada cliente y servidor. |
| RNF-01.8 | Logging de accesos y operaciones sensibles. |
| RNF-01.9 | Rate limiting específico en el endpoint de validación de flags: máx. 30 intentos/minuto por usuario y 10 intentos/minuto por flag; responder HTTP 429 al exceder. |

### RNF-02 Rendimiento
| ID | Requerimiento |
|---|---|
| RNF-02.1 | Carga de página ≤ 3s en condiciones normales. |
| RNF-02.2 | Soportar ≥100 usuarios concurrentes sin degradación (release 1.0). |
| RNF-02.3 | Validación de flag responde en <1s. |
| RNF-02.4 | Pruebas de carga (Locust) sobre funcionalidades críticas antes de cada release mayor. |

### RNF-03 Disponibilidad
| ID | Requerimiento |
|---|---|
| RNF-03.1 | Disponibilidad ≥99.5% en horario académico (7:00–22:00). |
| RNF-03.2 | Backup automático diario de la base de datos. |
| RNF-03.3 | Reanudación sin pérdida de progreso tras caída del sistema. |

### RNF-04 Escalabilidad
| ID | Requerimiento |
|---|---|
| RNF-04.1 | Backend con escalamiento horizontal (balanceador de carga). |
| RNF-04.2 | Orquestación Docker desacoplada del backend principal. |
| RNF-04.3 | BD soporta 10,000 usuarios y 500 laboratorios sin degradación. |

### RNF-05 Usabilidad
| ID | Requerimiento |
|---|---|
| RNF-05.1 | Interfaz responsiva en navegadores modernos (últimas 2 versiones). |
| RNF-05.2 | Navegable sin capacitación previa para estudiantes/instructores. |
| RNF-05.3 | Editor de administrador intuitivo, similar a procesador de texto. |
| RNF-05.4 | Mensajes de error descriptivos y orientados a la acción. |

### RNF-06 Mantenibilidad
| ID | Requerimiento |
|---|---|
| RNF-06.1 | Backend en patrón MVT de Django, separación clara de capas. |
| RNF-06.2 | API REST documentada con OpenAPI/Swagger. |
| RNF-06.3 | Cobertura de pruebas unitarias ≥80% (release 1.0). |
| RNF-06.4 | Migraciones de BD para todos los cambios de esquema. |

### RNF-07 Privacidad y Cumplimiento
| ID | Requerimiento |
|---|---|
| RNF-07.1 | Cumplimiento de la Ley 1581 de 2012 (Colombia). |
| RNF-07.2 | Consentimiento explícito en laboratorios de ingeniería social. |
| RNF-07.3 | No almacenar información sensible de estudiantes en texto plano. |

### RNF-08 Compatibilidad e Integración
| ID | Requerimiento |
|---|---|
| RNF-08.1 | Integración con Docker/Docker Compose para orquestación de laboratorios. |
| RNF-08.2 | API REST expuesta para consumo del frontend React. |
| RNF-08.3 | OAuth con Google y GitHub como proveedores iniciales. |

---

## 4. Trazabilidad HU ↔ RF

| Historia | RF relacionado |
|---|---|
| HV-01, HV-04, HV-05 | RF-01, RF-02, RF-03 |
| HV-02, HV-03 | RF-05, RF-06 |
| HE-01 | RF-07 |
| HE-02 | RF-06 |
| HE-03, HE-04, HE-08 | RF-08 |
| HE-05 | RF-09 |
| HE-06 | RF-10, RF-11 |
| HE-07, HE-11 | RF-11, RF-12, RF-13 |
| HE-09 | RF-14 |
| HE-10 | RF-17 |
| HE-12 | RF-18 |
| HE-13 | RF-16 |
| HI-01, HI-02 | RF-19 |
| HI-03 | RF-20 |
| HI-04 | RF-21 |
| HI-05 | RF-22 |
| HI-06 | RF-23 |
| HI-07 | RF-24, RF-32 |
| HI-08 | RF-15 |
| HI-09 | RF-25 |
| HA-01 | RF-26, RF-33 |
| HA-02 | RF-27 |
| HA-03 | RF-28 |
| HA-04 | RF-29 |
| HA-05 | RF-30 |
| HA-06 | RF-27, RF-31 |

---

## 5. Resumen

| Tipo | Cantidad |
|---|---|
| Historias de usuario | 33 |  <!-- + HV-05 + HA-06 -->
| Requisitos funcionales (RF) | 33 |
| Requisitos no funcionales (RNF) | 26 |

**Stack confirmado:**
- **Backend:** Django + DRF, PostgreSQL, Celery + Redis
- **Autenticación:** SimpleJWT + django-allauth (OAuth Google/GitHub)
- **Auditoría:** django-simple-history
- **Documentación API:** drf-spectacular (OpenAPI/Swagger)
- **Testing:** pytest-django
- **Frontend:** React
- **Contenedores:** Docker / Docker Compose
