"""Contenido estilo AWS de los laboratorios de la pista «Fundamentos de Redes»."""

_MI_IP = "10.10.14.7"

TCP_IP = {
    "nombre": "Introducción a TCP/IP",
    "descripcion": (
        "Recorre las capas de TCP/IP sobre una red real simulada: comprueba conectividad, "
        "descubre puertos abiertos y conéctate a un servicio escondido en un puerto no estándar."
    ),
    "resumen_cierre": (
        "<p>Recorriste el camino completo de cualquier reconocimiento: saber quién eres en la red "
        "(<code>ip a</code>), comprobar que el objetivo responde (<code>ping</code>), ver qué "
        "puertos tiene abiertos (<code>nmap</code>) y hablar directamente con un servicio "
        "(<code>nc</code>).</p>"
        "<div class=\"tip\"><p>Lo que viste en la tarea 4 pasa en sistemas reales: un servicio en un "
        "puerto alto no está oculto, solo es menos obvio. «Seguridad por oscuridad» no es seguridad.</p></div>"
        "<p><strong>Siguiente paso:</strong> en <em>Escaneo de Puertos con Nmap</em> aprenderás a "
        "identificar versiones de servicio y a descubrir todos los equipos de una subred.</p>"
    ),
    "secciones": [
        {
            "titulo": "El modelo TCP/IP y los puertos",
            "duracion": 12,
            "objetivos": [
                "Ubicar cada protocolo común en su capa de TCP/IP.",
                "Explicar qué identifica una dirección IP y qué identifica un puerto.",
                "Reconocer los puertos de los servicios más comunes.",
            ],
            "html": (
                "<div class=\"escenario\"><p>Acabas de entrar al equipo de seguridad de una universidad. "
                "Tu primera tarea es revisar un servidor del laboratorio de redes: nadie recuerda qué "
                "servicios dejó encendidos el último administrador.</p></div>"
                "<h3>Cuatro capas, cuatro preguntas</h3>"
                "<p>TCP/IP divide la comunicación en capas. Cada una resuelve un problema y le entrega su "
                "resultado a la de arriba:</p>"
                "<table><thead><tr><th>Capa</th><th>Pregunta que responde</th><th>Ejemplos</th></tr></thead><tbody>"
                "<tr><td>Aplicación</td><td>¿Qué quiere decir la aplicación?</td><td>HTTP, SSH, DNS, FTP</td></tr>"
                "<tr><td>Transporte</td><td>¿A qué programa del equipo va?</td><td>TCP, UDP (puertos)</td></tr>"
                "<tr><td>Internet</td><td>¿A qué equipo de la red va?</td><td>IP, ICMP (ping)</td></tr>"
                "<tr><td>Acceso a red</td><td>¿Cómo viajan los bits por el cable o el aire?</td><td>Ethernet, Wi-Fi, ARP</td></tr>"
                "</tbody></table>"
                "<h3>IP y puerto: la dirección completa</h3>"
                "<p>La <strong>IP</strong> lleva el paquete hasta el equipo. El <strong>puerto</strong> "
                "(0–65535) dice qué programa dentro del equipo lo recibe. Juntos forman un "
                "<em>socket</em>, por ejemplo <code>192.168.56.20:22</code>.</p>"
                "<table><thead><tr><th>Puerto</th><th>Servicio</th><th>Para qué sirve</th></tr></thead><tbody>"
                "<tr><td><code>22</code></td><td>SSH</td><td>Administración remota cifrada</td></tr>"
                "<tr><td><code>53</code></td><td>DNS</td><td>Traducir nombres a IP</td></tr>"
                "<tr><td><code>80</code></td><td>HTTP</td><td>Web sin cifrar</td></tr>"
                "<tr><td><code>443</code></td><td>HTTPS</td><td>Web cifrada con TLS</td></tr>"
                "<tr><td><code>3306</code></td><td>MySQL</td><td>Base de datos</td></tr>"
                "</tbody></table>"
                "<div class=\"nota\"><p>Que un servicio use su puerto «oficial» es una convención "
                "(<code>/etc/services</code>), no una regla. Nada impide correr SSH en el 2222 o un "
                "servicio propio en el 31337.</p></div>"
                "<h3>TCP y UDP</h3>"
                "<p><strong>TCP</strong> establece una conexión (el saludo de tres vías SYN, SYN-ACK, ACK) y "
                "garantiza que todo llegue en orden. <strong>UDP</strong> envía y olvida: más rápido, sin "
                "garantías. Web, SSH y correo usan TCP; DNS y streaming suelen usar UDP.</p>"
            ),
            "pasos": [],
            "entorno": None,
        },
        {
            "titulo": "Identificando servicios expuestos",
            "duracion": 18,
            "objetivos": [
                "Comprobar la conectividad con un equipo usando ICMP.",
                "Distinguir un escaneo de puertos comunes de uno completo.",
                "Conectarse a un servicio TCP y leer su banner.",
            ],
            "html": (
                "<h3>Tu misión</h3>"
                "<p>El servidor <code>servidor.lab</code> (<code>192.168.56.20</code>) tiene un servicio "
                "que nadie documentó. Encuéntralo, conéctate y recupera la flag que entrega al conectarse.</p>"
                "<table><thead><tr><th>Equipo</th><th>IP</th><th>Rol</th></tr></thead><tbody>"
                f"<tr><td>Tu máquina (kali)</td><td><code>{_MI_IP}</code></td><td>Desde aquí trabajas</td></tr>"
                "<tr><td>servidor.lab</td><td><code>192.168.56.20</code></td><td>Objetivo autorizado</td></tr>"
                "</tbody></table>"
                "<div class=\"aviso\"><p>Escanear equipos ajenos sin permiso es ilegal en Colombia (Ley 1273 "
                "de 2009). Aquí todo es simulado y el objetivo está autorizado para la práctica.</p></div>"
            ),
            "pasos": [
                (
                    "Revisa tu propia dirección",
                    "<p>Antes de mirar a otros, confirma quién eres en la red: tu IP y la interfaz que usas.</p>",
                    "ip a",
                    "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> ...\n    inet 10.10.14.7/24 brd 10.10.14.255 scope global dynamic eth0",
                ),
                (
                    "Comprueba que el objetivo responde",
                    "<p><code>ping</code> usa ICMP (capa Internet): si hay respuesta, el equipo está "
                    "encendido y alcanzable. <code>-c 3</code> envía solo tres paquetes.</p>",
                    "ping -c 3 192.168.56.20",
                    "64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=0.6 ms\n...\n3 packets transmitted, 3 received, 0% packet loss",
                ),
                (
                    "Escanea los puertos comunes",
                    "<p>Sin opciones, <code>nmap</code> revisa los ~1000 puertos más usados. Anota qué "
                    "servicios aparecen.</p>",
                    "nmap 192.168.56.20",
                    "PORT      STATE SERVICE\n22/tcp    open  ssh\n80/tcp    open  http",
                ),
                (
                    "Escanea los 65 535 puertos",
                    "<p>El escaneo anterior no mostró nada raro, pero solo miró los puertos comunes. "
                    "<code>-p-</code> revisa todos. Tarda más: en una red real, mucho más.</p>",
                    "nmap -p- 192.168.56.20",
                    "PORT      STATE SERVICE\n22/tcp    open  ssh\n80/tcp    open  http\n31337/tcp open  unknown",
                ),
                (
                    "Consulta el puerto en /etc/services",
                    "<p>Linux trae una lista de puertos «oficiales». Compara: el 22 aparece; el 31337 no, "
                    "porque no pertenece a ningún servicio estándar.</p>",
                    "grep -w 22 /etc/services",
                    "ssh             22/tcp                          # SSH Remote Login Protocol",
                ),
                (
                    "Conéctate al servicio desconocido",
                    "<p><code>nc</code> (netcat) abre una conexión TCP y te muestra lo que el servicio "
                    "responde. Copia la flag y entrégala a la derecha.</p>",
                    "nc 192.168.56.20 31337",
                    "Bienvenido al puerto secreto del laboratorio.\nFLAG{...}",
                ),
            ],
            "entorno": {
                "prompt": "estudiante@kali:~$",
                "banner": "Objetivo autorizado: servidor.lab (192.168.56.20).",
                "escenario": {
                    "host": "kali",
                    "ip": _MI_IP,
                    "archivos": {
                        "notas.txt": (
                            "Inventario pendiente del servidor del laboratorio de redes\n"
                            "- IP: 192.168.56.20 (servidor.lab)\n"
                            "- Documentados: SSH (22), web interna (80)\n"
                            "- El administrador anterior mencionó 'un servicio de pruebas' sin decir el puerto.\n"
                        ),
                        "/etc/services": (
                            "ftp             21/tcp\nssh             22/tcp                          # SSH Remote Login Protocol\n"
                            "telnet          23/tcp\nsmtp            25/tcp          mail\ndomain          53/udp\n"
                            "http            80/tcp          www             # WorldWideWeb HTTP\n"
                            "https           443/tcp                         # http protocol over TLS/SSL\n"
                            "mysql           3306/tcp\n"
                        ),
                    },
                    "red": [
                        {
                            "ip": "192.168.56.20",
                            "nombre": "servidor.lab",
                            "mac": "08:00:27:5a:11:20",
                            "so": "Linux; CPE: cpe:/o:linux:linux_kernel",
                            "servicios": [
                                {"puerto": 22, "servicio": "ssh", "version": "OpenSSH 8.9p1 Ubuntu 3ubuntu0.6", "banner": "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6"},
                                {"puerto": 80, "servicio": "http", "version": "Apache httpd 2.4.52 ((Ubuntu))"},
                                {"puerto": 31337, "servicio": "unknown", "banner": "Bienvenido al puerto secreto del laboratorio.\nFLAG{tcp_ip_puertos_101}"},
                            ],
                            "http": [{"ruta": "/", "cuerpo": "<html><body><h1>Laboratorio de redes</h1><p>Servidor interno.</p></body></html>"}],
                        }
                    ],
                },
                "comandos": [],
            },
        },
    ],
    "flag": {
        "pista": "El escaneo por defecto solo mira los puertos comunes: prueba nmap con -p- para revisarlos todos.",
        "paso_a_paso": "1) nmap -p- 192.168.56.20 muestra el puerto 31337 abierto.\n2) nc 192.168.56.20 31337 se conecta y el servicio imprime la flag.",
    },
    "examen": [
        {"enunciado": "¿En qué capa de TCP/IP se ubican TCP y UDP?", "tipo": "opcion_multiple", "opciones": ["Aplicación", "Transporte", "Internet", "Acceso a red"], "respuesta": "Transporte"},
        {"enunciado": "¿Qué puerto usa por convención HTTPS?", "tipo": "opcion_multiple", "opciones": ["80", "22", "443", "8080"], "respuesta": "443"},
        {"enunciado": "¿Por qué el primer escaneo con nmap no mostró el servicio del puerto 31337?", "tipo": "opcion_multiple", "opciones": ["Porque estaba filtrado por un firewall", "Porque nmap sin opciones solo revisa los puertos más comunes", "Porque el servicio estaba apagado", "Porque usa UDP"], "respuesta": "Porque nmap sin opciones solo revisa los puertos más comunes"},
        {"enunciado": "¿Qué protocolo usa ping para comprobar si un equipo responde?", "tipo": "opcion_multiple", "opciones": ["TCP", "ICMP", "ARP", "DNS"], "respuesta": "ICMP"},
    ],
}

