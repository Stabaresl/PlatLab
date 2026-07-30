# Sprint 3 — Punto 3: Target vulnerable de demo ("SQL Injection: Bypass de Login")

## ¿Qué es esto?

La primera imagen Docker real que se usa como `imagen_practica` de una
sección — un servidor HTTP mínimo, deliberadamente vulnerable a inyección
SQL, que corre **dentro** del contenedor de práctica de cada estudiante.

## ¿Por qué es importante?

Todo lo construido en los puntos 1 y 2 de este sprint (contenedores
aislados, WebSocket, terminal real) no sirve de nada sin algo real contra
lo cual practicar. Este target es la prueba de concepto end-to-end: valida
que el flujo completo (crear contenedor → exec interactivo → estudiante
ataca el objetivo → obtiene la flag) funciona con un caso realista y no
solo en teoría.

## ¿Qué se hizo exactamente?

### 1. La aplicación vulnerable — `docker/targets/sqli-login/app.py`

Un servidor HTTP escrito con la librería estándar de Python únicamente
(`http.server`, sin dependencias externas — imagen liviana y rápida de
construir), que expone un formulario de login (`/login.php`) contra una
base SQLite en memoria con un único usuario (`admin` / `S3cr3tP4ss!`).

La vulnerabilidad es real y a propósito: la consulta arma el `WHERE`
**concatenando strings** directamente con lo que mandó el usuario, en vez
de usar parámetros:

```python
query = (
    "SELECT username FROM users WHERE username = '"
    + username + "' AND password = '" + password + "'"
)
```

Exactamente el patrón vulnerable que describe el material teórico de la
sección — el estudiante que manda algo como `' OR '1'='1` como usuario
bypasea el login y la respuesta HTML incluye la flag
(`FLAG{sql_injection_1s_ez}` por defecto, configurable por
`LAB_FLAG`).

### 2. Aislamiento del target

El servidor escucha únicamente en `127.0.0.1:5000` — solo es alcanzable
**desde dentro del propio contenedor** del estudiante (por la sesión
`exec` que abre `TerminalConsumer`), nunca expuesto directamente a la red.
Sumado a `network_disabled=True` del contenedor completo (Sprint 3, punto
1), el target queda completamente aislado tanto de Internet como de otros
estudiantes.

### 3. `docker/targets/sqli-login/Dockerfile`

Build mínimo: imagen base liviana + copia de `app.py` + `CMD` que lo
ejecuta. `notes.txt` en la misma carpeta documenta, para quien mantenga el
laboratorio, que ese archivo de notas internas no debería quedar accesible
fuera del servidor y que la migración a *prepared statements* es
justamente lo que el laboratorio **no** hace a propósito (es el bug que el
estudiante tiene que encontrar).

## ¿Qué NO incluye este punto?

- Más targets vulnerables — este es el único hasta el momento; el patrón
  (`docker/targets/<nombre>/{Dockerfile,app.py}`) queda listo para
  replicarse con otras vulnerabilidades (XSS, IDOR, etc.) simplemente
  agregando una carpeta nueva y apuntando `imagen_practica` a ella.
- Build/publicación automática de la imagen en CI — se construye local con
  `docker build` (o queda pendiente de automatizar) y se referencia por
  nombre desde `Seccion.imagen_practica`.

## En una frase

Se armó el primer objetivo vulnerable real y deliberado (bypass de login
por SQL injection, con flag incluida) que corre aislado dentro del
contenedor de cada estudiante, cerrando el círculo completo del entorno de
práctica real construido en este sprint.
