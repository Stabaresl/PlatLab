# Sprint 1 — Punto 8c: LoginView

## ¿Qué es esto?
El endpoint HTTP real (`POST /api/v1/auth/login/`) que expone `LoginUseCase` (punto 8b) al mundo exterior. Con este punto, el flujo completo de "crear cuenta → iniciar sesión" queda disponible para cualquier frontend.

## ¿Por qué es importante?
Es el punto donde PlatLAB deja de ser solo lógica interna probada por tests, y pasa a ser algo que un frontend real (o Postman) puede usar de punta a punta: registrar un usuario y luego autenticarse con él, recibiendo un token que representa su sesión.

## ¿Qué se hizo?
- **`LoginRequestSerializer`**: valida la forma de los datos de entrada (correo, contraseña).
- **`LoginView`**: conecta el serializer con `LoginUseCase` y devuelve el par de tokens (`access`, `refresh`), su tiempo de expiración, y el rol del usuario.
- **Ruta registrada**: `POST /api/v1/auth/login/`.

Se probó con 4 tests HTTP: login exitoso con tokens devueltos correctamente, contraseña incorrecta (401), correo inexistente (401), y que el endpoint es público.

## ¿Qué NO incluye?
- Refrescar el token de acceso cuando expira, sin pedir contraseña de nuevo — eso es el punto 9 (actualmente en construcción).
- Cerrar sesión (logout) — punto 10.
- Que otros endpoints protegidos puedan usar este token para saber "quién soy" — eso requiere el punto 11 (`JWTAuthenticationMiddleware`), que todavía no existe. Es decir: ya se puede generar un token válido, pero ningún otro endpoint del sistema sabe todavía cómo leerlo.

## En una frase
Se completó, de punta a punta, el flujo de "crear cuenta e iniciar sesión" — un frontend ya puede implementar ambas pantallas contra el backend real.
