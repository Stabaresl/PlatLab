# Sprint 1 — Punto 1: Health-check público

## ¿Qué es esto?

Es un endpoint (una URL de la API) que responde con un simple "estoy bien" o "algo falla", consultando en tiempo real si el backend puede conectarse a sus dos dependencias críticas: la base de datos y Redis.

## ¿Por qué es importante?

Antes de que exista cualquier funcionalidad real (login, catálogo, etc.), tanto el frontend como el equipo de monitoreo necesitan una forma sencilla de responder la pregunta "¿el backend está disponible ahora mismo?". Por ejemplo:

- La landing page (HV-01) puede usarlo para avisarle al usuario si la plataforma está temporalmente caída, en vez de mostrar una pantalla en blanco o un error confuso.
- En producción, herramientas de monitoreo automático consultan este endpoint cada cierto tiempo para detectar caídas y alertar al equipo antes de que un usuario reporte el problema.

Es intencionalmente el primer punto del Sprint 1 porque es el endpoint más simple posible — sirve para confirmar que toda la cadena (Django, Docker, la URL, la respuesta JSON) funciona de punta a punta, antes de construir algo con lógica de negocio real encima.

## ¿Qué se hizo exactamente?

### 1. `HealthCheckView`
Un endpoint público (no requiere login) en `GET /api/v1/health/` que hace dos verificaciones reales:
- Intenta ejecutar una consulta mínima contra PostgreSQL.
- Intenta hacer ping a Redis.

Si ambas responden bien, devuelve `200 OK` con el detalle de cada chequeo. Si alguna falla, devuelve `503 Service Unavailable` — el código HTTP estándar para "el servicio no está disponible temporalmente".

### 2. Tests automáticos
Se probaron dos casos: que el endpoint responde `200` cuando todo está sano, y que **no** exige autenticación (a diferencia de casi todos los demás endpoints del sistema, este debe ser accesible sin login).

## ¿Qué NO incluye este punto?

- Métricas de rendimiento (tiempos de respuesta, uptime histórico) — eso es el dashboard de rendimiento (HA-04), previsto para el Sprint 9.

## En una frase

Se construyó el primer endpoint real de la API: una forma pública y automática de confirmar si el backend y sus dependencias (base de datos, Redis) están funcionando correctamente en cualquier momento.
