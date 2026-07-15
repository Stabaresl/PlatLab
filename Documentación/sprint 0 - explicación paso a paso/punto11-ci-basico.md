# Sprint 0 — Punto 11: CI básico (lint + tests automáticos)

## ¿Qué es esto?

Es un robot que corre automáticamente cada vez que alguien sube código a GitHub: revisa que el código esté bien escrito (lint) y que todos los tests pasen (testing), sin que ninguna persona tenga que hacerlo a mano.

## ¿Por qué es importante?

Hasta este punto, el proyecto tiene herramientas para escribir tests (punto 10) y para mantener el código ordenado, pero **nada obliga a que se usen** antes de subir cambios al repositorio compartido. Sin este punto, es posible que alguien suba código con errores de estilo, o que rompa un test existente sin darse cuenta, y que ese problema solo se descubra días después cuando ya afectó el trabajo de otro compañero.

CI significa "Integración Continua" (*Continuous Integration*): la idea de que cada cambio se valida automáticamente y de inmediato, en vez de esperar a integrarlo todo al final y descubrir los problemas tarde. Es la última capa de seguridad antes de que el código llegue a la rama principal del proyecto.

## ¿Qué se hizo exactamente?

### 1. `ruff` — Lint automático
Se agregó `ruff`, una herramienta que revisa el código Python en busca de errores comunes: imports que no se usan, variables no definidas, código mal formateado, etc. Se probó sobre **todo el código ya escrito en el Sprint 0** y no encontró ningún problema real (solo 2 falsos positivos esperables, que se configuraron como excepción a propósito, por un patrón válido de Django).

### 2. `.github/workflows/ci.yml` — El pipeline
Es la definición del robot que GitHub ejecuta automáticamente. Corre en 2 pasos (jobs), uno después del otro:

1. **`lint`**: revisa el estilo del código con `ruff`. Si algo está mal escrito, el pipeline falla aquí y ni siquiera intenta correr los tests.
2. **`test`**: levanta una base de datos PostgreSQL y un Redis temporales (exclusivos para esa ejecución, se destruyen al terminar) y corre toda la batería de tests del proyecto con `pytest`.

Esto se dispara automáticamente en **cada push**, a cualquier rama del repositorio — no hace falta que nadie lo ejecute manualmente ni lo recuerde.

### 3. ¿Dónde se ve el resultado?
En la pestaña **Actions** del repositorio en GitHub. Cada push queda con un ✅ verde (todo pasó) o ❌ rojo (algo falló), visible para todo el equipo — incluyendo, más adelante, directamente en cada Pull Request antes de aprobar una fusión de código.

## ¿Qué NO incluye este punto?

- Bloquear automáticamente que se fusione código a la rama principal si el CI falla (eso es una configuración de reglas de protección de rama en GitHub, se define con el equipo cuando se acuerde el flujo de trabajo de Git).
- Medición de cobertura de tests (%) dentro del pipeline — se agrega en el Sprint 9, cuando ya exista suficiente lógica de negocio para medir.
- Despliegue automático a producción — el CI de este punto solo valida, no despliega (eso es una etapa de CD, posterior, prevista para el Sprint 9).

## En una frase

Se dejó un robot corriendo en GitHub que revisa automáticamente el estilo del código y que todos los tests sigan pasando en cada cambio que se suba, sin depender de que alguien del equipo se acuerde de hacerlo manualmente.

---

## Cierre del Sprint 0

Con este punto se completan los 11 ítems del backlog fundacional: el proyecto Django está inicializado, contenerizado con Docker, conectado a PostgreSQL/Redis vía variables de entorno seguras, con el kernel de dominio y aplicación (`BaseEntity`, `BaseValueObject`, `DomainEvent`, excepciones, `BaseUseCase`) ya construido y probado, la infraestructura compartida lista (`EventDispatcher`, `BaseUnitOfWork`, `RedisClient`, `EmailClient`, `StorageClient`), documentación de API auto-generada, y testing + CI corriendo en cada push. A partir de aquí, el Sprint 1 empieza a construir funcionalidad de negocio real (Autenticación) sobre esta base ya validada.
