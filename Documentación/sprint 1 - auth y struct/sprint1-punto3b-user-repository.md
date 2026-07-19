# Sprint 1 — Punto 3b: UserRepository (implementación real)

## ¿Qué es esto?
La implementación real de `IUserRepository` (punto 3a) que sí habla con PostgreSQL — es la pieza que finalmente conecta la lógica de negocio con la base de datos.

## ¿Por qué es importante?
Con la interfaz y el traductor ya definidos (3a), este punto es el que hace que todo funcione de verdad: cuando un caso de uso pida "guardar este usuario", `UserRepository` es quien efectivamente ejecuta el `INSERT` en Postgres. Separar esto en su propio paso permitió probarlo de forma aislada (con la base de datos real, pero sin lógica de negocio de por medio) antes de construir algo más complejo encima.

## ¿Qué se hizo?
Se implementó `UserRepository`, con cada método de la interfaz resuelto usando el ORM de Django (`UserModel.objects...`) y traduciendo siempre a través de `mappers.py` — el resto del sistema nunca ve un `UserModel` directamente, solo la entidad `User`. Se probó con 5 tests de integración reales contra Postgres: crear y buscar un usuario, buscar uno que no existe, verificar existencia por email, actualizar datos, y vincular/consultar un proveedor de autenticación (ej. Google).

## ¿Qué NO incluye?
- Ningún caso de uso todavía (registro, login) — esos son los puntos siguientes, y son quienes van a usar este repositorio.

## En una frase
Se conectó, por primera vez, la lógica de negocio de usuarios con una base de datos PostgreSQL real y probada.