NMAP = {
    "nombre": "Escaneo de Puertos con Nmap",
    "descripcion": (
        "Descubre los equipos de una subred, identifica versiones de servicio con nmap -sV y "
        "encuentra la información que un banner mal configurado deja expuesta."
    ),
    "resumen_cierre": (
        "<p>Pasaste de «¿hay alguien ahí?» a un inventario con versiones: <code>-sn</code> para "
        "descubrir equipos, <code>-sV</code> para saber qué software exacto corre y <code>nc</code> "
        "para leer un banner de primera mano.</p>"
        "<div class=\"importante\"><p>La versión <code>vsftpd 2.3.4</code> que encontraste es famosa: "
        "una copia con puerta trasera circuló en 2011. Identificar versiones es el puente entre el "
        "reconocimiento y la búsqueda de vulnerabilidades conocidas (CVE).</p></div>"
    ),
    "secciones": [
        {
            "titulo": "Reconocimiento activo con Nmap",
            "duracion": 12,
            "objetivos": [
                "Elegir el tipo de escaneo adecuado según lo que se busca.",
                "Interpretar los estados open, closed y filtered.",
                "Explicar por qué identificar versiones es clave en un pentest.",
            ],
            "html": (
                "<div class=\"escenario\"><p>Te asignaron auditar la subred <code>192.168.56.0/24</code> "
                "del laboratorio. Antes de buscar fallas necesitas un inventario: qué equipos hay y qué "
                "software expone cada uno.</p></div>"
                "<h3>Las opciones que vas a usar</h3>"
                "<table><thead><tr><th>Opción</th><th>Qué hace</th><th>Cuándo usarla</th></tr></thead><tbody>"
                "<tr><td><code>-sn</code></td><td>Solo descubre equipos vivos, sin escanear puertos</td><td>Primer barrido de una subred</td></tr>"
                "<tr><td><code>-p 21,22</code></td><td>Escanea solo esos puertos</td><td>Confirmar algo puntual</td></tr>"
                "<tr><td><code>-p-</code></td><td>Escanea los 65 535 puertos</td><td>Inventario completo</td></tr>"
                "<tr><td><code>-sV</code></td><td>Conversa con cada servicio para saber su versión</td><td>Buscar vulnerabilidades conocidas</td></tr>"
                "<tr><td><code>-A</code></td><td>Versiones, sistema operativo y scripts por defecto</td><td>Cuando el ruido no importa</td></tr>"
                "</tbody></table>"
                "<h3>Estados de un puerto</h3>"
                "<ul><li><strong>open</strong>: un programa acepta conexiones.</li>"
                "<li><strong>closed</strong>: el equipo responde, pero nadie escucha en ese puerto.</li>"
                "<li><strong>filtered</strong>: no hay respuesta; casi siempre un firewall descarta los paquetes.</li></ul>"
                "<h3>¿Por qué importan las versiones?</h3>"
                "<p>«Hay un FTP» dice poco. «Hay un <code>vsftpd 2.3.4</code>» te permite buscar en bases de "
                "datos como <a href=\"https://nvd.nist.gov\">NVD</a> si esa versión tiene fallas públicas.</p>"
                "<div class=\"aviso\"><p>Un escaneo con <code>-A</code> o <code>-p-</code> es ruidoso: los "
                "sistemas de detección lo notan. En un pentest real se acuerda por escrito el alcance y el "
                "horario antes de lanzar nada.</p></div>"
            ),
            "pasos": [],
            "entorno": None,
        },
        {
            "titulo": "Inventario de la subred con detección de versiones",
            "duracion": 20,
            "objetivos": [
                "Descubrir los equipos vivos de una subred /24.",
                "Obtener las versiones de los servicios de un equipo.",
                "Encontrar información sensible en un banner.",
            ],
            "html": (
                "<h3>Tu misión</h3>"
                "<p>Haz el inventario de la subred y revisa en detalle el servidor de archivos. Uno de sus "
                "servicios anuncia más de lo que debería en su banner: ahí está la flag.</p>"
                "<div class=\"tip\"><p>Puedes redirigir la salida de cualquier comando a un archivo con "
                "<code>&gt;</code> y luego buscar en él con <code>grep</code>. Es como se trabaja con "
                "escaneos largos.</p></div>"
            ),
            "pasos": [
                (
                    "Descubre los equipos de la subred",
                    "<p>Un barrido <code>-sn</code> te dice qué IP responden, sin tocar sus puertos.</p>",
                    "nmap -sn 192.168.56.0/24",
                    "Nmap scan report for gateway.lab (192.168.56.1)\nNmap scan report for ftp.lab (192.168.56.21)\nNmap scan report for web.lab (192.168.56.22)\nNmap done: 256 IP addresses (3 hosts up)",
                ),
                (
                    "Escanea el servidor de archivos",
                    "<p>Empieza con un escaneo normal de <code>ftp.lab</code>.</p>",
                    "nmap 192.168.56.21",
                    "PORT      STATE SERVICE\n21/tcp    open  ftp\n22/tcp    open  ssh\n3306/tcp  open  mysql",
                ),
                (
                    "Identifica las versiones",
                    "<p>Ahora con <code>-sV</code>. Lee con calma la columna VERSION de cada servicio.</p>",
                    "nmap -sV 192.168.56.21",
                    "PORT      STATE SERVICE  VERSION\n21/tcp    open  ftp      vsftpd 2.3.4 (...)\n22/tcp    open  ssh      OpenSSH 8.9p1\n3306/tcp  open  mysql    MySQL 5.7.42",
                ),
                (
                    "Guarda el escaneo y búscalo",
                    "<p>Guarda el resultado en un archivo y filtra la línea que te interesa.</p>",
                    "nmap -sV 192.168.56.21 > escaneo.txt && grep ftp escaneo.txt",
                    "21/tcp    open  ftp      vsftpd 2.3.4 (FLAG{...})",
                ),
                (
                    "Confirma el banner a mano",
                    "<p>Conéctate al FTP con <code>nc</code>: el servidor saluda con el mismo banner que "
                    "leyó nmap.</p>",
                    "nc 192.168.56.21 21",
                    "220 (vsFTPd 2.3.4) FLAG{...}",
                ),
            ],
            "entorno": {
                "prompt": "estudiante@kali:~$",
                "banner": "Alcance autorizado: 192.168.56.0/24.",
                "escenario": {
                    "host": "kali",
                    "ip": _MI_IP,
                    "archivos": {
                        "alcance.txt": "Alcance del ejercicio: 192.168.56.0/24\nFuera de alcance: cualquier otra red\nHorario: libre (entorno de laboratorio)\n"
                    },
                    "red": [
                        {"ip": "192.168.56.1", "nombre": "gateway.lab", "mac": "52:54:00:12:35:01", "servicios": [{"puerto": 53, "servicio": "domain", "version": "dnsmasq 2.86"}]},
                        {
                            "ip": "192.168.56.21",
                            "nombre": "ftp.lab",
                            "mac": "08:00:27:a1:21:21",
                            "so": "Unix",
                            "servicios": [
                                {"puerto": 21, "servicio": "ftp", "version": "vsftpd 2.3.4 (FLAG{nmap_sv_banner_grab})", "banner": "220 (vsFTPd 2.3.4) FLAG{nmap_sv_banner_grab}"},
                                {"puerto": 22, "servicio": "ssh", "version": "OpenSSH 8.9p1", "banner": "SSH-2.0-OpenSSH_8.9p1"},
                                {"puerto": 3306, "servicio": "mysql", "version": "MySQL 5.7.42", "banner": "5.7.42-0ubuntu0.18.04.1"},
                            ],
                        },
                        {"ip": "192.168.56.22", "nombre": "web.lab", "mac": "08:00:27:b2:22:22", "servicios": [{"puerto": 80, "servicio": "http", "version": "nginx 1.18.0 (Ubuntu)"}], "http": [{"ruta": "/", "cuerpo": "<h1>Portal del laboratorio</h1>"}]},
                    ],
                },
                "comandos": [],
            },
        },
    ],
    "flag": {
        "pista": "La flag está en la versión que anuncia uno de los servicios: usa nmap -sV sobre ftp.lab.",
        "paso_a_paso": "1) nmap -sV 192.168.56.21\n2) La columna VERSION del puerto 21 incluye la flag (también la ves con nc 192.168.56.21 21).",
    },
    "examen": [
        {"enunciado": "¿Qué opción de nmap descubre los equipos vivos de una red sin escanear sus puertos?", "tipo": "opcion_multiple", "opciones": ["-sV", "-sn", "-p-", "-A"], "respuesta": "-sn"},
        {"enunciado": "Un puerto aparece como «filtered». ¿Qué es lo más probable?", "tipo": "opcion_multiple", "opciones": ["El servicio está caído", "Un firewall descarta los paquetes", "El puerto está abierto pero vacío", "El equipo está apagado"], "respuesta": "Un firewall descarta los paquetes"},
        {"enunciado": "¿Para qué sirve conocer la versión exacta de un servicio?", "tipo": "opcion_multiple", "opciones": ["Para buscar vulnerabilidades públicas de esa versión", "Para acelerar el escaneo", "Para ocultar el escaneo", "Para cifrar la conexión"], "respuesta": "Para buscar vulnerabilidades públicas de esa versión"},
        {"enunciado": "Antes de escanear la red de un cliente en un pentest real, ¿qué es indispensable?", "tipo": "opcion_multiple", "opciones": ["Usar -A para no perder nada", "Tener autorización y alcance acordados por escrito", "Desactivar el firewall del cliente", "Escanear de noche"], "respuesta": "Tener autorización y alcance acordados por escrito"},
    ],
}

