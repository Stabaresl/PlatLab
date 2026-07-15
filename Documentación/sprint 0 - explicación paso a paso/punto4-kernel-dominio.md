# Sprint 0 — Punto 4: Kernel de dominio

## ¿Qué es esto?

Son las 4 piezas de código más fundamentales de todo el proyecto: las "reglas base" que **todas** las entidades de negocio (Usuario, Laboratorio, Asignación, Progreso, etc.) de los 8 módulos van a heredar y reutilizar.

## ¿Por qué es importante?

PlatLAB sigue una arquitectura donde la lógica de negocio (llamada "Domain") vive completamente separada de Django, de la base de datos y de la web. Esto significa, por ejemplo, que la regla "una sección no se puede completar sin resolver su flag" se puede probar sin necesitar un servidor corriendo ni una base de datos conectada — es lógica de Python pura.

Para que esa separación funcione de forma consistente en los 8 módulos, se necesitan primero unas piezas base compartidas, en vez de que cada módulo invente su propia forma de identificar entidades o manejar errores.

## ¿Qué se hizo exactamente?

Se creó `modules/shared/domain/` con 4 archivos:

### 1. `base_entity.py` — `BaseEntity`
Toda "Entidad" del sistema (un Usuario, un Laboratorio, una Asignación) tiene una identidad única (`id`). `BaseEntity` define que dos objetos son "el mismo" si tienen el mismo `id`, aunque el resto de sus datos sea distinto en ese momento — igual que en la vida real, una persona sigue siendo la misma persona aunque cambie de nombre.

### 2. `base_value_object.py` — `BaseValueObject`
A diferencia de una Entidad, un "Value Object" (como un Email, o un NivelDificultad) no tiene identidad propia — se compara por su **valor**. Dos objetos `Email("ana@uni.edu")` son iguales entre sí simplemente porque tienen el mismo contenido, sin necesidad de un `id`. Además son inmutables (no se pueden modificar después de creados), lo cual evita bugs donde un dato cambia "por accidente" en un lugar inesperado del código.

### 3. `domain_event.py` — `DomainEvent`
Es la base de todos los "eventos de dominio" — cosas que pasaron en el sistema y que otras partes del código necesitan enterarse (ej. "se aceptó una invitación", "se publicó un laboratorio"). Cada evento lleva automáticamente un identificador único y la fecha/hora exacta en que ocurrió. Estos eventos son el mecanismo que, por ejemplo, hace que al aceptar una invitación se cree automáticamente el progreso del estudiante, o que se dispare una notificación, sin que ese código esté mezclado directamente adentro de la lógica de aceptar la invitación.

### 4. `exceptions.py` — Excepciones base
Define los tipos de error que la lógica de negocio puede lanzar, ya alineados con los códigos de error que la API va a devolver (documento `api.md`): dato inválido, recurso no encontrado, conflicto (ej. email duplicado), regla de negocio violada, sin permiso, no autenticado. Esto es clave porque significa que la lógica de negocio nunca tiene que preocuparse por "qué código HTTP devolver" — solo lanza la excepción que corresponde, y una capa más arriba (que se construirá más adelante) la traduce automáticamente al formato de error estándar de la API.

## ¿Qué NO incluye este punto?

- Las entidades reales del negocio (`User`, `Laboratorio`, etc.) — esas se crean en sprints posteriores, heredando de estas bases.
- Conexión a base de datos — este código es 100% independiente de Django y de PostgreSQL, a propósito.

## En una frase

Se construyeron las 4 piezas de vocabulario común (identidad, valor, evento, error) que toda la lógica de negocio del proyecto va a usar de la misma forma, sin importar el módulo.
