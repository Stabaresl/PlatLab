# Sprint 1 — Punto 3a: IUserRepository + mappers

## ¿Qué es esto?
La interfaz que define cómo se guarda y consulta un Usuario (`IUserRepository`), y el traductor (`mappers.py`) que convierte entre la entidad de negocio `User` (Domain, punto 2) y el modelo de base de datos `UserModel` (Infrastructure, punto 2).

## ¿Por qué es importante?
Ya teníamos las reglas de negocio de `User` (Domain) y la tabla real en Postgres (Infrastructure), pero nada las conectaba todavía. Definir primero la **interfaz** (qué operaciones existen: buscar por email, guardar, actualizar, etc.) antes que la implementación real permite que cualquier caso de uso (ej. `RegistrarUsuarioUseCase`) se escriba y se pruebe sin saber ni importarle si por debajo hay Postgres, una base en memoria para tests, o cualquier otra cosa — solo conoce el contrato.

## ¿Qué se hizo?
- **`repositories.py`**: la interfaz `IUserRepository` con las operaciones necesarias (buscar por id/email/username, verificar existencia, guardar, actualizar, y las mismas operaciones para `ProveedorAutenticacion`).
- **`mappers.py`**: funciones puras que convierten `UserModel` (ORM) ↔ `User` (entidad), y lo mismo para `ProveedorAutenticacionModel` ↔ `ProveedorAutenticacion`. Es la única parte del sistema que "conoce" ambos mundos a la vez.

## ¿Qué NO incluye?
- La implementación real que efectivamente consulta Postgres — eso es el punto 3b.

## En una frase
Se definió el contrato de persistencia de usuarios y el traductor entre la entidad de negocio y la tabla real, sin todavía implementar la conexión real a la base de datos.
