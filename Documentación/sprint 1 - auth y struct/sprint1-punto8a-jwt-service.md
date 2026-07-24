# Sprint 1 — Punto 8a: JWTService

## ¿Qué es esto?
El componente que genera y valida los tokens JWT (JSON Web Token) — el mecanismo que usa PlatLAB para reconocer "quién eres" en cada petición, sin tener que consultar la base de datos en cada una.

## ¿Por qué es importante?
PlatLAB no usa sesiones tradicionales (donde el servidor recuerda quién está conectado); usa JWT: al iniciar sesión, el servidor entrega un "carnet digital" firmado que el cliente (frontend) reenvía en cada petición. El servidor puede verificar que ese carnet es auténtico (no fue falsificado) sin tener que buscar nada en la base de datos, lo cual es rápido y escalable.

Se necesitan **dos** tokens: uno de **acceso** (corta duración, 15 minutos — se usa en cada petición) y uno de **refresco** (larga duración, 7 días — sirve únicamente para pedir un nuevo token de acceso sin tener que volver a poner la contraseña).

## ¿Qué se hizo?
- Se instaló `djangorestframework-simplejwt`, la librería estándar de JWT para Django, y se configuraron sus tiempos de vida exactamente como los definió el documento de Seguridad (access: 15 min, refresh: 7 días).
- Se creó `JWTService`, un wrapper que:
  - Genera el par de tokens con los datos mínimos necesarios ya incluidos (`sub`: quién es el usuario, `rol`: qué puede hacer, `exp`: cuándo expira, `jti`: identificador único del token, usado más adelante para detectar robos de sesión).
  - Valida un token recibido y devuelve sus datos, o rechaza el intento con un error claro si el token es falso, está vencido, o es del tipo equivocado (ej. usar un refresh token donde se esperaba uno de acceso).

Se probó con 5 tests: generación correcta del par de tokens, lectura de los datos de un access token, lectura de los datos de un refresh token, rechazo de un token inválido, y rechazo de un refresh token usado como si fuera de acceso.

## ¿Qué NO incluye?
- La lógica de login en sí (verificar contraseña) — eso es el punto 8b, que usa este servicio.
- La rotación y detección de reuso de refresh tokens — eso es el punto 9.

## En una frase
Se construyó y probó la maquinaria que genera y valida los "carnets digitales" (JWT) que el sistema usará para reconocer usuarios autenticados en cada petición.