_CAPTURA = """No.  Hora      Origen           Destino          Protocolo  Info
1    10:02:11  192.168.56.40    192.168.56.1     DNS        Standard query A intranet.lab
2    10:02:11  192.168.56.1     192.168.56.40    DNS        Standard query response A 192.168.56.60
3    10:02:12  192.168.56.40    192.168.56.60    TCP        51022 -> 80 [SYN]
4    10:02:12  192.168.56.60    192.168.56.40    TCP        80 -> 51022 [SYN, ACK]
5    10:02:12  192.168.56.40    192.168.56.60    HTTP       GET /login HTTP/1.1
     Host: intranet.lab
     User-Agent: Mozilla/5.0
6    10:02:12  192.168.56.60    192.168.56.40    HTTP       HTTP/1.1 200 OK (text/html)
7    10:02:19  192.168.56.40    192.168.56.60    HTTP       POST /login HTTP/1.1
     Host: intranet.lab
     Content-Type: application/x-www-form-urlencoded
     username=admin&password=FLAG{sniff_http_plaintext}
8    10:02:19  192.168.56.60    192.168.56.40    HTTP       HTTP/1.1 302 Found (Location: /panel)
9    10:03:40  192.168.56.40    142.250.78.4     TLSv1.3    Client Hello (SNI=correo.ejemplo.com)
10   10:03:40  142.250.78.4     192.168.56.40    TLSv1.3    Application Data [cifrado]
"""

