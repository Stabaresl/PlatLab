# Sprint 0 — Punto 5: Kernel de aplicación (BaseUseCase)

## ¿Qué es esto?

Es la plantilla que **todos** los "casos de uso" del sistema (crear laboratorio, aceptar invitación, validar flag, etc. — más de 40 en total) van a seguir exactamente igual, paso por paso.

## ¿Por qué es importante?

Un "caso de uso" es una acción concreta que un usuario puede realizar (ej. "Instructor invita a un estudiante"). Sin una plantilla común, cada desarrollador del equipo podría implementar sus casos de uso de forma distinta: uno valida antes de guardar, otro guarda y valida después, otro se olvida de manejar errores a medio camino, etc. Eso genera bugs difíciles de rastrear y hace que el código sea impredecible.

`BaseUseCase` fuerza a que **todos** los casos de uso sigan la misma secuencia de 4 pasos, sin excepción, evitando ese tipo de inconsistencias.

## ¿Qué se hizo exactamente?

### 1. `ports.py` — Los "enchufes" que el kernel necesita
Antes de construir la plantilla, se definieron dos interfaces (contratos) que `BaseUseCase` va a usar pero sin saber todavía *cómo* están implementadas por dentro:
- **`IUnitOfWork`**: representa "una transacción segura" — algo que se puede confirmar (`commit`) o deshacer (`rollback`) si algo sale mal.
- **`IEventDispatcher`**: representa "algo que avisa a otras partes del sistema que ocurrió un evento".

Esto permite que `BaseUseCase` quede terminado y probado *ya*, aunque las implementaciones reales de esas dos piezas (conectadas a PostgreSQL y a la lógica de notificaciones real) se construyan después, en los puntos 6 y 7. Es como diseñar un enchufe de pared sin todavía haber instalado la planta eléctrica — cualquier aparato que respete la forma del enchufe va a funcionar después sin cambios.

### 2. `base_use_case.py` — La plantilla (Template Method)
Define que **todo** caso de uso de escritura sigue siempre esta secuencia fija:

1. **Validar la entrada** — ¿los datos que llegaron tienen sentido? ¿el usuario tiene permiso?
2. **Ejecutar la lógica de negocio** — la acción en sí (ej. crear el registro de la invitación).
3. **Persistir de forma atómica** — guardar los cambios en la base de datos como una unidad indivisible: o se guarda todo, o no se guarda nada (evita que, por ejemplo, se cree una invitación pero falle a medias el registro de progreso asociado).
4. **Avisar del evento** — solo después de que el guardado fue exitoso, se notifica al resto del sistema de que la acción ocurrió (para que, por ejemplo, se dispare un email).

Cada caso de uso concreto (que se escribirá en sprints futuros) solo tiene que llenar los pasos 1 y 2 con su lógica específica — los pasos 3 y 4 ya vienen resueltos automáticamente por heredar de `BaseUseCase`.

## ¿Qué NO incluye este punto?

- Ningún caso de uso real del negocio todavía (esos empiezan en el Sprint 1, ej. `RegistrarUsuarioUseCase`).
- La implementación real de `IUnitOfWork` sobre PostgreSQL — eso es el punto 7.
- La implementación real de `IEventDispatcher` — eso es el punto 6.

## En una frase

Se construyó el molde común que asegura que cada una de las +40 acciones que el sistema puede realizar siga siempre el mismo orden seguro: validar, ejecutar, guardar de forma segura, y recién ahí avisar — sin atajos ni inconsistencias entre desarrolladores.
