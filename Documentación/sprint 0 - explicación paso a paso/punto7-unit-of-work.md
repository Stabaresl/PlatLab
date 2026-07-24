# Sprint 0 — Punto 7: BaseUnitOfWork

## ¿Qué es esto?

Es la pieza que conecta el paso 3 de `BaseUseCase` (punto 5, "persistir de forma atómica") con PostgreSQL real. Garantiza que cada caso de uso guarde sus cambios en la base de datos de forma "todo o nada".

## ¿Por qué es importante?

Muchas acciones del sistema modifican varias tablas a la vez. Ejemplo: al aceptar una invitación, se actualiza el estado de la Asignación **y** se crea el Progreso inicial del estudiante. Si el sistema lograra guardar el primer cambio pero fallara justo antes del segundo (por ejemplo, se cae el servidor a mitad de camino), quedaría un estado inconsistente: una asignación marcada como aceptada pero sin ningún progreso asociado — un bug muy difícil de detectar y reparar manualmente.

Una **transacción atómica** evita esto: agrupa varios cambios como una sola unidad indivisible. O se confirman todos los cambios juntos, o —si algo falla en el medio— se deshacen todos, como si nada hubiera pasado. La base de datos nunca queda en un estado "a medias".

## ¿Qué se hizo exactamente?

Se creó `BaseUnitOfWork` en `modules/shared/infrastructure/`, que envuelve el mecanismo de transacciones de Django/PostgreSQL y se comporta así:

- Al iniciar (`with self._uow:`), abre una transacción.
- Si el caso de uso llega hasta el final y llama explícitamente a `commit()`, los cambios se confirman de verdad en la base de datos al cerrar el bloque.
- Si ocurre **cualquier excepción** dentro del bloque (ej. una regla de negocio se viola a mitad de camino), Django deshace automáticamente todo lo que se había escrito hasta ese punto — no queda ningún registro parcial.
- Si el bloque termina **sin** haber llamado a `commit()` (por ejemplo, un desarrollador se olvidó de confirmarlo), también se deshace por seguridad — el sistema nunca asume que algo debe guardarse "por accidente".

Esto se probó con tres casos reales usando el modelo de usuarios de Django:
1. Con `commit()` explícito → el registro queda guardado.
2. Sin `commit()` → el registro NO queda guardado (rollback automático).
3. Con una excepción a mitad de camino → el registro NO queda guardado (rollback automático).

## ¿Qué NO incluye este punto?

- Repositorios concretos por módulo (`IUserRepository`, `ILaboratorioRepository`, etc.) — esos se construyen en los sprints donde se implementa cada módulo, y son los que usan `BaseUnitOfWork` por debajo.

## En una frase

Se construyó la garantía de que ninguna acción del sistema puede dejar la base de datos en un estado "a medio guardar" — o se completa todo el cambio, o no se guarda nada.
