# PlatLAB

Plataforma de laboratorios prácticos de ciberseguridad y hacking ético. Cada laboratorio
trae teoría, una práctica guiada paso a paso en una consola dentro del navegador, una
*flag* que demuestra que resolviste el reto y un examen final. Los instructores publican
laboratorios, invitan estudiantes o abren **salas** con código para trabajar en grupo; el
administrador revisa lo que se publica y gestiona las cuentas.

- **Para estudiantes**: 12 laboratorios en 3 pistas (redes, web, criptografía), consola Linux simulada, progreso visual, XP, logros y un avatar que se viste con lo que ganas.
- **Para instructores**: laboratorios propios, invitaciones por correo, salas en vivo para hasta 100 personas y seguimiento del avance de cada estudiante.
- **Para administradores**: usuarios, revisión de laboratorios, solicitudes de instructor y el mapa de aprendizaje.

Backend en Django (arquitectura hexagonal por módulos) y frontend en React. La documentación
funcional y técnica extendida, sprint a sprint, está en [`Documentación/`](./Documentación);
el sistema visual, en [`design.md`](./design.md).

---

## Índice

**Para usar la plataforma**
- [Empieza en 5 minutos](#empieza-en-5-minutos)
- [Credenciales de prueba](#credenciales-de-prueba)
- [Primer recorrido según tu rol](#primer-recorrido-según-tu-rol)
- [Funciones en detalle](#funciones-en-detalle)
  - [Laboratorios](#laboratorios) · [Examen final](#examen-final) · [Roadmap](#roadmap) · [Salas privadas](#salas-privadas) · [Invitaciones](#invitaciones) · [Progreso, XP y avatar](#progreso-xp-y-avatar) · [Panel del administrador](#panel-del-administrador)
- [Probar las invitaciones paso a paso](#probar-las-invitaciones-paso-a-paso)
- [Usarla en un aula (modo red)](#usarla-en-un-aula-modo-red)
- [Glosario](#glosario)

**Para desarrollar**
- [Stack](#stack) · [Requisitos previos](#requisitos-previos) · [Arranque en modo desarrollo](#arranque-en-modo-desarrollo) · [Frontend](#frontend)
- [Crear o editar el contenido de un laboratorio](#crear-o-editar-el-contenido-de-un-laboratorio)
- [Correr sin Docker](#correr-sin-docker-backend-nativo) · [Tests](#tests) · [Variables de entorno](#variables-de-entorno)
- [Solución de problemas comunes](#solución-de-problemas-comunes) · [Estructura del proyecto](#estructura-del-proyecto)

---

## Empieza en 5 minutos

Solo necesitas **Docker Desktop** (Windows/macOS) o **Docker Engine + compose** (Linux), encendido. No hace falta instalar Python, Node ni Bun: todo se construye dentro de Docker.

```bash
git clone <url-del-repo>
cd PlatLab
```

| Sistema | Cómo instalar |
|---|---|
| Windows | Doble clic en **`instalar.cmd`** (o en PowerShell: `.\platlab.ps1`) |
| Linux / macOS | `bash platlab.sh` |

El instalador revisa los requisitos, crea el `.env` con claves aleatorias, construye las imágenes (también las de los laboratorios), levanta todo, carga los 12 laboratorios con sus guías, el mapa de aprendizaje, los logros y una sala de prueba, y al final te muestra la dirección para entrar. La primera vez tarda varios minutos; después arranca en segundos.

Te pregunta **cómo se va a usar**:

- **Solo en este computador** (lo normal para probar): entras por `http://localhost:8080` con las [cuentas demo](#credenciales-de-prueba). Nadie más en la red puede entrar.
- **En red / aula**: otros equipos entran por la IP de este. Ver [Usarla en un aula](#usarla-en-un-aula-modo-red).

Para el día a día (en Linux/macOS cambia `.\platlab.ps1` por `bash platlab.sh`):

| Comando | Qué hace |
|---|---|
| `.\platlab.ps1 iniciar` | Enciende la plataforma (por ejemplo, después de reiniciar el equipo) |
| `.\platlab.ps1 detener` | La apaga sin borrar nada |
| `.\platlab.ps1 estado` | Muestra qué servicios están corriendo |
| `.\platlab.ps1 logs [servicio]` | Muestra los registros (`web`, `worker`, `gateway`...) |
| `.\platlab.ps1 actualizar` | Descarga la última versión (`git pull`) y la reconstruye conservando los datos |
| `.\platlab.ps1 desinstalar [-BorrarDatos]` | Elimina los contenedores; con `-BorrarDatos` (`--borrar-datos` en Linux) también la base de datos |

Opciones sin preguntas, por ejemplo para preparar varios equipos: `.\platlab.ps1 instalar -Modo red -Puerto 8090 -AdminEmail profe@universidad.edu.co -SinPreguntas` (en Linux: `--modo red --puerto 8090 --admin-email ... --si`).

**Cómo queda armado.** Todo entra por un único puerto, servido por el contenedor `gateway` (Caddy): entrega la interfaz ya compilada, hace de proxy hacia la API y el WebSocket de la terminal, y sirve los archivos subidos de forma aislada (`docker-compose.local.yml`, `frontend/Dockerfile`, `frontend/docker/Caddyfile`). El backend corre con `config.settings.local`: `DEBUG` apagado y sobre HTTP, porque en una red local no hay dominio para un certificado. Para publicarlo en internet con HTTPS existe `docker-compose.prod.yml`.

> El instalador y el entorno de desarrollo comparten proyecto de Docker: para volver al modo desarrollo (código montado, puerto 8000) basta con `docker compose up -d`; para volver al modo instalado, `.\platlab.ps1 iniciar`.

---

## Credenciales de prueba

Las crea el instalador en modo «solo este computador» (o `seed_demo_data` en desarrollo):

| Rol | Email | Contraseña |
|---|---|---|
| Administrador | `admin@platlab.demo` | `Admin1234` |
| Instructor | `instructor@platlab.demo` | `Instructor1234` |
| Estudiante | `estudiante@platlab.demo` | `Estudiante1234` |

Estas contraseñas son públicas: el modo **red / aula** desactiva estas cuentas. Para cuentas reales usa `python manage.py create_production_users --admin-email ...` (genera la contraseña y la muestra una sola vez). Cualquier persona puede crear su propia cuenta de estudiante en **Registrarse**.

> La sesión se guarda por navegador. Para tener dos cuentas abiertas a la vez (por ejemplo, instructor y estudiante), usa una ventana de incógnito para la segunda.

---

## Primer recorrido según tu rol

Al entrar por primera vez, un **tour de bienvenida** señala las partes de la pantalla (y al terminarlo ganas el logro «Primeros Pasos»).

### Estudiante (`estudiante@platlab.demo`)

1. **Panel del estudiante** (`/dashboard`). Arriba está tu **núcleo de progreso**: una esfera 3D donde cada laboratorio asignado es una esfera más pequeña en órbita y sus lunas son las secciones. Al terminar un laboratorio, su esfera viaja y se suma al núcleo. Debajo: tus laboratorios con su avance, tus calificaciones y los próximos vencimientos.
2. **Roadmap** (`/roadmap`). El camino recomendado: 3 pistas de 4 laboratorios. El siguiente laboratorio disponible tiene la etiqueta «Siguiente»; los demás se desbloquean al terminar el anterior. Haz clic en uno disponible para inscribirte.
3. **Resolver un laboratorio**. La teoría se lee y se marca como completada. En la práctica tienes la guía a la izquierda (especificaciones del reto, tareas numeradas con «Copiar» / «Ejecutar en consola» y el resultado esperado) y la consola a la derecha. Cuando encuentres la flag, entrégala en **Entrega la flag**.
4. **Examen final**. Se habilita al completar todas las secciones. Lee las [reglas](#examen-final) antes de empezar: no se puede salir a mitad de camino.
5. **Salas**. Si tu instructor te da un código, escríbelo en el recuadro del panel o en **Salas**. Prueba con `PRUEBA`, la sala demo.
6. **Mi perfil** (`/profile`, desde tu avatar en la barra). Nivel y XP, tu avatar, logros, títulos e inventario con un probador para ver cómo te queda cada pieza.
7. **Ser instructor**. Al final del panel, «Convertirme en instructor» envía una solicitud con tu ORCID; un administrador la aprueba.

### Instructor (`instructor@platlab.demo`)

1. **Panel del instructor**. Tus laboratorios (borrador, en revisión, publicado), los estudiantes con su porcentaje de avance y el acceso a salas.
2. **Invitar estudiantes**. Botón arriba a la derecha: eliges un laboratorio publicado, pegas los correos y opcionalmente una fecha de vencimiento. Ver [paso a paso](#probar-las-invitaciones-paso-a-paso).
3. **Salas → Nueva sala**. Eliges laboratorio, cupo (hasta 100) y cierre opcional; compartes el código o el enlace y sigues el tablero en vivo.
4. **Crear un laboratorio** (`/laboratorios/nuevo`). Secciones de teoría y práctica, flags, examen y la consola de cada práctica. Al terminar lo envías a revisión: un administrador lo aprueba antes de publicarse.

### Administrador (`admin@platlab.demo`)

1. **Panel del administrador**: tabla de todos los usuarios (búsqueda, filtros por rol y estado, cambio de rol, habilitar o deshabilitar), cola de laboratorios en revisión, solicitudes de instructor y actividad reciente.
2. **Roadmap → Editar roadmap** (`/roadmap/admin`): crea pistas y ordena los laboratorios predeterminados.
3. **Catálogo**: decide qué laboratorios de instructores se muestran en el catálogo público.

El **catálogo** (`/laboratorios`) se puede ver sin iniciar sesión.

---

## Funciones en detalle

### Laboratorios

Cada laboratorio tiene esta forma, inspirada en los laboratorios de AWS:

| Parte | Qué contiene |
|---|---|
| **Teoría** | Escenario, objetivos, explicación con tablas y avisos (nota, consejo, atención, importante). Se marca como completada. |
| **Práctica** | La ficha **Especificaciones del reto** (tu equipo, objetivo, alcance, qué entregas, formato de la flag, dónde se entrega y las convenciones del laboratorio), tareas numeradas con su comando y el **resultado esperado**, y la consola. |
| **Flag** | Un texto con forma `FLAG{...}` que aparece al resolver el reto. Se entrega completa y distingue mayúsculas. |
| **Ayuda progresiva** | A los 5 intentos fallidos de flag se abre una pista; a los 15, el paso a paso. Equivocarse no resta. |
| **Examen final** | 4 preguntas de opción múltiple o respuesta abierta. Ver [reglas](#examen-final). |
| **Conclusión** | Qué aprendiste y cómo se defiende un sistema real. |

**La consola.** Casi todos los laboratorios usan una **consola simulada**: una máquina Linux que corre en tu navegador, con archivos, red y servicios propios del ejercicio. Entiende `ls`, `cd`, `cat`, `grep` con tuberías, `nmap` (`-sn`, `-sV`, `-p-`), `curl`, `nc`, `ping`, `ip`, `arp`, `md5sum`, `tr`, `base64` y más; `help` muestra la lista, Tab completa y las flechas recorren el historial. No ejecuta nada real.

El laboratorio «SQL Injection: Bypass de Login» además ofrece un **entorno real**: un contenedor Docker propio y descartable con la aplicación vulnerable, conectado por WebSocket (xterm.js). Se apaga solo si queda inactivo.

**Las 12 prácticas**

| Pista | Laboratorios |
|---|---|
| Fundamentos de Redes | Introducción a TCP/IP · Escaneo de Puertos con Nmap · Sniffing de Tráfico Básico · ARP Spoofing: Detectando un Man-in-the-Middle |
| Seguridad Web | SQL Injection: Nivel Básico · Cross-Site Scripting Reflejado · SQL Injection: Bypass de Login · Inyección SQL a Ciegas (Blind SQLi) |
| Criptografía Aplicada | Cifrado César y Frecuencia · Hashes y Fuerza Bruta Básica · Introducción a Cifrado Asimétrico · Esteganografía: Mensajes Ocultos en Imágenes |

**Vencimientos.** Una asignación puede tener fecha límite. Al vencer, el laboratorio queda en solo lectura: se puede revisar, pero no entregar flags ni presentar el examen.

### Examen final

- **3 intentos.** Si repruebas los 3, el examen se bloquea **24 horas** contadas desde el último; la pantalla muestra una cuenta regresiva. Después vuelves a tener 3. Aprobar también reinicia la cuenta (puedes volver a presentarlo para mejorar la nota).
- **Se aprueba con 60 %.** Solo aprobar cuenta como laboratorio terminado: en el panel, en el XP, en los logros y en el tablero de las salas.
- **No se puede salir.** Al empezar, el examen ocupa toda la pantalla. El botón Atrás muestra un aviso; recargar o cerrar la pestaña pide confirmación y **entrega lo que llevas**. Si esa entrega no alcanza a llegar, el intento cuenta como 0.
- Las preguntas solo llegan al empezar un intento: abrir el examen ya cuenta como presentarlo.

Estas reglas las aplica el servidor (`modules/progress`, `PoliticaDeIntentosExamen`), no solo la pantalla.

### Roadmap

El camino curado por la plataforma: pistas con laboratorios en orden. Cada uno se desbloquea al terminar el anterior de su pista. Cada pista muestra cuántos llevas, los caminos ya recorridos se ven en verde y el siguiente paso tiene la etiqueta «Siguiente». Inscribirse en un nodo crea la asignación al instante.

### Salas privadas

Para trabajar un laboratorio en grupo, con hora de inicio y competencia sana.

- Las crean instructores y administradores: laboratorio publicado, cupo de 1 a 100 y cierre opcional.
- Cada sala tiene un **código de 6 caracteres** (sin letras ni números que se confundan) y un enlace `/salas/unirse/CÓDIGO`.
- Cada estudiante recibe **su propio laboratorio** y, si lo hay, su propio entorno real.
- El **tablero en vivo** muestra el avance de cada participante, su examen y su puesto, junto a un lobby 3D donde cada persona orbita más cerca del centro a medida que avanza.
- Al terminar (aprobando el examen), el puesto da un bono de XP: **150 / 110 / 80**, y 50 para el resto. Hay logros y títulos propios de las salas.
- El anfitrión puede cerrar los ingresos o finalizar la sala.

Prueba rápida: entra como estudiante y usa el código `PRUEBA` (lo crea el instalador o `seed_sala_demo`).

### Invitaciones

El instructor invita por correo a estudiantes **ya registrados** a uno de sus laboratorios publicados, con un vencimiento opcional. El estudiante recibe una notificación y ve la invitación en su panel con **Aceptar / Rechazar**. Desde ahí, el instructor ve su avance en su panel.

### Progreso, XP y avatar

- **XP por laboratorio terminado**, según su dificultad: básico 50, intermedio 100, avanzado 150 (más el bono de sala). Hay 11 niveles.
- **12 logros**: el tour de bienvenida, 1, 5, 10 y 25 laboratorios, completar cada pista del roadmap, salas terminadas y primeros puestos. Cada logro muestra su avance (por ejemplo, 3/5) y qué recompensa da.
- **Recompensas**: títulos (uno equipado a la vez, se muestra bajo tu avatar) y piezas para el avatar: hoodie, gafas, máscara, gorra, audífonos, mochila, guantes, zapatos, insignias, aura y marco.
- **Avatar ilustrado**: eliges uno de 8 personajes (o subes tu foto) y cada pieza equipada se dibuja puesta en su lugar del cuerpo.
- **Inventario con probador**: la colección completa, con lo que te falta y qué logro lo da. Al pasar el mouse por una pieza, aunque esté bloqueada, tu avatar se la prueba.
- **Notificaciones**: la campana de la barra avisa de invitaciones, vencimientos, decisiones sobre tu solicitud de instructor y resultados de salas.

### Panel del administrador

- **Usuarios**: todos, paginados, con búsqueda por nombre o correo y filtros por rol y estado. Cambiar el rol y habilitar o deshabilitar se hace en la misma fila.
- **Solicitudes de instructor**: los datos de quien la envió junto a lo que dice OpenAlex de su ORCID (consulta automática en segundo plano). Se aprueba o se rechaza con un motivo.
- **Revisión de laboratorios**: los que los instructores enviaron, con vista previa completa antes de aprobar o rechazar.
- **Catálogo público** y **actividad reciente** (registro de auditoría).

---

## Probar las invitaciones paso a paso

1. Abre una **ventana de incógnito** (Ctrl+Shift+N) y crea un estudiante en `http://localhost:8080/signup`, por ejemplo `ana@prueba.co`.
2. En tu ventana normal entra como `instructor@platlab.demo` / `Instructor1234`.
3. En el panel del instructor pulsa **Invitar estudiantes**, elige «SQL Injection: Bypass de Login» (el laboratorio publicado del instructor demo), escribe `ana@prueba.co` y envía. El resultado debe decir «invitado».
4. En la ventana de Ana aparece la notificación y la invitación con **Aceptar / Rechazar**. Al aceptar, el laboratorio entra en órbita en su núcleo de progreso y **Continuar** lo abre.
5. Como instructor, Ana aparece en tu panel con su avance.

Con una **sala** es todavía más directo: como instructor, **Salas → Nueva sala**, y Ana entra con el código.

---

## Usarla en un aula (modo red)

1. Instala con `.\platlab.ps1 instalar -Modo red -AdminEmail tu@correo.com`. Crea un administrador con una contraseña que se muestra **una sola vez** y desactiva las cuentas demo.
2. En Windows, la red debe estar marcada como **Privada**. Si no ejecutas la consola como administrador, el instalador te imprime el comando para abrir el puerto en el firewall.
3. Los demás entran a `http://<IP-que-muestra-el-instalador>:8080` y se registran.
4. Para que alguien sea instructor: cámbiale el rol en **Panel admin → Usuarios**, o que lo pida desde su panel con su ORCID y tú apruebas la solicitud.
5. Para volver a las cuentas demo: `.\platlab.ps1 instalar -Modo local`.

---

## Glosario

| Término | Qué es |
|---|---|
| **Flag** | El texto `FLAG{...}` que prueba que resolviste la práctica. |
| **Asignación** | Tu inscripción a un laboratorio (por roadmap, invitación o sala). Puede tener vencimiento. |
| **Sección** | Una parte del laboratorio: teoría o práctica. Se desbloquean en orden. |
| **Especificaciones del reto** | La ficha al inicio de cada práctica: qué máquina eres, a qué apuntas y qué entregas. |
| **Pista** | Un grupo de laboratorios del roadmap (por ejemplo, Seguridad Web). |
| **Sala** | Un grupo que resuelve el mismo laboratorio con un código, un tablero y premios por puesto. |
| **Núcleo de progreso** | La esfera del panel del estudiante: cada laboratorio terminado se le suma. |
| **Consola simulada / entorno real** | Máquina Linux en el navegador / contenedor Docker propio por estudiante. |

---

## Stack

**Backend**
- Python 3.12, Django 6, Django REST Framework, SimpleJWT
- PostgreSQL 16 (pool de conexiones nativo de Django + psycopg 3), Redis 7
- Uvicorn con varios procesos (HTTP + WebSocket, ASGI) y Django Channels para la terminal real
- Celery + Celery Beat: tareas asíncronas, vencimiento de asignaciones, reaper de entornos inactivos y una cola dedicada (`entornos`) para levantar laboratorios en paralelo
- `docker` (SDK de Python): el backend crea contenedores Docker "hermanos", uno por estudiante, a través de un proxy del socket que solo deja pasar las llamadas necesarias

**Frontend**
- React 19 + TypeScript + Vite
- Tailwind CSS 4 + shadcn/ui (Radix UI)
- framer-motion (animaciones) y three.js (núcleo de progreso, lobby de salas y globo de la portada, en carga diferida)
- xterm.js (terminal real por WebSocket) y un intérprete de consola propio (`frontend/src/lib/shell`)

**Infraestructura**: Docker Compose (`postgres`, `redis`, `docker-proxy`, `web`, `worker`, `worker-entornos`, `beat` y, en la instalación local, `gateway`).

---

## Requisitos previos

Para **usar** la plataforma basta con Docker (ver [Empieza en 5 minutos](#empieza-en-5-minutos)). Para **desarrollar**, instala además:

| Herramienta | Versión mínima | Para qué | Verificar con |
|---|---|---|---|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | con compose 2.24.4 o superior; en Windows, backend WSL2 | correr Postgres/Redis/backend y los contenedores de cada laboratorio | `docker --version` y `docker compose version` |
| [Git](https://git-scm.com/) | cualquiera reciente | clonar el repo | `git --version` |
| [Bun](https://bun.sh/) | 1.2 o superior (o Node.js 20+ y npm) | frontend en modo desarrollo | `bun --version` |
| Python | 3.12+ | **solo** si vas a correr el backend fuera de Docker | `python --version` |

**Windows**: Docker Desktop debe estar corriendo con el backend **WSL2** activado (no Hyper-V clásico): el proxy del socket de Docker monta `/var/run/docker.sock`, y eso solo funciona de forma confiable con WSL2. Abre Docker Desktop y espera a que diga *Engine running* antes de arrancar.

---

## Arranque en modo desarrollo

En este modo el código del repo se monta dentro de los contenedores. Todo el backend (API, workers, beat, base de datos, Redis) corre en Docker, y el mismo Docker que los corre es el que el backend usa para levantar los laboratorios ("Docker-outside-of-Docker").

```bash
git clone <url-del-repo>
cd PlatLab
cp .env.example .env          # los valores de ejemplo sirven para desarrollo local
docker compose up --build     # en segundo plano: docker compose up -d --build
```

`.env` **nunca** se sube al repositorio (está en `.gitignore`): cada quien mantiene el suyo.

Servicios que levanta (la primera vez descarga imágenes y puede tardar unos minutos):

- `postgres`: base de datos (sin puerto publicado; ver `docker-compose.override.example.yml` si necesitas entrar desde el host)
- `redis`: caché, broker de Celery y refresh tokens (sin puerto publicado)
- `docker-proxy`: único punto de contacto con el Docker del host
- `web`: Uvicorn sirviendo la API REST + WebSocket en `http://localhost:8000`
- `worker`: Celery (notificaciones, auditoría, verificación OpenAlex, vencimientos)
- `worker-entornos`: Celery con hilos, dedicado a levantar contenedores de laboratorio
- `beat`: tareas periódicas (expira asignaciones vencidas, apaga entornos inactivos)

Solo `web` corre las migraciones al arrancar (`docker/entrypoint.sh`); los workers esperan a que esté sano. Uvicorn en desarrollo **no recarga el código solo**: después de cambiar el backend, `docker compose restart web`.

**Cargar los datos de demo** (con los contenedores corriendo):

```bash
docker compose exec web python manage.py seed_demo_data              # usuarios demo, laboratorio y asignación
docker compose exec web python manage.py seed_roadmap_labs           # pistas del roadmap
docker compose exec web python manage.py seed_labs_expansion         # el resto de los 12 laboratorios
docker compose exec web python manage.py seed_gamification_catalog   # logros, cosméticos y títulos
docker compose exec web python manage.py actualizar_contenido_labs   # guías, especificaciones, consola y examen
docker compose exec web python manage.py seed_sala_demo              # sala de prueba con el código PRUEBA
docker build -t platlab-target-sqli:latest docker/targets/sqli-login # imagen del laboratorio con terminal real
```

Todos son idempotentes: correrlos de nuevo no duplica datos. `actualizar_contenido_labs` actualiza en su lugar, así que no borra el avance de nadie. `seed_demo_data --activar-cuentas-demo` reactiva las cuentas demo si antes instalaste en modo red.

El backend queda en `http://localhost:8000/api/v1/`.

---

## Frontend

En otra terminal, desde la raíz del repo:

```bash
cd frontend
bun install     # o: npm install
bun run dev     # o: npm run dev
```

Se sirve en `http://localhost:5173` y apunta al backend en `http://localhost:8000/api/v1`. En el build de producción (el que usa el instalador) usa rutas relativas, porque la interfaz y la API comparten origen detrás del gateway. Para forzar otra URL, crea `frontend/.env.local`:

```bash
VITE_API_URL=http://localhost:8000/api/v1
# Solo si configuraste credenciales OAuth reales en el backend:
# VITE_OAUTH_ENABLED=true
```

Los botones de login social (Google/GitHub) están ocultos por defecto porque no hay credenciales OAuth configuradas: es lo esperado en un entorno de prueba, no un error.

Antes de tocar la interfaz, lee [`design.md`](./design.md): fija colores, tipografía, movimiento, el fondo ASCII, el avatar y las reglas de cada tipo de pantalla.

---

## Crear o editar el contenido de un laboratorio

Los 12 laboratorios predeterminados viven como datos en `modules/laboratories/management/commands/_contenido_{redes,web,cripto}.py` y se aplican con `actualizar_contenido_labs` (`--solo "Nombre exacto"` para uno solo). Cada laboratorio define:

- `descripcion`, `resumen_cierre` (la conclusión) y dos `secciones` (teoría y práctica) con `titulo`, `duracion`, `objetivos`, `html` y `pasos`: tuplas `(título, instrucciones HTML, comando sugerido, resultado esperado)`.
- `entorno` de la práctica: la máquina de la consola simulada (formato abajo).
- `especificaciones`: `objetivo`, `alcance`, `entregar` y `convenciones` (lista). El comando les suma las filas comunes (tu equipo, formato de la flag, dónde se entrega, la consola) y arma la ficha «Especificaciones del reto».
- `flag` (`pista` y `paso_a_paso`) y `examen` (lista de preguntas con `tipo`, `opciones` y `respuesta`).

El HTML pasa por un sanitizador con lista blanca (`content_sanitizer.py`): tablas, `pre`, `code`, `kbd` y los avisos `<div class="nota|aviso|tip|importante|escenario|especificaciones">`. Los tests de `modules/laboratories/tests/application/test_contenido_labs.py` comprueban que cada laboratorio esté completo, que la flag exista en la máquina simulada y que el HTML sobreviva al sanitizador.

Los instructores crean los suyos desde la interfaz (`/laboratorios/nuevo`); la máquina simulada y el resultado esperado de cada paso, por ahora, se definen por la API de secciones.

### La máquina de la consola simulada

La consola de cada sección práctica se arma con `entorno_practica`. Además del guion (`comandos`, con `patron` opcional para aceptar variantes), admite un `escenario` que describe la máquina. El intérprete vive en `frontend/src/lib/shell/`.

```json
{
  "prompt": "estudiante@kali:~$",
  "banner": "Objetivo autorizado: servidor.lab",
  "comandos": [{ "comando": "./verificar clave", "patron": "(\\./)?verificar\\s+clave", "salida": "FLAG{...}" }],
  "escenario": {
    "host": "kali", "ip": "10.10.14.7",
    "archivos": { "notas.txt": "texto", "/etc/passwd": "root:x:0:0" },
    "red": [{
      "ip": "192.168.56.20", "nombre": "servidor.lab", "mac": "08:00:27:5a:11:20",
      "servicios": [{ "puerto": 22, "servicio": "ssh", "version": "OpenSSH 8.9p1", "banner": "SSH-2.0-OpenSSH_8.9p1" }],
      "http": [{ "ruta": "/buscar", "cuando": "<script", "cuerpo": "Resultados: {{q}} FLAG{...}" }]
    }],
    "efectos": [{ "patron": "steghide extract .*-p gaia", "archivos": { "secreto.txt": "FLAG{...}" } }]
  }
}
```

- `http[].cuando` es una expresión regular contra los datos enviados y la query: permite responder distinto según el payload (inyección, XSS). `{{param}}` refleja el parámetro tal cual.
- `efectos` crea archivos cuando una línea coincide con el patrón.
- Cada paso de la guía admite `resultado_esperado`, que se muestra como bloque bajo el comando.

### API del examen

| Método y ruta | Qué hace |
|---|---|
| `GET /api/v1/progress/{asignacion}/exam/` | Estado: intentos restantes, bloqueo, si quedó un intento abierto. No devuelve preguntas. |
| `POST /api/v1/progress/{asignacion}/exam/iniciar/` | Abre un intento y entrega las preguntas (o `iniciado: false` si está bloqueado). Cierra como 0 un intento abandonado. |
| `POST /api/v1/progress/{asignacion}/exam/` | Entrega y califica el intento abierto. |

---

## Correr sin Docker (backend nativo)

Alternativa para desarrollar el backend sin reconstruir la imagen. Igual necesitas **Postgres y Redis** (copia `docker-compose.override.example.yml` como `docker-compose.override.yml` para publicarlos en `127.0.0.1` y luego `docker compose up postgres redis`) y **Docker corriendo en el host** si quieres los entornos reales de laboratorio.

```bash
python -m venv venv
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

pip install -r requirements/dev.txt -c requirements/constraints.txt

# Edita .env: POSTGRES_HOST=localhost y REDIS_URL=redis://localhost:6379/0
# ("postgres"/"redis" solo resuelven dentro de la red de docker compose)

python manage.py migrate
python manage.py seed_demo_data

# Uvicorn, no runserver: runserver no entiende WebSockets y la terminal
# real se queda "conectando" para siempre.
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --lifespan off
```

En otras terminales, los workers y las tareas periódicas:

```bash
celery -A config worker -l info
celery -A config worker -Q entornos --pool threads --concurrency 20 -n entornos@%h -l info
celery -A config beat -l info
```

---

## Tests

**Backend** (pytest contra `config.settings.test`: Celery en modo síncrono, no necesita worker). En modo desarrollo:

```bash
docker compose exec web pytest
docker compose exec web ruff check .
```

Con la plataforma instalada (la imagen de `web` es de producción y no trae pytest), construye una imagen de pruebas y córrela contra la misma base:

```bash
docker build -t platlab-pruebas --build-arg REQUIREMENTS_FILE=requirements/dev.txt .
docker run --rm --network platlab_default --env-file .env -e POSTGRES_HOST=postgres \
  -v "$(pwd):/app" -w /app platlab-pruebas pytest -q
```

En PowerShell cambia `$(pwd)` por `${PWD}`. pytest crea su propia base `test_*`: no toca los datos de la instalación.

**Frontend** (tipos + lint):

```bash
cd frontend
bun run build   # tsc -b + vite build: falla si hay errores de tipos
bun run lint
```

**Carga y estrés**: ver [`loadtests/README.md`](./loadtests/README.md) (Locust para la API y un script que levanta 100 laboratorios a la vez).

---

## Variables de entorno

Definidas en `.env` (plantilla completa en `.env.example`; el instalador las completa solo):

| Variable | Uso | ¿Hace falta tocarla para desarrollo local? |
|---|---|---|
| `SECRET_KEY` | clave de Django (firma de tokens) | no en local; en cualquier instalación compartida, una aleatoria (el instalador la genera) |
| `FLAG_HASH_KEY` | clave HMAC de flags y respuestas de examen; vacía = derivada de `SECRET_KEY` | no; si rotas `SECRET_KEY`, pon aquí la anterior |
| `DEBUG` | modo debug de Django | no |
| `ALLOWED_HOSTS` | hosts permitidos (dev/prod) | no |
| `CORS_ALLOWED_ORIGINS` | orígenes permitidos para el frontend de desarrollo | no, ya incluye `localhost:5173` |
| `POSTGRES_*` | conexión a la base de datos | no, salvo que cambies credenciales |
| `REDIS_URL` | Celery, refresh tokens, canal de Channels | no |
| `DJANGO_ADMIN_URL` | ruta del admin de Django | no; el instalador usa una ruta aleatoria |
| `PLATLAB_MODO`, `PLATLAB_PORT`, `PLATLAB_BIND` | modo, puerto y alcance de la instalación local | las escribe el instalador |
| `WEB_CONCURRENCY`, `CELERY_CONCURRENCY`, `LAB_ENV_*` | capacidad (procesos web, workers, laboratorios simultáneos) | solo para afinar con muchos usuarios |
| `DEFAULT_FROM_EMAIL` | remitente de emails (dev usa consola) | no |
| `GOOGLE_OAUTH_*`, `GITHUB_OAUTH_*` | login social | solo para probar OAuth real; si no, déjalos en `changeme` y los botones quedan ocultos |

**Frontend** (`frontend/.env.local`, opcional, no versionado):

| Variable | Valor si no se define |
|---|---|
| `VITE_API_URL` | `http://localhost:8000/api/v1` en desarrollo; `/api/v1` (mismo origen) en el build de producción |
| `VITE_OAUTH_ENABLED` | `false` (oculta los botones de Google/GitHub) |

---

## Solución de problemas comunes

**El instalador dice que Docker no está corriendo**
Abre Docker Desktop y espera a que diga *Engine running*. En Linux: `sudo systemctl start docker`; si el error es de permisos, agrega tu usuario al grupo `docker` (`sudo usermod -aG docker $USER`) y vuelve a iniciar sesión.

**El instalador falla descargando imágenes (`no such host`, `timeout`)**
Es la red: el instalador reintenta solo cuatro veces. Si sigue fallando, revisa la conexión (o el proxy de la red de la institución) y vuelve a ejecutarlo; retoma sin perder nada.

**Las cuentas demo dicen «credenciales inválidas»**
Probablemente instalaste antes en modo red, que las desactiva. Reinstala en modo local (`.\platlab.ps1 instalar -Modo local`) o corre `python manage.py seed_demo_data --activar-cuentas-demo`.

**Otros equipos de la red no logran entrar (modo red / aula)**
Comprueba que entras desde el propio equipo con `http://<IP>:8080`. Si ahí funciona, es el firewall: en Windows ejecuta el instalador como administrador o crea la regla que te sugiere, y marca la red como *Privada*. Si la IP del equipo cambió (DHCP), solo usa la nueva: no hace falta reinstalar.

**No veo los cambios después de actualizar**
El navegador guarda la versión anterior: recarga con Ctrl+F5. En modo desarrollo, el backend necesita `docker compose restart web`.

**El examen dice que está bloqueado**
Reprobaste los 3 intentos: la pantalla muestra cuándo se desbloquea (24 h después del último). Es la regla, no un error.

**`docker compose up` falla en `docker-proxy` con error sobre `/var/run/docker.sock`**
En Windows, confirma que Docker Desktop usa el backend **WSL2** (Settings → General → "Use the WSL 2 based engine").

**`port is already allocated` para 8000 / 8080 / 5173**
Otro programa ya usa ese puerto. Detenlo o elige otro: `.\platlab.ps1 instalar -Puerto 8090` (instalación) o cambia el mapeo en `docker-compose.yml` / `vite.config.ts` (desarrollo).

**El frontend de desarrollo carga pero las peticiones a la API fallan / error de CORS**
Confirma que el backend esté arriba en `http://localhost:8000` y que `CORS_ALLOWED_ORIGINS` en `.env` incluya la URL exacta del frontend (por defecto `http://localhost:5173`).

**La terminal "real" de un laboratorio se queda en "conectando..."**
- Confirma que existe la imagen del laboratorio: `docker images platlab-target-sqli` (el instalador la construye; en desarrollo, ver los datos de demo).
- Confirma que Docker está corriendo y revisa `docker compose logs -f worker-entornos web` por errores del SDK de Docker.
- Si corres el backend fuera de Docker, usa `uvicorn` (no `runserver`, que no soporta WebSockets).

**`seed_demo_data` falla o no crea nada**
Necesita las migraciones aplicadas: sin Docker, corre antes `python manage.py migrate`. Si falla a mitad de camino, vuelve a correrlo: retoma sin duplicar lo ya creado.

**No tengo Bun instalado**
Solo hace falta para el frontend en desarrollo. Todos los comandos `bun ...` tienen equivalente en `npm` (`npm install`, `npm run dev`); el repo versiona `bun.lock`, así que npm generará su propio `package-lock.json` local.

**Los botones de login con Google/GitHub no aparecen**
Es lo esperado sin credenciales OAuth reales (ver [Variables de entorno](#variables-de-entorno)).

---

## Estructura del proyecto

Backend organizado por módulos con arquitectura hexagonal (domain / application / infrastructure / presentation). Detalle módulo por módulo en [`Documentación/estructura-carpetas.md`](./Documentación/estructura-carpetas.md).

```
PlatLab/
├── config/                    # settings (dev, local, prod, test), urls, asgi, celery
├── modules/
│   ├── authentication/        # registro, login, JWT, OAuth
│   ├── users/                 # usuarios, roles, solicitudes de instructor (OpenAlex)
│   ├── laboratories/          # laboratorios, secciones, flags, exámenes, contenido de los 12 labs
│   ├── assignments/           # asignaciones e invitaciones, vencimientos
│   ├── progress/              # avance por sección, flags, examen (intentos y bloqueo)
│   ├── lab_environments/      # contenedores Docker por estudiante y terminal por WebSocket
│   ├── rooms/                 # salas privadas con código y tablero
│   ├── roadmap/               # pistas y nodos del mapa de aprendizaje
│   ├── gamification/          # XP, niveles, logros, cosméticos, títulos, avatar
│   ├── notifications/, audit/, reports/
│   └── shared/                # casos de uso base, eventos, unit of work
├── docker/                    # entrypoint.sh + targets vulnerables de los laboratorios
├── frontend/                  # React + Vite (+ Dockerfile del gateway)
│   └── src/
│       ├── pages/             # una pantalla por archivo; api.ts es el cliente de la API
│       ├── components/        # three/ (escenas 3D), avatar/, examen/, movimiento/, marca/, salas/, ui/
│       └── lib/shell/         # intérprete de la consola simulada
├── loadtests/                 # pruebas de carga (Locust) y de estrés de laboratorios
├── requirements/              # base / dev / prod + constraints.txt (versiones congeladas)
├── Documentación/             # documentación funcional y técnica por sprint
├── design.md                  # sistema visual de la interfaz
├── docker-compose.yml         # desarrollo
├── docker-compose.local.yml   # instalación local / aula (platlab.ps1, platlab.sh)
├── docker-compose.prod.yml    # servidor en internet con HTTPS (Caddy)
├── instalar.cmd, platlab.ps1  # instalador y administración en Windows
├── platlab.sh                 # instalador y administración en Linux/macOS
└── .env.example
```

Para el detalle funcional (casos de uso, reglas de negocio, dominio) y el progreso sprint a sprint, ver [`Documentación/`](./Documentación).
