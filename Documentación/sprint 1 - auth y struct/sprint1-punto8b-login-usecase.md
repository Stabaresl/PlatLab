# Sprint 1 — Punto 8b: LoginUseCase

## ¿Qué es esto?
La lógica completa de inicio de sesión: verifica que el correo y la contraseña sean correctos, y si lo son, entrega el par de tokens JWT (punto 8a) que el usuario usará de ahí en adelante.

## ¿Por qué es importante?
Es el segundo caso de uso real del sistema (después del registro) y el que finalmente permite "entrar" a la plataforma. También aplica una regla de seguridad clave: el mensaje de error ante credenciales incorrectas es siempre el mismo, genérico ("Credenciales inválidas"), sin importar si el problema fue que el correo no existe o que la contraseña estaba mal — así un atacante no puede usar el mensaje de error para descubrir qué correos están registrados en la plataforma (mismo principio anti-enumeración ya aplicado en el registro).

## ¿Qué se hizo?
- Busca al usuario por correo y compara la contraseña ingresada contra el hash guardado (nunca se compara la contraseña "en texto plano" directamente).
- Si el usuario no existe, o la contraseña no coincide → error genérico de credenciales inválidas.
- Si el usuario existe y la contraseña es correcta, pero la cuenta está deshabilitada → error específico de cuenta deshabilitada (a diferencia del anterior, este si distingue el motivo, porque ya se confirmó que la persona es dueña de esa cuenta).
- Si todo es correcto: actualiza la fecha de último login, genera el par de tokens JWT, y dispara un evento `UserLoggedIn` (insumo para el futuro módulo de auditoría).

Se probó con 6 tests: login exitoso, actualización de último login, contraseña incorrecta, correo inexistente, cuenta deshabilitada, y disparo del evento.

## ¿Qué NO incluye?
- El endpoint HTTP — eso es el punto 8c.
- Bloqueo temporal tras varios intentos fallidos (rate limiting de login) — es una capa transversal (middleware) pendiente para más adelante.

## En una frase
Se construyó y probó la lógica completa de login: verificación segura de credenciales y entrega del par de tokens JWT correspondiente.
