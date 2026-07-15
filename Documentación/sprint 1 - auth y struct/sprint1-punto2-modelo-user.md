# Sprint 1 — Punto 2: Modelo User + ProveedorAutenticacion

## ¿Qué es esto?

Es la primera funcionalidad de negocio real del proyecto: la representación de un **Usuario** de PlatLAB (estudiante, instructor o administrador) y de sus **métodos de acceso** (email/contraseña, Google, GitHub), tanto a nivel de reglas de negocio como de tabla real en la base de datos.

## ¿Por qué es importante?

Todo el sistema gira alrededor de quién es cada usuario y qué puede hacer — sin esto, no se puede construir login, ni permisos, ni nada que dependa de "quién está usando la plataforma". Además, este punto es el primero donde se pone en práctica de punta a punta la arquitectura por capas que se preparó en el Sprint 0 (Domain / Infrastructure separados), con un caso real en vez de solo el kernel abstracto.

Un mismo usuario puede tener varios métodos de acceso a la vez (por ejemplo, se registró con contraseña pero después también vinculó su cuenta de Google) — por eso son dos conceptos separados: el Usuario en sí, y sus "Proveedores de Autenticación" asociados.

## ¿Qué se hizo exactamente?

### 1. Reglas de negocio puras (Domain) — `value_objects.py` y `entities.py`
Se definió, en código que no depende de Django ni de la base de datos:
- **`Rol`**: los 3 roles posibles del sistema (Estudiante, Instructor, Administrador).
- **`Email`**: un correo no es simplemente un texto cualquiera — se valida su formato en el momento en que se crea. Si alguien intenta construir un `Email` con un valor inválido, el sistema lo rechaza inmediatamente con un error claro, antes de que ese dato llegue a tocar la base de datos.
- **`User`**: la entidad completa del usuario (correo, nombre, rol, si está activo, cuándo se registró, etc.).
- **`ProveedorAutenticacion`**: el vínculo entre un usuario y un método de acceso (email, Google o GitHub).

Se probó que dos usuarios con el mismo `id` se consideran "el mismo usuario" aunque el resto de sus datos varíe (regla ya definida en el kernel del Sprint 0), y que un correo mal formado se rechaza automáticamente.

### 2. Tablas reales en PostgreSQL (Infrastructure) — `models.py`
Se crearon los modelos de Django que Django traduce automáticamente en tablas SQL:
- **`users_user`**: guarda cada usuario, con restricciones a nivel de base de datos (no dos usuarios pueden tener el mismo correo o el mismo username).
- **`users_proveedorautenticacion`**: guarda cada método de acceso vinculado, con dos restricciones importantes:
  - Un usuario no puede vincular el mismo proveedor (ej. Google) dos veces.
  - Un mismo UID de Google/GitHub no puede vincularse a dos cuentas distintas (previene que dos usuarios "compartan" el mismo login social por error o abuso).

### 3. Migración aplicada
Se generó y aplicó la migración (`0001_initial.py`), que es el archivo que le dice a PostgreSQL exactamente qué tablas y restricciones crear. Se verificó en el entorno real que las tablas quedaron creadas correctamente, insertando y consultando un usuario de prueba.

## ¿Qué NO incluye este punto?

- Ningún endpoint HTTP todavía (no se puede registrar un usuario desde el navegador o Postman aún) — eso son los puntos 3 y 6.
- Contraseñas reales hasheadas de forma segura — el campo existe (`password_hash`) pero el proceso de hashear con bcrypt/argon2 se implementa en el caso de uso de registro (punto 3).
- Login, JWT, OAuth real — son los puntos siguientes del sprint.

## En una frase

Se construyó la base de datos real de usuarios de PlatLAB (con sus reglas de validación y sus restricciones de integridad), separando claramente "qué es un usuario" (reglas de negocio) de "cómo se guarda en la base de datos" (detalle técnico) — la primera pieza concreta sobre la que se construye todo el módulo de Autenticación.