SNIFFING = {
    "nombre": "Sniffing de Tráfico Básico",
    "descripcion": (
        "Analiza una captura de tráfico de una red compartida y comprueba por qué un login sobre "
        "HTTP sin cifrar regala la contraseña a cualquiera que escuche."
    ),
    "resumen_cierre": (
        "<p>Viste con tus propios ojos la diferencia entre el paquete 7 (HTTP: usuario y contraseña "
        "legibles) y el 10 (TLS: <em>Application Data</em> cifrado). Eso es todo lo que HTTPS hace por "
        "ti, y es mucho.</p>"
        "<div class=\"tip\"><p>Como usuario: desconfía de cualquier formulario de login que no use "
        "<code>https://</code>. Como desarrollador: HTTPS en todo el sitio y la cabecera HSTS.</p></div>"
    ),
    "secciones": [
        {
            "titulo": "Tráfico en claro y sniffing",
            "duracion": 10,
            "objetivos": [
                "Explicar qué ve un atacante que comparte la red con la víctima.",
                "Diferenciar tráfico HTTP de tráfico TLS en una captura.",
                "Justificar el uso de HTTPS en todo formulario.",
            ],
            "html": (
                "<div class=\"escenario\"><p>Un profesor reporta que alguien entró a su cuenta de la "
                "intranet. Se conectaba desde la Wi-Fi abierta de la cafetería. El equipo de redes te "
                "entrega una captura de tráfico de esa red para que expliques cómo pudo pasar.</p></div>"
                "<h3>¿Qué es hacer sniffing?</h3>"
                "<p>Es capturar los paquetes que pasan por una red. En una red compartida (Wi-Fi abierta, "
                "un hub, un switch con el puerto en espejo) cualquiera con la herramienta adecuada "
                "(<code>tcpdump</code>, Wireshark) puede ver el tráfico de los demás.</p>"
                "<h3>HTTP frente a HTTPS</h3>"
                "<table><thead><tr><th></th><th>HTTP</th><th>HTTPS (HTTP sobre TLS)</th></tr></thead><tbody>"
                "<tr><td>Puerto típico</td><td><code>80</code></td><td><code>443</code></td></tr>"
                "<tr><td>Contenido en la captura</td><td>Legible: URLs, cabeceras, formularios</td><td>Cifrado: solo se ve a qué servidor te conectas</td></tr>"
                "<tr><td>Contraseña de un login</td><td>Visible tal cual</td><td>Ilegible</td></tr>"
                "</tbody></table>"
                "<div class=\"nota\"><p>Los formularios de login viajan casi siempre como <code>POST</code>, "
                "con los campos en el cuerpo de la petición: <code>username=...&amp;password=...</code>.</p></div>"
            ),
            "pasos": [],
            "entorno": None,
        },
        {
            "titulo": "Analizando la captura",
            "duracion": 15,
            "objetivos": [
                "Navegar una captura de tráfico con herramientas de texto.",
                "Encontrar la petición que contiene las credenciales.",
                "Comparar un paquete HTTP con uno TLS.",
            ],
            "html": (
                "<h3>Tu misión</h3>"
                "<p>En tu directorio está <code>captura.pcap.txt</code>, la exportación en texto de la "
                "captura. Encuentra la petición con las credenciales del profesor: la contraseña es la flag.</p>"
                "<div class=\"tip\"><p><code>grep -A N</code> muestra las N líneas siguientes a cada "
                "coincidencia: útil cuando el dato está debajo de la línea que buscas.</p></div>"
            ),
            "pasos": [
                ("Mira qué hay en tu directorio", "<p>Lista los archivos con detalle.</p>", "ls -l", "-rw-r--r-- 1 estudiante estudiante ... captura.pcap.txt\n-rw-r--r-- 1 estudiante estudiante ... LEEME.txt"),
                ("Dimensiona la captura", "<p>¿Cuántas líneas tiene? Así sabes si conviene leerla entera o filtrar.</p>", "wc -l captura.pcap.txt", "16 captura.pcap.txt"),
                (
                    "Filtra solo el tráfico HTTP",
                    "<p>El protocolo es la quinta columna. Busca las líneas HTTP con su número de línea.</p>",
                    "grep -n HTTP captura.pcap.txt",
                    "6:5    10:02:12  ...  HTTP       GET /login HTTP/1.1\n...\n11:7    10:02:19  ...  HTTP       POST /login HTTP/1.1",
                ),
                (
                    "Mira el cuerpo del POST",
                    "<p>Las credenciales están unas líneas debajo de la petición POST.</p>",
                    "grep -A3 POST captura.pcap.txt",
                    "7    10:02:19  ...  POST /login HTTP/1.1\n     Host: intranet.lab\n     Content-Type: application/x-www-form-urlencoded\n     username=admin&password=FLAG{...}",
                ),
                (
                    "Compara con el tráfico cifrado",
                    "<p>Ahora mira los paquetes TLS: ¿qué puedes saber de ellos?</p>",
                    "grep TLS captura.pcap.txt",
                    "9    10:03:40  ...  TLSv1.3    Client Hello (SNI=correo.ejemplo.com)\n10   10:03:40  ...  TLSv1.3    Application Data [cifrado]",
                ),
            ],
            "entorno": {
                "prompt": "estudiante@kali:~$",
                "banner": "Captura entregada por el equipo de redes: captura.pcap.txt",
                "escenario": {
                    "host": "kali",
                    "ip": _MI_IP,
                    "archivos": {
                        "captura.pcap.txt": _CAPTURA,
                        "LEEME.txt": "Captura de la red Wi-Fi 'Cafeteria-Libre', 10:02 a 10:04.\nLa víctima usa la IP 192.168.56.40.\n",
                    },
                },
                "comandos": [
                    {
                        "comando": "tcpdump -r captura.pcap -A",
                        "patron": r"tcpdump\s+.*-r\s+captura\.pcap.*",
                        "salida": "tcpdump: la captura ya está exportada a texto en captura.pcap.txt; ábrela con cat o grep.",
                    }
                ],
            },
        },
    ],
    "flag": {
        "pista": "Las credenciales de un login viajan en una petición POST: busca 'POST' y mira las líneas siguientes.",
        "paso_a_paso": "grep -A3 POST captura.pcap.txt muestra username=admin&password=... ; el valor de password es la flag.",
    },
    "examen": [
        {"enunciado": "¿Por qué el atacante pudo leer la contraseña en esta captura?", "tipo": "opcion_multiple", "opciones": ["Porque el login usaba HTTP sin cifrar", "Porque la contraseña era débil", "Porque el servidor estaba caído", "Porque usaba UDP"], "respuesta": "Porque el login usaba HTTP sin cifrar"},
        {"enunciado": "En un paquete TLS capturado, ¿qué información sigue siendo visible?", "tipo": "opcion_multiple", "opciones": ["El usuario y la contraseña", "El contenido completo de la página", "El servidor de destino (IP y, a menudo, el nombre en el SNI)", "Nada en absoluto"], "respuesta": "El servidor de destino (IP y, a menudo, el nombre en el SNI)"},
        {"enunciado": "¿Con qué método HTTP suelen enviarse los formularios de login?", "tipo": "opcion_multiple", "opciones": ["GET", "POST", "HEAD", "OPTIONS"], "respuesta": "POST"},
        {"enunciado": "¿Qué medida protege mejor a los usuarios de este ataque?", "tipo": "opcion_multiple", "opciones": ["Cambiar el puerto 80 por el 8080", "Usar HTTPS en todo el sitio con HSTS", "Pedir contraseñas más largas", "Ocultar el formulario"], "respuesta": "Usar HTTPS en todo el sitio con HSTS"},
    ],
}

