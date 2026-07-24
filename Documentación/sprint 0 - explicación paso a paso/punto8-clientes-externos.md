# Sprint 0 — Punto 8: RedisClient, EmailClient, StorageClient

## ¿Qué es esto?

Son 3 "conectores" reutilizables hacia servicios externos que el sistema necesita constantemente: memoria rápida (Redis), envío de correos, y almacenamiento de archivos.

## ¿Por qué es importante?

Varios módulos del sistema necesitan las mismas capacidades técnicas una y otra vez: guardar algo temporal con expiración (Redis), enviar un correo (email de verificación, recuperación de contraseña, notificaciones), o guardar un archivo (adjuntos de reportes de estudiantes). Sin estos conectores compartidos, cada módulo terminaría escribiendo su propia forma de hacer lo mismo, con inconsistencias y código duplicado.

Además, al centralizar el acceso a estos servicios en una sola clase por servicio, si el día de mañana se necesita cambiar de proveedor (ej. de guardar archivos en el disco local a guardarlos en Amazon S3), el cambio se hace en un solo lugar, sin tocar el código de negocio que los usa.

## ¿Qué se hizo exactamente?

### 1. `RedisClient`
Conector hacia Redis con operaciones simples: guardar (`set`), leer (`get`), eliminar (`delete`), verificar existencia (`exists`) y poner tiempo de expiración (`expire`). Se usará, por ejemplo, para guardar los "refresh tokens" de sesión con una expiración automática de 7 días (documento de Seguridad), sin tener que reescribir esa lógica en cada lugar que lo necesite.

### 2. `EmailClient`
Conector hacia el sistema de envío de correos de Django. En **desarrollo**, los correos no se envían de verdad — se imprimen en la consola/log del contenedor, para poder verificar el contenido sin necesidad de una cuenta de correo real ni gastar cuota de un proveedor SMTP. En **producción**, bastará con cambiar variables de entorno (sin tocar código) para que empiece a enviar correos reales por SMTP.

### 3. `StorageClient`
Conector hacia el sistema de archivos de Django. Hoy guarda los archivos en el disco local del servidor (carpeta `media/`), pensado para adjuntos de reportes de estudiantes (ej. una captura de pantalla de un error). El diseño ya está preparado para que, en producción, se pueda cambiar a almacenamiento en la nube (S3/MinIO) sin modificar el código que lo usa — solo cambia la configuración.

## ¿Qué NO incluye este punto?

- El envío real de emails por SMTP (queda configurado pero apagado por defecto en desarrollo).
- Almacenamiento en la nube real (S3/MinIO) — hoy es local, el cambio a la nube es solo configuración cuando se despliegue a producción.
- La validación específica de archivos subidos (tipo de archivo permitido, tamaño máximo) — eso se construye sobre `StorageClient` en el módulo de Reportes, más adelante.

## En una frase

Se construyeron los 3 conectores compartidos que cualquier módulo del sistema va a usar para guardar datos temporales, enviar correos o guardar archivos, sin que cada módulo tenga que resolver esas conexiones por su cuenta.
