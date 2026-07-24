# Sprint 1 — Punto 3d: RegisterView + manejo de errores estándar

## ¿Qué es esto?
El endpoint HTTP real (`POST /api/v1/auth/register/`) que expone `RegistrarUsuarioUseCase` al mundo exterior — el primer punto donde un frontend o Postman puede hablar con el backend para crear un usuario. Incluye también el manejador de errores global de toda la API.

## ¿Por qué es importante?
Hasta este punto, toda la lógica construida solo se podía probar desde el shell de Django o con `pytest` — no existía forma de que un usuario real (o un frontend) interactuara con ella. Este punto es la primera "puerta de entrada" real del sistema.

También se resolvió algo transversal a **toda** la API, no solo a este endpoint: cómo se traduce un error de negocio (ej. "email duplicado") al formato de error estándar ya definido en el documento de API, para que el frontend siempre reciba errores con la misma forma, sin importar qué endpoint los generó.

## ¿Qué se hizo?
- **`exception_handler.py`** (global, en `config/`): intercepta cualquier error de negocio o de validación en toda la API y lo traduce automáticamente al formato `{"error": {"code", "message", "details"}}` con el código HTTP correcto (400, 409, 422, etc.) — configurado una sola vez, aplica a todos los endpoints futuros sin que cada uno tenga que repetir esta lógica.
- **`RegistroRequestSerializer`**: valida la forma básica de los datos que llegan (tipos, campos requeridos) antes de que le lleguen al caso de uso.
- **`RegisterView`**: conecta el serializer con `RegistrarUsuarioUseCase` y devuelve la respuesta HTTP.
- **Ruta registrada**: `POST /api/v1/auth/register/`.

Se probó con 5 tests HTTP reales: registro exitoso (201), email duplicado (409), campo faltante (400), contraseña débil (400), y que el endpoint es público (no exige login).

## ¿Qué NO incluye?
- Login — con esto se puede crear un usuario, pero todavía no iniciar sesión (eso es el punto 8).
- Registro con Google/GitHub (OAuth) — pendiente, puntos 4-6.

## En una frase
Se abrió la primera puerta real de la API: cualquier cliente HTTP ya puede registrar un usuario nuevo, con errores devueltos siempre en el mismo formato estándar en toda la plataforma.