_ARPWATCH = """Nov  4 09:58:02 kali arpwatch: new station 192.168.56.1 11:22:33:44:55:66 eth0
Nov  4 09:58:40 kali arpwatch: new station 192.168.56.23 08:00:27:3c:1d:aa eth0
Nov  4 10:05:13 kali arpwatch: new station 192.168.56.50 aa:bb:cc:00:11:22 eth0
Nov  4 10:06:01 kali arpwatch: changed ethernet address 192.168.56.1 aa:bb:cc:00:11:22 (11:22:33:44:55:66) eth0
Nov  4 10:06:01 kali arpwatch: flip flop 192.168.56.1 aa:bb:cc:00:11:22 (11:22:33:44:55:66) eth0
Nov  4 10:06:02 kali arpwatch: alerta del SOC: posible MITM desde la impresora. Código de incidente FLAG{arp_spoof_mitm_detectado}
"""

ARP = {
    "nombre": "ARP Spoofing: Detectando un Man-in-the-Middle",
    "descripcion": (
        "Investiga una red local donde alguien suplantó la puerta de enlace: lee la tabla ARP, "
        "encuentra la MAC duplicada y confirma el ataque en el registro de arpwatch."
    ),
    "resumen_cierre": (
        "<p>Detectaste el patrón clásico de un ARP spoofing: dos IP con la misma MAC, y un "
        "<em>changed ethernet address</em> sobre la puerta de enlace en el registro.</p>"
        "<div class=\"importante\"><p>Defensas reales: <strong>Dynamic ARP Inspection</strong> en los "
        "switches, entradas ARP estáticas para la puerta de enlace en equipos críticos, segmentar con "
        "VLAN y, sobre todo, cifrar (HTTPS, SSH, VPN): aunque el atacante quede en medio, no lee nada.</p></div>"
    ),
    "secciones": [
        {
            "titulo": "ARP y su punto débil",
            "duracion": 12,
            "objetivos": [
                "Explicar para qué sirve ARP dentro de una red local.",
                "Describir cómo un atacante envenena la tabla ARP.",
                "Reconocer los síntomas de un ataque de intermediario (MITM).",
            ],
            "html": (
                "<div class=\"escenario\"><p>Varios equipos de la sala de cómputo reportan que la conexión "
                "«va lenta» y que el navegador mostró alertas de certificado. El SOC sospecha que alguien "
                "está interceptando el tráfico de la red local.</p></div>"
                "<h3>Cómo funciona ARP</h3>"
                "<p>Dentro de una red local, los equipos se hablan por <strong>dirección MAC</strong>, no por IP. "
                "ARP traduce una a la otra: un equipo pregunta a todos «¿quién tiene la 192.168.56.1?» y el "
                "dueño responde con su MAC. La respuesta se guarda en la <em>tabla ARP</em>.</p>"
                "<h3>El punto débil</h3>"
                "<p>ARP no autentica nada. Cualquiera puede responder «la 192.168.56.1 soy yo», incluso sin "
                "que nadie haya preguntado, y los equipos le creen.</p>"
                "<table><thead><tr><th>Paso</th><th>Qué hace el atacante</th></tr></thead><tbody>"
                "<tr><td>1</td><td>Le dice a la víctima que la puerta de enlace tiene <em>su</em> MAC.</td></tr>"
                "<tr><td>2</td><td>Le dice a la puerta de enlace que la víctima tiene <em>su</em> MAC.</td></tr>"
                "<tr><td>3</td><td>Reenvía el tráfico entre ambos y lo lee o modifica en el camino.</td></tr>"
                "</tbody></table>"
                "<div class=\"nota\"><p>El síntoma más fácil de ver: <strong>dos IP distintas con la misma "
                "MAC</strong> en la tabla ARP. La MAC repetida es la del atacante.</p></div>"
            ),
            "pasos": [],
            "entorno": None,
        },
        {
            "titulo": "Leyendo una tabla ARP envenenada",
            "duracion": 18,
            "objetivos": [
                "Consultar la tabla ARP de un equipo Linux.",
                "Encontrar la MAC suplantada.",
                "Confirmar el ataque en los registros de arpwatch.",
            ],
            "html": (
                "<h3>Tu misión</h3>"
                "<p>Desde un equipo de la sala, identifica qué dispositivo está suplantando a la puerta "
                "de enlace y recupera el código de incidente que dejó el SOC en el registro.</p>"
                "<table><thead><tr><th>Equipo</th><th>IP</th><th>MAC legítima</th></tr></thead><tbody>"
                "<tr><td>Puerta de enlace</td><td><code>192.168.56.1</code></td><td><code>11:22:33:44:55:66</code></td></tr>"
                "<tr><td>PC de la sala</td><td><code>192.168.56.23</code></td><td><code>08:00:27:3c:1d:aa</code></td></tr>"
                "<tr><td>Impresora</td><td><code>192.168.56.50</code></td><td>(sin registrar)</td></tr>"
                "</tbody></table>"
            ),
            "pasos": [
                ("Ubica la puerta de enlace", "<p>La ruta por defecto te dice cuál es.</p>", "ip route", "default via 192.168.56.1 dev eth0 proto dhcp metric 100\n192.168.56.0/24 dev eth0 proto kernel scope link src 192.168.56.23"),
                ("Consulta la tabla ARP", "<p>Compara las MAC que tiene guardadas el equipo con la tabla de arriba.</p>", "arp -a", "gateway.lab (192.168.56.1) at aa:bb:cc:00:11:22 [ether] on eth0\nimpresora.lab (192.168.56.50) at aa:bb:cc:00:11:22 [ether] on eth0\nintranet.lab (192.168.56.60) at 08:00:27:6e:60:60 [ether] on eth0"),
                ("Encuentra la MAC repetida", "<p>Filtra por la MAC sospechosa: si aparece dos veces, ya tienes al intermediario.</p>", "arp -a | grep aa:bb:cc:00:11:22", "gateway.lab (192.168.56.1) at aa:bb:cc:00:11:22 [ether] on eth0\nimpresora.lab (192.168.56.50) at aa:bb:cc:00:11:22 [ether] on eth0"),
                ("Revisa el registro de arpwatch", "<p>arpwatch avisa cuando una IP cambia de MAC. Mira las últimas entradas.</p>", "tail -n 4 /var/log/arpwatch.log", "... changed ethernet address 192.168.56.1 aa:bb:cc:00:11:22 (11:22:33:44:55:66) eth0\n..."),
                ("Recupera el código de incidente", "<p>El SOC dejó el código del incidente en el mismo registro.</p>", "grep FLAG /var/log/arpwatch.log", "... Código de incidente FLAG{...}"),
            ],
            "entorno": {
                "prompt": "estudiante@pc-sala:~$",
                "banner": "Equipo de la sala de cómputo 3. Tienes permisos de lectura sobre /var/log.",
                "escenario": {
                    "host": "pc-sala",
                    "ip": "192.168.56.23",
                    "archivos": {
                        "/var/log/arpwatch.log": _ARPWATCH,
                        "reporte_soc.txt": "Ticket SOC-2291: usuarios reportan alertas de certificado en la sala 3.\nRevisar tabla ARP y arpwatch.\n",
                    },
                    "red": [
                        {"ip": "192.168.56.1", "nombre": "gateway.lab", "mac": "aa:bb:cc:00:11:22", "servicios": [{"puerto": 53, "servicio": "domain"}]},
                        {"ip": "192.168.56.50", "nombre": "impresora.lab", "mac": "aa:bb:cc:00:11:22", "servicios": [{"puerto": 9100, "servicio": "jetdirect"}]},
                        {"ip": "192.168.56.60", "nombre": "intranet.lab", "mac": "08:00:27:6e:60:60", "servicios": [{"puerto": 80, "servicio": "http"}]},
                    ],
                },
                "comandos": [],
            },
        },
    ],
    "flag": {
        "pista": "Si dos IP distintas tienen la misma MAC, una de las dos respuestas ARP es falsa. El código del incidente está en /var/log/arpwatch.log.",
        "paso_a_paso": "1) arp -a muestra 192.168.56.1 y 192.168.56.50 con la MAC aa:bb:cc:00:11:22.\n2) grep FLAG /var/log/arpwatch.log devuelve el código de incidente.",
    },
    "examen": [
        {"enunciado": "¿Qué traduce el protocolo ARP?", "tipo": "opcion_multiple", "opciones": ["Nombres de dominio a IP", "Direcciones IP a direcciones MAC", "Puertos a servicios", "IP públicas a privadas"], "respuesta": "Direcciones IP a direcciones MAC"},
        {"enunciado": "¿Qué síntoma en la tabla ARP delata un ARP spoofing?", "tipo": "opcion_multiple", "opciones": ["Una IP sin MAC", "Dos IP distintas con la misma MAC", "Muchas entradas incompletas", "Una MAC con letras mayúsculas"], "respuesta": "Dos IP distintas con la misma MAC"},
        {"enunciado": "¿Qué función de los switches gestionables bloquea respuestas ARP falsas?", "tipo": "opcion_multiple", "opciones": ["Port mirroring", "Dynamic ARP Inspection", "Spanning Tree", "QoS"], "respuesta": "Dynamic ARP Inspection"},
        {"enunciado": "Si el atacante logra quedar en medio, ¿qué impide que lea las contraseñas?", "tipo": "opcion_multiple", "opciones": ["Que la red sea cableada", "Que el tráfico vaya cifrado (HTTPS, SSH, VPN)", "Que el equipo tenga antivirus", "Que la IP sea fija"], "respuesta": "Que el tráfico vaya cifrado (HTTPS, SSH, VPN)"},
    ],
}

LABS = [TCP_IP, NMAP, SNIFFING, ARP]
