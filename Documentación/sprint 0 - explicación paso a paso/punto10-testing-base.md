# Sprint 0 — Punto 10: Testing base (pytest-django)

## ¿Qué es esto?

Es la configuración que permite escribir y correr **pruebas automáticas** (tests) sobre el código del proyecto, y la estructura de carpetas donde cada módulo va a guardar las suyas.

## ¿Por qué es importante?

Un test automático es código que verifica que otro código funciona correctamente, sin necesidad de que una persona lo pruebe manualmente cada vez. Esto es crítico por varias razones:

- **Detecta errores antes de que lleguen a producción.** Si alguien modifica una regla de negocio y sin querer rompe algo, los tests fallan inmediatamente en vez de que el error lo descubra un estudiante usando la plataforma real.
- **Da confianza para modificar código existente.** Sin tests, el equipo tiene miedo de tocar código antiguo porque no sabe qué más se puede romper. Con tests, se puede modificar y correr los tests para confirmar que nada se rompió.
- **Es un requisito del proyecto.** El documento de requisitos no funcionales exige al menos 80% de cobertura de tests en la lógica de negocio antes del release 1.0 (RNF-06.3) — esto solo es posible si la infraestructura de testing está lista desde el principio, no al final.

## ¿Qué se hizo exactamente?

### 1. Se completó la estructura de carpetas `tests/` en los 8 módulos
Cada módulo tiene su carpeta de tests dividida en 3 tipos, reflejando las 3 capas principales de la arquitectura:
- **`tests/domain/`**: prueba las reglas de negocio puras (ej. "¿se calcula bien el contador de fallos de una flag?").
- **`tests/application/`**: prueba los casos de uso completos (ej. "¿aceptar una invitación realmente crea el progreso inicial?").
- **`tests/presentation/`**: prueba los endpoints de la API (ej. "¿el endpoint de login devuelve 401 con credenciales incorrectas?").

### 2. Se configuró `pytest-django` (`pyproject.toml`)
Se le indicó a la herramienta de testing (`pytest`) cómo encontrar y ejecutar los tests del proyecto, y que use la configuración de Django de desarrollo al correrlos (para que tenga acceso al ORM, la base de datos de test, etc.).

### 3. Se escribió un test de humo (`test_kernel_smoke.py`)
Es un primer test que no prueba lógica de negocio todavía (porque aún no existe ninguna), sino que confirma que **la infraestructura de testing en sí misma funciona**: que los tests se detectan, que corren, que pueden usar las piezas del kernel de dominio (puntos 4-7), y que pueden crear y consultar una base de datos de prueba real sin afectar la base de datos de desarrollo.

## ¿Qué NO incluye este punto?

- Tests de lógica de negocio real — esos se escriben junto con cada caso de uso, a partir del Sprint 1 en adelante.
- Medición de cobertura de código (% de líneas cubiertas por tests) — es una tarea del Sprint 9, al cierre del proyecto.

## En una frase

Se dejó lista la infraestructura para que, desde el primer caso de uso real que se escriba, el equipo pueda (y deba) acompañarlo con pruebas automáticas que confirmen que funciona y que sigan funcionando aunque el código cambie más adelante.
