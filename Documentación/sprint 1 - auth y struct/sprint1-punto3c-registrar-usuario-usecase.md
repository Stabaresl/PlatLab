# Sprint 1 — Punto 3c: RegistrarUsuarioUseCase

## ¿Qué es esto?
La lógica completa del registro de un nuevo usuario con correo y contraseña: validaciones, hasheo seguro de la contraseña, y creación del usuario — siguiendo el molde `BaseUseCase` construido en el Sprint 0.

## ¿Por qué es importante?
Es el primer caso de uso real del sistema. Reúne todas las piezas construidas hasta ahora (kernel del Sprint 0, entidades y repositorio de Users) en una sola acción de negocio completa, con todas sus reglas: nadie puede registrarse dos veces con el mismo correo, la contraseña debe cumplir una política mínima de seguridad, y nunca se guarda la contraseña en texto plano.

## ¿Qué se hizo?
- **Validación de contraseñas coincidentes**: `password` y `password_confirm` deben ser iguales.
- **Política de contraseña** (RF-01): mínimo 8 caracteres, al menos 1 mayúscula, al menos 1 número.
- **Anti-enumeración de usuarios** (UC-01 E1): si el correo ya existe, el error es genérico ("Este correo ya está registrado"), sin dar pistas de más.
- **Hasheo seguro**: la contraseña nunca se guarda tal cual — se transforma con un algoritmo de hash seguro (RNF-01.2) antes de persistirla.
- **Evento `UserRegistered`**: al completarse el registro, se dispara un evento de dominio (mecanismo del Sprint 0) que en el futuro disparará el envío del correo de verificación — el "enchufe" ya queda listo, aunque todavía no hay nadie escuchando ese evento.

Se probó con 8 tests: registro exitoso, email duplicado, contraseñas no coincidentes, 3 variantes de contraseña débil, email con formato inválido, y que el evento se dispara correctamente.

## ¿Qué NO incluye?
- El endpoint HTTP para llamar esto desde afuera — eso es el punto 3d.
- El envío real del correo de verificación — el evento existe pero aún no tiene quién lo escuche.

## En una frase
Se construyó y probó la lógica completa (y segura) de registro de un nuevo usuario, lista para ser expuesta como endpoint.
