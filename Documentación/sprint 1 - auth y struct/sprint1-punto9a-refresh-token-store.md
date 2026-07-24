# Sprint 1 — Punto 9a: RefreshTokenStore

## ¿Qué es esto?
El componente que guarda en Redis el "historial" de cada sesión de login, permitiendo renovar el token de acceso sin pedir la contraseña de nuevo, y detectando automáticamente si un token fue robado y reusado.

## ¿Por qué es importante?
El token de acceso dura solo 15 minutos (punto 8a) — a propósito, para que si alguien lo roba, el daño esté limitado en el tiempo. Pero no se puede pedir al usuario que ponga su contraseña cada 15 minutos, así que existe el token de refresco (7 días) para renovarlo automáticamente.

El riesgo de un token de larga duración es que, si se roba, sirve por mucho tiempo. La solución estándar (definida en el documento de Seguridad) es la **rotación con detección de reuso**: cada vez que se usa un refresh token para renovar, ese token queda "quemado" y se entrega uno nuevo. Si alguien intenta usar un token ya quemado (por ejemplo, un atacante que robó una copia vieja mientras el usuario legítimo ya rotó el suyo), el sistema lo detecta inmediatamente y cancela **toda la sesión**, forzando a ambos (usuario legítimo y atacante) a iniciar sesión de nuevo — así el robo se neutraliza en el momento en que se intenta usar.

## ¿Qué se hizo?
Se construyó `RefreshTokenStore`, que guarda en Redis (con expiración automática a los 7 días, igual que el token):
- Qué token es el válido "ahora" para cada sesión (familia de tokens).
- A qué sesión pertenece cada token.
- Qué sesiones activas tiene cada usuario (para poder cerrarlas todas de una vez más adelante, en "cerrar sesión en todos los dispositivos").

Con esto, se pueden hacer 3 operaciones: registrar una sesión nueva al hacer login, rotar un token válido por uno nuevo, y revocar todas las sesiones de un usuario.

Se probó con 7 tests: registro de sesión, rotación exitosa, rotación encadenada (rotar dos veces seguidas), detección de reuso de un token ya rotado, que la detección de reuso invalida toda la sesión (no solo el token robado), rechazo de un token que nunca existió, y revocación de todas las sesiones de un usuario.

## ¿Qué NO incluye?
- Todavía no está conectado a `LoginUseCase` ni a ningún endpoint — es la pieza de bajo nivel. La conexión real (`RefreshTokenUseCase` + endpoint) es el siguiente paso.

## En una frase
Se construyó y probó el mecanismo de seguridad que permite mantener sesiones largas sin pedir la contraseña constantemente, mientras detecta y neutraliza automáticamente el robo de tokens de sesión.
